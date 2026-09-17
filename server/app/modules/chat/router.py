"""Chat API endpoints with pre-provider rate limiting."""

import time
import uuid
from collections import defaultdict
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_optional_current_user
from app.modules.chat import service
from app.modules.chat.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])

# In-memory sliding window rate limiter
# Key -> list of request timestamps
_USER_RATE_LIMITS: dict[str, list[float]] = defaultdict(list)
_IP_RATE_LIMITS: dict[str, list[float]] = defaultdict(list)

USER_LIMIT_PER_MINUTE = 30
IP_LIMIT_PER_MINUTE = 60
WINDOW_SECONDS = 60.0
MAX_STORAGE_ENTRIES = 10_000


def cleanup_rate_limits(storage: dict[str, list[float]], now: float | None = None) -> int:
    """Utility to prune expired entries from rate limiter storage. Returns number of keys removed."""
    current_time = now if now is not None else time.time()
    expired_keys = [
        k for k, timestamps in list(storage.items())
        if not [t for t in timestamps if current_time - t < WINDOW_SECONDS]
    ]
    for k in expired_keys:
        storage.pop(k, None)
    return len(expired_keys)


def _sweep_if_exceeded_ceiling(storage: dict[str, list[float]], now: float) -> None:
    """Bounded memory sweep: only triggers if storage exceeds the safety ceiling."""
    if len(storage) > MAX_STORAGE_ENTRIES:
        cleanup_rate_limits(storage, now)
        # If still over ceiling (e.g. intense active DDoS from >10k IPs), evict oldest
        if len(storage) > MAX_STORAGE_ENTRIES:
            excess = len(storage) - MAX_STORAGE_ENTRIES
            oldest_keys = sorted(
                storage.keys(),
                key=lambda k: storage[k][-1] if storage[k] else 0,
            )[:excess]
            for k in oldest_keys:
                storage.pop(k, None)


def _check_rate_limit(key: str, storage: dict[str, list[float]], max_requests: int, error_detail: str):
    now = time.time()
    # 1. Prune expired timestamps for current key
    current_timestamps = storage.get(key, [])
    valid_timestamps = [t for t in current_timestamps if now - t < WINDOW_SECONDS]

    # 2. Check limit violation
    if len(valid_timestamps) >= max_requests:
        storage[key] = valid_timestamps
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_detail,
        )

    # 3. Add current request
    valid_timestamps.append(now)
    storage[key] = valid_timestamps

    # 4. Check bounded memory ceiling
    _sweep_if_exceeded_ceiling(storage, now)


@router.post("", response_model=ChatResponse)
async def chat_with_bot(
    request: ChatRequest,
    req: Request,
    current_user: dict | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message to the AI campus assistant with pre-provider rate limiting."""
    # Client IP is resolved by ProxyHeadersMiddleware using TRUSTED_PROXY_IPS.
    # When behind a trusted proxy (Nginx/LB), req.client.host reflects the real
    # client IP from X-Forwarded-For; untrusted sources cannot spoof this value.
    client_ip = req.client.host if req.client else "unknown"

    # 1. IP rate limit check (Abuse protection for all)
    _check_rate_limit(
        key=client_ip,
        storage=_IP_RATE_LIMITS,
        max_requests=IP_LIMIT_PER_MINUTE,
        error_detail="Quá nhiều yêu cầu từ địa chỉ IP của bạn. Vui lòng thử lại sau 1 phút.",
    )

    # 2. User rate limit check (for authenticated users)
    user_id = None
    if current_user and "sub" in current_user:
        try:
            user_id = uuid.UUID(current_user["sub"])
            _check_rate_limit(
                key=str(user_id),
                storage=_USER_RATE_LIMITS,
                max_requests=USER_LIMIT_PER_MINUTE,
                error_detail="Bạn đã gửi quá nhiều tin nhắn. Vui lòng chờ 1 phút trước khi tiếp tục.",
            )
        except ValueError:
            user_id = None

    return await service.handle_chat(
        db=db,
        user_id=user_id,
        request=request,
        user_lat=request.user_lat,
        user_lng=request.user_lng,
    )

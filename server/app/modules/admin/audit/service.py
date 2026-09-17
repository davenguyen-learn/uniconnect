"""Service for recording and querying Admin Audit Trail."""

import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.admin.audit.schemas import AdminAuditLogItem, AdminAuditLogList
from app.modules.admin.models import AdminAuditAction, AdminAuditLog, AdminAuditTargetType


async def record_audit_log(
    db: AsyncSession,
    actor_id: uuid.UUID | None,
    action: AdminAuditAction | str,
    target_type: AdminAuditTargetType | str,
    target_id: uuid.UUID,
    metadata_json: dict | None = None,
) -> AdminAuditLog:
    """Record an atomic administrative audit log with sanitized metadata."""
    act_str = action.value if hasattr(action, "value") else str(action)
    tgt_str = target_type.value if hasattr(target_type, "value") else str(target_type)

    # Sanitize metadata (shallow copy, strip any passwords/tokens if accidentally passed)
    clean_meta = None
    if metadata_json:
        clean_meta = {
            k: v
            for k, v in metadata_json.items()
            if not any(s in k.lower() for s in ("password", "token", "secret", "hash"))
        }

    log_entry = AdminAuditLog(
        actor_id=actor_id,
        action=act_str,
        target_type=tgt_str,
        target_id=target_id,
        metadata_json=clean_meta,
    )
    db.add(log_entry)
    await db.flush()
    return log_entry


async def list_audit_logs(
    db: AsyncSession,
    action: str | None = None,
    target_type: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> AdminAuditLogList:
    """List paginated audit trail logs with actor info."""
    base = select(AdminAuditLog).options(joinedload(AdminAuditLog.actor))
    count_base = select(func.count()).select_from(AdminAuditLog)

    if action:
        base = base.where(AdminAuditLog.action == action)
        count_base = count_base.where(AdminAuditLog.action == action)

    if target_type:
        base = base.where(AdminAuditLog.target_type == target_type)
        count_base = count_base.where(AdminAuditLog.target_type == target_type)

    total = (await db.execute(count_base)).scalar() or 0
    stmt = base.order_by(AdminAuditLog.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    logs = result.unique().scalars().all()

    items = [
        AdminAuditLogItem(
            id=log.id,
            actor_id=log.actor_id,
            action=log.action,
            target_type=log.target_type,
            target_id=log.target_id,
            metadata_json=log.metadata_json,
            created_at=log.created_at,
            actor_username=log.actor.username if log.actor else None,
        )
        for log in logs
    ]

    return AdminAuditLogList(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )

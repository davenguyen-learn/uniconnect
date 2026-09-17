import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.core.config import settings
from app.core.database import check_db_connectivity, engine
from app.core.exception_handlers import register_exception_handlers

logger = logging.getLogger("uniconnect.access")


# Defense-in-depth security headers applied at the application level.
# Nginx also sets these for public HTTP boundary; both layers must agree.
_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Middleware to measure request duration, inject timing + security headers, and log access."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        try:
            response: Response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000
            response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"
            for header_name, header_value in _SECURITY_HEADERS.items():
                response.headers.setdefault(header_name, header_value)
            if not request.url.path.startswith("/health"):
                logger.info(
                    "%s %s - status=%s duration=%.2fms",
                    request.method,
                    request.url.path,
                    response.status_code,
                    duration_ms,
                )
            return response
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "%s %s - ERROR duration=%.2fms error=%s",
                request.method,
                request.url.path,
                duration_ms,
                exc.__class__.__name__,
            )
            raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown lifecycle events."""
    # Ensure all SQLAlchemy models are loaded into registry on startup
    import app.modules.users.models  # noqa: F401
    import app.modules.activities.models  # noqa: F401
    import app.modules.groups.models  # noqa: F401
    import app.modules.forms.models  # noqa: F401
    import app.modules.participation.models  # noqa: F401
    import app.modules.interactions.models  # noqa: F401
    import app.modules.trophies.models  # noqa: F401
    import app.modules.notifications.models  # noqa: F401
    import app.modules.reports.models  # noqa: F401
    import app.modules.calendar.models  # noqa: F401

    yield
    # Shutdown: dispose the engine to close all connections
    await engine.dispose()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    application = FastAPI(
        title="UniConnect",
        description="Location-aware activity discovery platform for university communities",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── Middleware (execution order: outermost first → innermost last) ──
    # 1. Timing + security headers (innermost — runs closest to route handler)
    application.add_middleware(RequestTimingMiddleware)
    # 2. CORS (must wrap timing so preflight responses get correct headers)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Process-Time"],
    )
    # 3. Proxy headers (outermost — translates X-Forwarded-* before anything else)
    # trusted_hosts controls which source IPs are allowed to set forwarded headers.
    # Default "127.0.0.1"; set TRUSTED_PROXY_IPS in production to actual proxy IPs.
    application.add_middleware(
        ProxyHeadersMiddleware,
        trusted_hosts=settings.trusted_proxy_list,
    )

    # ── Exception Handlers ──
    register_exception_handlers(application)

    # ── Routes ──
    @application.get("/health", tags=["system"])
    @application.get("/api/health", tags=["system"])
    @application.get("/api/v1/health", tags=["system"])
    async def health_check():
        start = time.perf_counter()
        try:
            # Test DB connectivity with a strict 3.0s timeout
            await check_db_connectivity(timeout=3.0)
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            return {
                "status": "ok",
                "db": "healthy",
                "latency_ms": latency_ms,
                "version": application.version,
            }
        except Exception as exc:
            # Log error without leaking credentials, connection string or host
            logger.warning("Database health check failed: %s", exc.__class__.__name__)
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "degraded",
                    "db": "unhealthy",
                    "version": application.version,
                },
            )

    # Module routers
    from app.modules.auth.router import router as auth_router
    from app.modules.users.router import router as users_router
    from app.modules.activities.router import router as activities_router
    from app.modules.participation.router import router as participation_router
    from app.modules.groups.router import router as groups_router
    from app.modules.interactions.router import router as interactions_router
    from app.modules.chat.router import router as chat_router
    from app.modules.notifications.router import router as notifications_router
    from app.modules.reports.router import router as reports_router
    from app.modules.admin.router import router as admin_router
    from app.modules.trophies.router import router as trophies_router
    from app.modules.calendar.router import router as calendar_router

    application.include_router(auth_router, prefix="/api/v1")
    application.include_router(users_router, prefix="/api/v1")
    application.include_router(activities_router, prefix="/api/v1")
    application.include_router(participation_router, prefix="/api/v1")
    application.include_router(groups_router, prefix="/api/v1")
    application.include_router(interactions_router, prefix="/api/v1")
    application.include_router(chat_router, prefix="/api/v1")
    application.include_router(notifications_router, prefix="/api/v1")
    application.include_router(reports_router, prefix="/api/v1")
    application.include_router(admin_router, prefix="/api/v1")
    application.include_router(trophies_router, prefix="/api/v1")
    application.include_router(calendar_router, prefix="/api/v1")


    return application


app = create_app()

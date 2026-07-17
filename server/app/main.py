"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown lifecycle events."""
    # Startup: connection pool is lazily created by SQLAlchemy on first use
    yield
    # Shutdown: dispose the engine to close all connections
    from app.core.database import engine

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

    # ── Middleware ──
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception Handlers ──
    register_exception_handlers(application)

    # ── Routes ──
    @application.get("/health", tags=["system"])
    async def health_check():
        return {"status": "ok"}

    # Module routers
    from app.modules.auth.router import router as auth_router
    from app.modules.users.router import router as users_router
    from app.modules.activities.router import router as activities_router
    from app.modules.participation.router import router as participation_router
    from app.modules.groups.router import router as groups_router
    from app.modules.interactions.router import router as interactions_router
    from app.modules.documents.router import router as documents_router
    from app.modules.chat.router import router as chat_router
    from app.modules.notifications.router import router as notifications_router
    from app.modules.reports.router import router as reports_router
    from app.modules.admin.router import router as admin_router
    from app.modules.trophies.router import router as trophies_router

    application.include_router(auth_router, prefix="/api/v1")
    application.include_router(users_router, prefix="/api/v1")
    application.include_router(activities_router, prefix="/api/v1")
    application.include_router(participation_router, prefix="/api/v1")
    application.include_router(groups_router, prefix="/api/v1")
    application.include_router(interactions_router, prefix="/api/v1")
    application.include_router(documents_router, prefix="/api/v1")
    application.include_router(chat_router, prefix="/api/v1")
    application.include_router(notifications_router, prefix="/api/v1")
    application.include_router(reports_router, prefix="/api/v1")
    application.include_router(admin_router, prefix="/api/v1")
    application.include_router(trophies_router, prefix="/api/v1")


    return application


app = create_app()

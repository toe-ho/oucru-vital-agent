from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.assessment_router import router as assessment_router
from app.api.auth_router import router as auth_router
from app.api.chat_router import router as chat_router
from app.api.health_router import router as health_router
from app.api.recordings_router import router as recordings_router
from app.api.reports_router import router as reports_router
from app.api.segment_overrides_router import router as segment_overrides_router
from app.api.settings_router import router as settings_router
from app.core.errors import register_error_handlers
from app.core.settings import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_title,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    register_error_handlers(app)

    app.include_router(health_router)
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    app.include_router(settings_router, prefix="/api/settings", tags=["settings"])
    app.include_router(recordings_router, prefix="/api/recordings", tags=["recordings"])
    app.include_router(assessment_router, prefix="/api/assess", tags=["assessment"])
    app.include_router(reports_router, prefix="/api/reports", tags=["reports"])
    app.include_router(segment_overrides_router, prefix="/api/segments", tags=["segment-overrides"])
    app.include_router(chat_router, prefix="/api/chat", tags=["chat"])

    return app


app = create_app()

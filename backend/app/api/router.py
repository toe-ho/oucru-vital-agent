from fastapi import APIRouter

from app.api import assessments, chat, dashboard, health, recordings, reports, segments, settings_router, uploads

router = APIRouter()

router.include_router(health.router)
router.include_router(uploads.router)
router.include_router(recordings.router)
router.include_router(assessments.router)
router.include_router(segments.router)
router.include_router(reports.router)
router.include_router(dashboard.router)
router.include_router(chat.router)
router.include_router(settings_router.router)

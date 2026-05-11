from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import router
from app.config import settings
from app.exceptions import AppException, app_exception_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.session import engine
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))

    from app.db.session import AsyncSessionLocal
    from app.db.init_db import seed_roles, seed_settings
    async with AsyncSessionLocal() as db:
        await seed_roles(db)
        await seed_settings(db)

    yield

    await engine.dispose()


app = FastAPI(
    title="OUCRU Vital Agent",
    description="Agentic AI for high-frequency waveform data quality monitoring",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


app.add_exception_handler(AppException, app_exception_handler)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=500,
        content={"error": "InternalServerError", "detail": "An unexpected error occurred.", "request_id": request_id},
    )


app.include_router(router, prefix="/api")

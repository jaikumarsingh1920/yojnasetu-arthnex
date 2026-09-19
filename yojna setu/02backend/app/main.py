from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import RequestIDMiddleware
from app.core.rate_limit import RateLimitMiddleware
from app.core.errors import (
    http_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    unhandled_exception_handler,
)
from app.api.v1.router import api_router
from app.services.ingestion.scheduler import auto_scheduler

# Initialize structured logging
setup_logging()

is_prod = settings.is_production()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cleanly manages application background task lifecycle."""
    if settings.SCHEME_INGESTION_ENABLED:
        auto_scheduler.start()
    yield
    if auto_scheduler.is_running:
        auto_scheduler.stop()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="YojnaSetu AI-assisted Multilingual Platform API - Production Hardened",
    version="1.0.0",
    openapi_url="/openapi.json" if not is_prod else None,
    docs_url="/docs" if not is_prod else None,
    redoc_url="/redoc" if not is_prod else None,
    redirect_slashes=False,
    lifespan=lifespan,
)

# Exception Handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Custom Middlewares (Request ID & Rate Limiting)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestIDMiddleware)

# CORS middleware: Strict origin whitelisting in production; dev regex permitted in non-production
cors_regex = None if is_prod else r"https://.*\.vercel\.app|https://.*\.ngrok-free\.app|https://.*\.ngrok\.io|http://localhost:\d+|http://127\.0\.0\.1:\d+"

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_origin_regex=cors_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
def root_health_check():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENV
    }

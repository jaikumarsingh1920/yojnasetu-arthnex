from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.api.deps import get_db
from app.core.config import settings

router = APIRouter()


@router.get("", summary="Liveness probe")
def liveness_check():
    """
    Returns basic service liveness status.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENV,
        "version": "1.0.0"
    }


@router.get("/ready", summary="Readiness probe")
def readiness_check(db: Session = Depends(get_db)):
    """
    Deep readiness check verifying database connectivity.
    """
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "service": settings.PROJECT_NAME,
            "database": "connected",
            "environment": settings.ENV
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database readiness probe failed: {str(e)}"
        )

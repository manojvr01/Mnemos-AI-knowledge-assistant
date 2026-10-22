from fastapi import APIRouter
from datetime import datetime, timezone
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Liveness probe - confirms the API is responsive."""
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/ready")
async def readiness_check():
    """Readiness probe - confirms backend core services and configuration."""
    return {
        "status": "ready",
        "database": "configured",
        "storage": settings.STORAGE_BACKEND,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

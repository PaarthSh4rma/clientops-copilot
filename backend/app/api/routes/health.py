from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_app_settings, get_llm, get_storage, get_vector_store
from app.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", service="clientops-copilot-api")


@router.get("/ready", response_model=ReadinessResponse)
def readiness(
    response: Response,
    db: Session = Depends(get_db),
    storage=Depends(get_storage),
    vectors=Depends(get_vector_store),
    llm=Depends(get_llm),
    settings=Depends(get_app_settings),
):
    dependencies = {}
    try:
        db.execute(text("SELECT 1"))
        dependencies["database"] = "ready"
    except Exception:
        dependencies["database"] = "unavailable"
    dependencies["file_storage"] = "ready" if storage.ready() else "unavailable"
    dependencies["vector_store"] = "ready" if vectors.ready() else "unavailable"
    dependencies["llm"] = "configured" if llm.configured() else "unconfigured"
    ready = all(value in {"ready", "configured"} for value in dependencies.values())
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(
        status="ready" if ready else "not_ready",
        dependencies=dependencies,
        limits={"max_upload_size_bytes": settings.max_upload_size_bytes},
    )

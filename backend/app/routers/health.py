from fastapi import APIRouter
from datetime import datetime
from app.services.pipeline.state import pipeline_state

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "last_pipeline_run": pipeline_state.last_run,
        "pipeline_running": pipeline_state.is_running,
        "articles_processed": pipeline_state.articles_processed,
        "timestamp": datetime.utcnow(),
    }

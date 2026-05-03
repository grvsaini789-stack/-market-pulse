from fastapi import APIRouter, BackgroundTasks
from app.services.pipeline.runner import run_pipeline
from app.services.pipeline.state import pipeline_state

router = APIRouter(prefix="/api", tags=["pipeline"])


@router.post("/pipeline/run")
async def trigger_pipeline(background_tasks: BackgroundTasks):
    """Manually trigger the news pipeline (useful during development)."""
    if pipeline_state.is_running:
        return {"status": "already_running", "last_run": pipeline_state.last_run}
    background_tasks.add_task(run_pipeline)
    return {"status": "started"}

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.db.database import init_db
from app.routers import health, stories, pipeline as pipeline_router
from app.services.pipeline.runner import run_pipeline


scheduler = AsyncIOScheduler()

# Only schedule auto-run if interval is set to a reasonable value (max 1 week)
AUTO_RUN = 0 < settings.pipeline_interval_minutes <= 10080


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    if AUTO_RUN:
        scheduler.add_job(
            run_pipeline,
            "interval",
            minutes=settings.pipeline_interval_minutes,
            id="news_pipeline",
            replace_existing=True,
        )
        scheduler.start()
    yield
    if AUTO_RUN:
        scheduler.shutdown(wait=False)


app = FastAPI(title="Market Pulse", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(stories.router)
app.include_router(pipeline_router.router)

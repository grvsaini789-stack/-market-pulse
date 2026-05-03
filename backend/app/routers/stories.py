from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from datetime import datetime, timedelta

from app.db.database import get_db
from app.db.models import Article, StoryCluster
from app.models.story import StoriesResponse, StoryDetailResponse, StoryOut, StoryDetailOut
from app.models.article import ArticleOut
from app.services.pipeline.state import pipeline_state
from app.config import settings

router = APIRouter(prefix="/api", tags=["stories"])


@router.get("/stories", response_model=StoriesResponse)
async def list_stories(
    theme: str | None = Query(None, description="Filter by theme"),
    limit: int = Query(30, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    cutoff = datetime.utcnow() - timedelta(days=settings.news_lookback_days)
    q = select(StoryCluster).where(StoryCluster.last_updated_at >= cutoff)
    if theme:
        q = q.where(StoryCluster.theme == theme)

    # Sort: importance DESC, then last_updated_at DESC
    q = q.order_by(desc(StoryCluster.importance), desc(StoryCluster.last_updated_at))

    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar() or 0

    q = q.limit(limit).offset(offset)
    result = await db.execute(q)
    clusters = result.scalars().all()

    stories = [StoryOut.model_validate(c) for c in clusters]
    return StoriesResponse(
        stories=stories,
        total=total,
        last_pipeline_run=pipeline_state.last_run,
    )


@router.get("/stories/{story_id}", response_model=StoryDetailResponse)
async def get_story(story_id: str, db: AsyncSession = Depends(get_db)):
    cluster = await db.get(StoryCluster, story_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Story not found")

    articles_result = await db.execute(
        select(Article)
        .where(Article.cluster_id == story_id)
        .order_by(desc(Article.published_at))
    )
    articles = articles_result.scalars().all()
    article_outs = [ArticleOut.model_validate(a) for a in articles]

    detail = StoryDetailOut(
        **StoryOut.model_validate(cluster).model_dump(),
        articles=article_outs,
    )
    return StoryDetailResponse(story=detail)

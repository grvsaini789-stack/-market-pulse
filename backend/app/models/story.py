from pydantic import BaseModel
from datetime import datetime
from app.models.article import ArticleOut


class StoryOut(BaseModel):
    id: str
    title: str
    summary: str
    theme: str
    importance: int
    tickers: list[str]
    article_count: int
    first_seen_at: datetime
    last_updated_at: datetime

    class Config:
        from_attributes = True


class StoryDetailOut(StoryOut):
    articles: list[ArticleOut]


class StoriesResponse(BaseModel):
    stories: list[StoryOut]
    total: int
    last_pipeline_run: datetime | None


class StoryDetailResponse(BaseModel):
    story: StoryDetailOut

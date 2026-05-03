from pydantic import BaseModel
from datetime import datetime


class ArticleOut(BaseModel):
    id: str
    url: str
    title: str
    summary: str
    source: str
    published_at: datetime
    tickers: list[str]
    theme: str
    relevance_score: float
    key_entities: list[str]

    class Config:
        from_attributes = True

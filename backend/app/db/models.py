import uuid
from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    url: Mapped[str] = mapped_column(String, unique=True, index=True)
    title: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String)  # finnhub / alpha_vantage / rss / twitter
    published_at: Mapped[datetime] = mapped_column(DateTime)
    tickers: Mapped[list] = mapped_column(JSON, default=list)
    theme: Mapped[str] = mapped_column(String, default="")
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    key_entities: Mapped[list] = mapped_column(JSON, default=list)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    cluster_id: Mapped[str | None] = mapped_column(String, ForeignKey("story_clusters.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cluster: Mapped["StoryCluster | None"] = relationship("StoryCluster", back_populates="articles")


class StoryCluster(Base):
    __tablename__ = "story_clusters"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String, default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    theme: Mapped[str] = mapped_column(String, default="")
    importance: Mapped[int] = mapped_column(Integer, default=1)
    tickers: Mapped[list] = mapped_column(JSON, default=list)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    article_count: Mapped[int] = mapped_column(Integer, default=0)
    needs_rebuild: Mapped[bool] = mapped_column(default=True)  # flag for story builder to reprocess

    articles: Mapped[list["Article"]] = relationship("Article", back_populates="cluster")

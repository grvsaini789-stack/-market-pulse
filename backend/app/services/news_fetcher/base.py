from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawArticle:
    url: str
    title: str
    summary: str
    source: str
    published_at: datetime
    tickers: list[str] = field(default_factory=list)


class BaseFetcher(ABC):
    @abstractmethod
    async def fetch(self) -> list[RawArticle]:
        """Return list of raw articles fetched from the source."""
        ...

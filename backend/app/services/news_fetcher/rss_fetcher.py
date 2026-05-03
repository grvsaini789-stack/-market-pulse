import re
import feedparser
import httpx
from datetime import datetime
from email.utils import parsedate_to_datetime
from app.services.news_fetcher.base import BaseFetcher, RawArticle

# Only tier-1 business/financial news sources
RSS_FEEDS = [
    # Global wires
    ("Reuters Business", "https://feeds.reuters.com/reuters/businessNews"),
    ("Reuters Markets", "https://feeds.reuters.com/reuters/marketsNews"),
    ("AP Business", "https://feeds.apnews.com/rss/business"),
    # Financial press
    ("Financial Times", "https://www.ft.com/rss/home/uk"),
    ("Bloomberg Markets", "https://feeds.bloomberg.com/markets/news.rss"),
    ("WSJ Markets", "https://feeds.content.dowjones.io/public/rss/mw_marketpulse"),
    ("MarketWatch", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
    # Business broadcast
    ("CNBC Top News", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
    ("CNBC World Economy", "https://www.cnbc.com/id/20910258/device/rss/rss.html"),
    ("BBC Business", "https://feeds.bbci.co.uk/news/business/rss.xml"),
    # India (credible financial press)
    ("Economic Times Markets", "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"),
    ("Economic Times Economy", "https://economictimes.indiatimes.com/economy/rssfeeds/1373380680.cms"),
    ("Mint Markets", "https://www.livemint.com/rss/markets"),
    ("Mint Economy", "https://www.livemint.com/rss/economy"),
    ("Business Standard Markets", "https://www.business-standard.com/rss/markets-106.rss"),
    ("Moneycontrol News", "https://www.moneycontrol.com/rss/latestnews.xml"),
]

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return _TAG_RE.sub("", text).strip()


def _parse_date(entry) -> datetime:
    for attr in ("published", "updated"):
        raw = getattr(entry, attr, None)
        if raw:
            try:
                return parsedate_to_datetime(raw).replace(tzinfo=None)
            except Exception:
                pass
    return datetime.utcnow()


class RssFetcher(BaseFetcher):
    async def fetch(self) -> list[RawArticle]:
        articles = []
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            for source_name, feed_url in RSS_FEEDS:
                try:
                    resp = await client.get(feed_url)
                    feed = feedparser.parse(resp.text)
                    for entry in feed.entries[:25]:
                        url = entry.get("link", "")
                        title = entry.get("title", "")
                        if not url or not title:
                            continue
                        summary = entry.get("summary", "") or entry.get("description", "")
                        articles.append(RawArticle(
                            url=url,
                            title=_strip_html(title),
                            summary=_strip_html(summary)[:500],
                            source=f"rss:{source_name}",
                            published_at=_parse_date(entry),
                            tickers=[],
                        ))
                except Exception as e:
                    print(f"[RssFetcher] {source_name} error: {e}")
        return articles

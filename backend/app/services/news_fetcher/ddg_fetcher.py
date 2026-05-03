import time
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from duckduckgo_search import DDGS
from app.services.news_fetcher.base import BaseFetcher, RawArticle

MARKET_QUERIES = [
    ("geo_war_conflict",    "war conflict sanctions geopolitical crisis market impact"),
    ("geo_trade_tariff",    "trade war tariffs sanctions trade deal economy"),
    ("macro_fed",           "Federal Reserve interest rate decision inflation policy"),
    ("macro_rbi",           "RBI Reserve Bank India interest rate monetary policy"),
    ("macro_ecb",           "ECB European Central Bank rate decision euro"),
    ("macro_inflation",     "inflation CPI PPI data economy impact"),
    ("commodity_oil",       "crude oil price Brent WTI market today"),
    ("commodity_gold",      "gold silver commodity price market"),
    ("earnings_results",    "quarterly earnings results beat miss guidance stock"),
    ("corporate_ma",        "merger acquisition buyout deal billion stock"),
    ("india_market",        "Nifty Sensex NSE BSE India stock market today"),
    ("market_forex",        "dollar rupee yuan currency exchange rate"),
]

TRUSTED_DOMAINS = {
    "reuters.com", "bloomberg.com", "ft.com", "wsj.com", "cnbc.com",
    "apnews.com", "bbc.com", "bbc.co.uk", "economist.com", "marketwatch.com",
    "economictimes.indiatimes.com", "livemint.com", "business-standard.com",
    "moneycontrol.com", "ndtvprofit.com", "financialexpress.com",
    "theguardian.com", "nytimes.com", "washingtonpost.com",
    "businessinsider.com", "fortune.com", "forbes.com",
    "investing.com", "seekingalpha.com", "barrons.com",
}


def _domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.lstrip("www.")
    except Exception:
        return ""


def _is_trusted(url: str) -> bool:
    d = _domain(url)
    return any(d == trusted or d.endswith("." + trusted) for trusted in TRUSTED_DOMAINS)


def _fetch_all_sequential() -> list[RawArticle]:
    """Runs all queries sequentially with a delay to avoid DDG rate limiting."""
    all_articles: list[RawArticle] = []
    for label, query in MARKET_QUERIES:
        try:
            with DDGS() as ddgs:
                results = ddgs.news(
                    keywords=query,
                    region="wt-wt",
                    safesearch="moderate",
                    timelimit="d",
                    max_results=10,
                )
                for item in results:
                    url = item.get("url", "")
                    title = item.get("title", "")
                    if not url or not title or not _is_trusted(url):
                        continue
                    raw_date = item.get("date", "")
                    try:
                        published_at = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).replace(tzinfo=None)
                    except Exception:
                        published_at = datetime.utcnow()
                    all_articles.append(RawArticle(
                        url=url,
                        title=title,
                        summary=item.get("body", "")[:500],
                        source=f"ddg:{_domain(url)}",
                        published_at=published_at,
                        tickers=[],
                    ))
        except Exception as e:
            print(f"[DDGFetcher] query '{label}' error: {e}")
        time.sleep(2)  # 2-second pause between queries to avoid rate limiting

    print(f"[DDGFetcher] fetched {len(all_articles)} articles from {len(MARKET_QUERIES)} queries")
    return all_articles


class DuckDuckGoFetcher(BaseFetcher):
    async def fetch(self) -> list[RawArticle]:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            articles = await loop.run_in_executor(executor, _fetch_all_sequential)
        return articles

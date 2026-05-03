from app.services.news_fetcher.base import BaseFetcher, RawArticle
from app.services.news_fetcher.ddg_fetcher import DuckDuckGoFetcher
from app.services.news_fetcher.rss_fetcher import RssFetcher
from app.services.news_fetcher.twitter_fetcher import TwitterFetcher
from app.config import settings


def get_fetchers() -> list[BaseFetcher]:
    fetchers: list[BaseFetcher] = [
        DuckDuckGoFetcher(),  # free web search — no API key needed
        RssFetcher(),         # free RSS from credible outlets
    ]
    token = settings.twitter_bearer_token
    if token and not token.startswith("optional") and not token.startswith("your_"):
        fetchers.append(TwitterFetcher())  # optional, paid X API
    return fetchers


async def fetch_all() -> list[RawArticle]:
    articles: list[RawArticle] = []
    for fetcher in get_fetchers():
        results = await fetcher.fetch()
        articles.extend(results)
    return articles

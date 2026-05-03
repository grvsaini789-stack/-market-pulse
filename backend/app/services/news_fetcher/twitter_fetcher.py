import tweepy
from datetime import datetime
from app.services.news_fetcher.base import BaseFetcher, RawArticle
from app.config import settings

# Curated whitelist: official verified accounts of major financial news outlets only.
# These are institutional accounts, not individual users.
CREDIBLE_ACCOUNTS = [
    # Global wires & financial press
    "Reuters",
    "AP",
    "BloombergMarkets",
    "BloombergBusiness",
    "WSJ",
    "FinancialTimes",
    "FT",
    "MarketWatch",
    "CNBC",
    "CNBCWorld",
    "BBCBusiness",
    "BBCWorld",
    "TheEconomist",
    # Central banks & regulators (official accounts)
    "federalreserve",
    "ecb",
    "RBI",
    "SEBI_India",
    "IMFNews",
    "WorldBank",
    # India financial press
    "EconomicTimes",
    "livemint",
    "bsindia",
    "moneycontrolcom",
    "NDTVProfit",
]

# We fetch recent tweets from these accounts and filter for financial content
FINANCIAL_KEYWORDS = {
    "market", "rate", "inflation", "gdp", "stock", "equity", "bond", "fed",
    "rbi", "ecb", "earnings", "trade", "tariff", "sanctions", "oil", "gold",
    "recession", "growth", "deficit", "surplus", "ipo", "merger", "acquisition",
    "central bank", "interest", "currency", "rupee", "dollar", "yuan", "economy",
}


def _is_financial(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in FINANCIAL_KEYWORDS)


class TwitterFetcher(BaseFetcher):
    def __init__(self):
        if settings.twitter_bearer_token:
            self._client = tweepy.Client(bearer_token=settings.twitter_bearer_token)
        else:
            self._client = None

    async def fetch(self) -> list[RawArticle]:
        if not self._client:
            return []

        articles = []
        for username in CREDIBLE_ACCOUNTS:
            try:
                # Resolve username to user ID
                user_resp = self._client.get_user(username=username)
                if not user_resp.data:
                    continue
                user_id = user_resp.data.id

                # Fetch recent tweets (no retweets, no replies)
                tweets_resp = self._client.get_users_tweets(
                    user_id,
                    max_results=10,
                    exclude=["retweets", "replies"],
                    tweet_fields=["created_at", "entities"],
                )
                if not tweets_resp.data:
                    continue

                for tweet in tweets_resp.data:
                    if not _is_financial(tweet.text):
                        continue

                    # Use the first URL in the tweet as canonical link (usually points to article)
                    entities = tweet.entities or {}
                    urls_in_tweet = [u["expanded_url"] for u in entities.get("urls", []) if "expanded_url" in u]
                    canonical_url = urls_in_tweet[0] if urls_in_tweet else f"https://twitter.com/{username}/status/{tweet.id}"

                    articles.append(RawArticle(
                        url=canonical_url,
                        title=tweet.text[:200],
                        summary=tweet.text,
                        source=f"twitter:@{username}",
                        published_at=tweet.created_at.replace(tzinfo=None) if tweet.created_at else datetime.utcnow(),
                        tickers=[],
                    ))
            except Exception as e:
                print(f"[TwitterFetcher] @{username} error: {e}")

        return articles

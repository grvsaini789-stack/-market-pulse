import hashlib
from app.services.news_fetcher.base import RawArticle


def _simhash(text: str) -> int:
    """Simple 64-bit SimHash for near-duplicate detection."""
    tokens = text.lower().split()
    v = [0] * 64
    for token in tokens:
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        for i in range(64):
            v[i] += 1 if (h >> i) & 1 else -1
    return sum(1 << i for i in range(64) if v[i] > 0)


def _hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def deduplicate(articles: list[RawArticle], existing_urls: set[str]) -> list[RawArticle]:
    """Remove articles whose URL is already known, and near-duplicate titles."""
    seen_urls = set(existing_urls)
    seen_hashes: list[int] = []
    unique: list[RawArticle] = []

    for article in articles:
        if article.url in seen_urls:
            continue
        seen_urls.add(article.url)

        sh = _simhash(article.title)
        if any(_hamming(sh, h) <= 4 for h in seen_hashes):
            continue
        seen_hashes.append(sh)
        unique.append(article)

    return unique

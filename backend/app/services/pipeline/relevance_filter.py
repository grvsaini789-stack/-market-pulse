import json
import anthropic
from app.services.news_fetcher.base import RawArticle
from app.config import settings

THEMES = "geopolitics|monetary-policy|earnings|commodity|macro|regulatory|corporate"

SYSTEM_PROMPT = (
    "You are a financial analyst assistant. Assess news articles for market relevance. "
    "Respond ONLY with a JSON array — one object per article, same order as input."
)

ITEM_SCHEMA = """{
  "relevance_score": 0.0-1.0,
  "theme": \"""" + THEMES + """\",
  "tickers": ["ticker symbols mentioned, empty list if none"],
  "key_entities": ["countries, companies, people that matter to markets"],
  "reason": "one sentence"
}"""

# Keyword-based theme detection used as fallback when Claude is unavailable
_THEME_KEYWORDS = {
    "geopolitics":      ["war", "conflict", "sanction", "geopolit", "military", "iran", "russia", "china", "taiwan", "nato", "ukraine", "middle east", "missile", "tension"],
    "monetary-policy":  ["fed", "federal reserve", "rate hike", "rate cut", "interest rate", "rbi", "ecb", "central bank", "monetary", "quantitative", "inflation target", "powell", "lagarde"],
    "earnings":         ["earnings", "quarterly", "revenue", "profit", "eps", "guidance", "beat", "miss", "results", "q1", "q2", "q3", "q4", "annual report"],
    "commodity":        ["oil", "crude", "brent", "wti", "opec", "gold", "silver", "copper", "commodity", "metal", "wheat", "natural gas", "coal"],
    "regulatory":       ["sec", "sebi", "regulation", "fine", "penalty", "lawsuit", "antitrust", "ban", "comply", "compliance", "investigation", "probe"],
    "corporate":        ["merger", "acquisition", "buyout", "ipo", "ceo", "layoff", "restructur", "bankruptcy", "deal", "takeover", "spinoff"],
}


def _keyword_theme(text: str) -> str:
    lower = text.lower()
    scores = {theme: sum(1 for kw in kws if kw in lower) for theme, kws in _THEME_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "macro"


def _fallback_assessment(article: RawArticle) -> dict:
    text = f"{article.title} {article.summary}"
    return {
        "relevance_score": 0.7,
        "theme": _keyword_theme(text),
        "tickers": [],
        "key_entities": [],
    }


def _build_prompt(articles: list[RawArticle]) -> str:
    lines = ["Assess each article and return a JSON array:\n"]
    for i, a in enumerate(articles):
        lines.append(f"{i+1}. Title: {a.title}\n   Summary: {a.summary[:300]}\n   Source: {a.source}\n")
    lines.append(f"\nReturn a JSON array of {len(articles)} objects matching this schema:\n{ITEM_SCHEMA}")
    return "\n".join(lines)


async def filter_relevant(articles: list[RawArticle], min_score: float = 0.4) -> list[dict]:
    if not articles:
        return []

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    results = []
    batch_size = 20

    for i in range(0, len(articles), batch_size):
        batch = articles[i : i + batch_size]
        prompt = _build_prompt(batch)
        try:
            resp = client.messages.create(
                model="claude-opus-4-7",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            assessments = json.loads(text)
        except Exception as e:
            print(f"[RelevanceFilter] Claude error: {e}")
            assessments = [_fallback_assessment(a) for a in batch]

        for article, assessment in zip(batch, assessments):
            score = float(assessment.get("relevance_score", 0))
            if score >= min_score:
                results.append({
                    "article": article,
                    "relevance_score": score,
                    "theme": assessment.get("theme", _keyword_theme(f"{article.title} {article.summary}")),
                    "tickers": assessment.get("tickers", []),
                    "key_entities": assessment.get("key_entities", []),
                })

    return results

import json
import anthropic
from app.config import settings

SYSTEM_PROMPT = (
    "You are a financial news editor synthesizing market intelligence. "
    "Respond ONLY with a single JSON object."
)

SCHEMA = """{
  "title": "max 10 words, factual, present tense, suitable as a story card headline",
  "summary": "exactly 2 sentences — what is happening and why it matters to investors",
  "importance": 1-5
}"""


async def build_story_card(headlines: list[str], theme: str) -> dict:
    """
    Given a list of chronologically ordered headlines from a cluster,
    generate a story card title, summary, and importance score using claude-opus-4-7.
    """
    if not headlines:
        return {"title": "Market Development", "summary": "", "importance": 1}

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    headlines_text = "\n".join(f"- {h}" for h in headlines[:20])
    prompt = (
        f"These {len(headlines)} headlines are about the same developing {theme} market situation "
        f"(chronological order):\n\n{headlines_text}\n\n"
        f"Generate a story card. Schema:\n{SCHEMA}"
    )

    try:
        resp = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        result = json.loads(text)
        result["importance"] = max(1, min(5, int(result.get("importance", 3))))
        return result
    except Exception as e:
        print(f"[StoryBuilder] Claude error: {e}")
        return {"title": headlines[0][:80] if headlines else "Market Update", "summary": "", "importance": 2}

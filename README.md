# Market Pulse

AI-curated market news intelligence — one card per story, not per article.

Market Pulse collects news from across the web, groups related articles into story clusters using AI, and presents each ongoing market situation as a single card with a chronological timeline. Instead of seeing 20 separate articles about US-Iran tensions, you see one card that tracks the story as it develops.

![Market Pulse](https://img.shields.io/badge/status-active-brightgreen) ![Python](https://img.shields.io/badge/python-3.11-blue) ![Next.js](https://img.shields.io/badge/next.js-14-black)

---

## What it does

- Fetches news from DuckDuckGo search + 15 credible RSS sources (Reuters, Bloomberg, FT, WSJ, CNBC, ET, Mint, etc.)
- Uses **Claude Opus** to score market relevance, extract tickers and entities, and classify by theme
- Clusters related articles into story cards using **sentence-transformers** + **HDBSCAN**
- Generates AI story titles and summaries for each cluster
- Presents a card-based feed filtered by theme, sorted by importance

## Themes

| Theme | Examples |
|-------|---------|
| Geopolitics | Wars, sanctions, trade tensions |
| Monetary Policy | Fed/RBI/ECB rate decisions |
| Earnings | Company results, guidance |
| Commodity | Oil, gold, metals |
| Macro | Inflation, GDP, employment |
| Regulatory | SEBI, SEC, government policy |
| Corporate | M&A, IPOs, leadership changes |

---

## Tech Stack

**Backend** — FastAPI · SQLAlchemy · SQLite · APScheduler · Claude Opus 4.7 · sentence-transformers · HDBSCAN

**Frontend** — Next.js 14 · TypeScript · Tailwind CSS · TanStack Query · Zustand

---

## Getting Started

### Prerequisites

- Python 3.11
- Node.js 18+
- Anthropic API key (get one at [console.anthropic.com](https://console.anthropic.com))

### Backend

```bash
cd backend
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
py -3.11 -m pip install -r requirements.txt
py -3.11 -m uvicorn app.main:app --reload --port 8001
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3001](http://localhost:3001) in your browser.

Click **Refresh Feed** to run the first pipeline. It takes 1–2 minutes to fetch, filter, cluster, and generate story cards.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key for relevance filtering and story generation |
| `TWITTER_BEARER_TOKEN` | No | Twitter/X API v2 bearer token (paid) |
| `DATABASE_URL` | No | SQLite by default: `sqlite+aiosqlite:///./market_pulse.db` |
| `PIPELINE_INTERVAL_MINUTES` | No | Auto-run interval. Set to `99999` to disable auto-run |
| `NEWS_LOOKBACK_DAYS` | No | How many days of articles to keep (default: 14) |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend URL (default: `http://localhost:8001`) |

---

## How the Pipeline Works

```
1. Fetch     → DuckDuckGo news search (12 themed queries) + RSS feeds
2. Dedup     → Remove duplicate URLs and near-duplicate titles (SimHash)
3. Filter    → Claude Opus scores each article for market relevance (0–1)
4. Embed     → sentence-transformers generates vector embeddings locally
5. Cluster   → HDBSCAN groups related articles into story clusters
6. Summarize → Claude Opus generates story title, summary, importance score
7. Serve     → FastAPI serves clustered stories to the frontend
```

The pipeline runs manually via the **Refresh Feed** button, or automatically on a set interval.

---

## Project Structure

```
market-pulse/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Settings
│   │   ├── db/                  # SQLAlchemy models
│   │   ├── routers/             # API endpoints
│   │   └── services/
│   │       ├── news_fetcher/    # DDG, RSS, Twitter fetchers
│   │       └── pipeline/        # Filter, embed, cluster, build
│   └── requirements.txt
└── frontend/
    ├── app/                     # Next.js pages
    ├── components/              # React components
    ├── lib/api/                 # API client
    └── store/                   # Zustand state
```

---

## Notes

- The tool works without Claude credits using keyword-based fallback classification, but story titles and summaries will not be AI-generated
- Twitter/X integration requires a paid API v2 key
- RSS feeds require internet access; DuckDuckGo search has rate limits so queries run sequentially with a 2-second pause

from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy import select
from app.db.database import AsyncSessionLocal
from app.db.models import Article, StoryCluster
from app.services.news_fetcher.fetcher_factory import fetch_all
from app.services.pipeline.deduplicator import deduplicate
from app.services.pipeline.relevance_filter import filter_relevant
from app.services.pipeline.embedder import embed
from app.services.pipeline.clusterer import cluster_articles
from app.services.pipeline.story_builder import build_story_card
from app.services.pipeline.state import pipeline_state
from app.config import settings
import uuid


async def run_pipeline():
    if pipeline_state.is_running:
        print("[Pipeline] Already running, skipping.")
        return

    pipeline_state.is_running = True
    pipeline_state.last_run = datetime.utcnow()
    print(f"[Pipeline] Starting at {pipeline_state.last_run}")

    try:
        async with AsyncSessionLocal() as db:
            # Step 1: Fetch from all sources
            raw_articles = await fetch_all()
            print(f"[Pipeline] Fetched {len(raw_articles)} raw articles")

            # Step 2: Deduplicate against existing URLs
            cutoff = datetime.utcnow() - timedelta(days=settings.news_lookback_days)
            existing = await db.execute(select(Article.url).where(Article.created_at >= cutoff))
            existing_urls = {row[0] for row in existing.fetchall()}
            new_articles = deduplicate(raw_articles, existing_urls)
            print(f"[Pipeline] {len(new_articles)} articles after dedup")

            if not new_articles:
                print("[Pipeline] No new articles.")
                return

            # Step 3: Relevance filter via Claude Opus
            filtered = await filter_relevant(new_articles)
            print(f"[Pipeline] {len(filtered)} relevant articles")

            if not filtered:
                return

            # Step 4: Generate embeddings
            texts = [f"{f['article'].title}. {f['article'].summary[:200]}" for f in filtered]
            embeddings = embed(texts)

            # Step 5: Persist new articles (without cluster yet)
            new_db_articles: list[Article] = []
            for f, emb in zip(filtered, embeddings):
                a = f["article"]
                db_article = Article(
                    id=str(uuid.uuid4()),
                    url=a.url,
                    title=a.title,
                    summary=a.summary,
                    source=a.source,
                    published_at=a.published_at,
                    tickers=f["tickers"],
                    theme=f["theme"],
                    relevance_score=f["relevance_score"],
                    key_entities=f["key_entities"],
                    embedding=emb,
                )
                db.add(db_article)
                new_db_articles.append(db_article)
            await db.flush()

            # Step 6: Load all recent articles with embeddings for clustering
            result = await db.execute(
                select(Article).where(
                    Article.created_at >= cutoff,
                    Article.embedding.is_not(None),
                )
            )
            all_recent = result.scalars().all()
            all_ids = [a.id for a in all_recent]
            all_embeddings = [a.embedding for a in all_recent]

            if len(all_ids) < 2:
                await db.commit()
                return

            # Step 7: Cluster
            label_map = cluster_articles(all_ids, all_embeddings)

            # Group article IDs by cluster label
            label_to_ids: dict[int, list[str]] = defaultdict(list)
            for aid, label in label_map.items():
                label_to_ids[label].append(aid)

            # Build lookup for existing articles
            article_map = {a.id: a for a in all_recent}

            # Load existing clusters to reuse their IDs
            existing_clusters_result = await db.execute(select(StoryCluster))
            # Map: frozenset of article ids → cluster (not perfect but we'll use article cluster_id)
            # Instead, reassign based on re-clustering from scratch each run
            # Clear cluster assignments on all recent articles first, then reassign
            for a in all_recent:
                a.cluster_id = None

            await db.flush()

            # Delete clusters with no articles (will be recreated)
            stale_clusters = await db.execute(select(StoryCluster))
            for cluster in stale_clusters.scalars().all():
                await db.delete(cluster)
            await db.flush()

            # Step 8: Create clusters and assign articles
            for label, ids in label_to_ids.items():
                is_noise = label == -1
                articles_in_cluster = [article_map[aid] for aid in ids if aid in article_map]
                if not articles_in_cluster:
                    continue

                # For noise, each article is its own "developing" story
                if is_noise:
                    for art in articles_in_cluster:
                        cluster = StoryCluster(
                            id=str(uuid.uuid4()),
                            title=art.title[:100],
                            summary=art.summary[:300] or "Developing story — no additional context yet.",
                            theme=art.theme or "macro",
                            importance=max(1, min(5, int(art.relevance_score * 5))),
                            tickers=art.tickers,
                            first_seen_at=art.published_at,
                            last_updated_at=art.published_at,
                            article_count=1,
                            needs_rebuild=False,
                        )
                        db.add(cluster)
                        await db.flush()
                        art.cluster_id = cluster.id
                    continue

                # Proper cluster: generate story card
                sorted_arts = sorted(articles_in_cluster, key=lambda a: a.published_at)
                headlines = [a.title for a in sorted_arts]

                # Determine dominant theme
                from collections import Counter
                theme_counts = Counter(a.theme for a in articles_in_cluster if a.theme)
                dominant_theme = theme_counts.most_common(1)[0][0] if theme_counts else "macro"

                # Aggregate tickers
                all_tickers: list[str] = []
                for a in articles_in_cluster:
                    all_tickers.extend(a.tickers or [])
                unique_tickers = list(dict.fromkeys(all_tickers))[:10]

                card = await build_story_card(headlines, dominant_theme)

                cluster = StoryCluster(
                    id=str(uuid.uuid4()),
                    title=card.get("title", headlines[0][:80]),
                    summary=card.get("summary", ""),
                    theme=dominant_theme,
                    importance=card.get("importance", 3),
                    tickers=unique_tickers,
                    first_seen_at=sorted_arts[0].published_at,
                    last_updated_at=sorted_arts[-1].published_at,
                    article_count=len(articles_in_cluster),
                    needs_rebuild=False,
                )
                db.add(cluster)
                await db.flush()

                for art in articles_in_cluster:
                    art.cluster_id = cluster.id

            await db.commit()
            pipeline_state.articles_processed += len(new_db_articles)
            print(f"[Pipeline] Done. {len(new_db_articles)} new articles, {len(label_to_ids)} clusters.")

    except Exception as e:
        print(f"[Pipeline] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pipeline_state.is_running = False

import numpy as np
import hdbscan
from sklearn.preprocessing import normalize


def cluster_articles(
    article_ids: list[str],
    embeddings: list[list[float]],
    min_cluster_size: int = 3,
) -> dict[str, int]:
    """
    Returns mapping of article_id -> cluster_label.
    Label -1 means noise (single-article story).
    """
    if len(article_ids) < min_cluster_size:
        return {aid: -1 for aid in article_ids}

    X = normalize(np.array(embeddings, dtype=np.float32))
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=2,
        metric="euclidean",  # cosine via L2-normalized vectors
        cluster_selection_method="eom",
    )
    labels = clusterer.fit_predict(X)
    return {aid: int(label) for aid, label in zip(article_ids, labels)}

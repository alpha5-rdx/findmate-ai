"""Matching engine: semantic cosine similarity + small bounded metadata bonus."""
from __future__ import annotations

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from ai.embedder import embed_one, embed_texts, item_text
from config import (CATEGORY_BONUS, HIGH_CONFIDENCE, LOCATION_BONUS,
                    MEDIUM_CONFIDENCE, MIN_SEMANTIC_SIMILARITY)
from database import db


def confidence_label(score: float) -> str:
    if score >= HIGH_CONFIDENCE:
        return "High"
    if score >= MEDIUM_CONFIDENCE:
        return "Medium"
    return "Low"


def embedding_for(name: str, description: str, category: str) -> np.ndarray:
    return embed_texts([item_text(name, description, category)])[0]


def ensure_embeddings(items: list[dict]) -> None:
    """Compute and persist embeddings for any item that lacks one (batched)."""
    missing = [i for i in items if i.get("embedding") is None]
    if not missing:
        return
    vecs = embed_texts([item_text(i["name"], i["description"], i["category"]) for i in missing])
    for item, vec in zip(missing, vecs):
        db.set_embedding(item["id"], vec)
        item["embedding"] = vec.tobytes()


def _location_similarity(a: str, b: str) -> float:
    """0..1 semantic closeness of two place names ("Central Library" ~ "Main Library")."""
    if not a.strip() or not b.strip():
        return 0.0
    sim = float(cosine_similarity([embed_one(a)], [embed_one(b)])[0, 0])
    # Embeddings of any two place names are mildly similar; rescale so only
    # clearly related places earn a bonus.
    return float(np.clip((sim - 0.4) / 0.6, 0.0, 1.0))


def combined_score(semantic: float, same_category: bool, location_sim: float) -> float:
    """Final ranking score.

    score = semantic + CATEGORY_BONUS*[same category] + LOCATION_BONUS*location_sim

    * Semantic cosine similarity is the backbone of the score.
    * Metadata can add at most CATEGORY_BONUS + LOCATION_BONUS (= 0.09), so it
      can reorder close candidates but never lift an unrelated pair.
    * Pairs below MIN_SEMANTIC_SIMILARITY get no bonus at all (they are dropped).
    """
    if semantic < MIN_SEMANTIC_SIMILARITY:
        return semantic
    bonus = CATEGORY_BONUS * float(same_category) + LOCATION_BONUS * location_sim
    return float(min(1.0, semantic + bonus))


def run_matching() -> int:
    """Re-score every open lost item against every open found item and store candidates.

    Returns the number of candidate pairs stored.
    """
    lost = db.list_items("lost", "open")
    found = db.list_items("found", "open")
    rows: list[tuple[int, int, float, float]] = []
    if lost and found:
        ensure_embeddings(lost + found)
        L = np.vstack([db.blob_to_vec(i["embedding"]) for i in lost])
        F = np.vstack([db.blob_to_vec(i["embedding"]) for i in found])
        sims = cosine_similarity(L, F)  # (n_lost x n_found) matrix in one call
        for a, li in enumerate(lost):
            for b, fj in enumerate(found):
                sem = float(sims[a, b])
                if sem < MIN_SEMANTIC_SIMILARITY:
                    continue
                loc = _location_similarity(li["location"], fj["location"])
                score = combined_score(sem, li["category"] == fj["category"], loc)
                rows.append((li["id"], fj["id"], sem, score))
    db.replace_pending_matches(rows)
    return len(rows)


def semantic_search(query: str, kind: str | None = None, category: str | None = None,
                    include_resolved: bool = False, top_k: int = 20) -> list[dict]:
    """Natural-language search: embed the query and rank items by cosine similarity."""
    query = (query or "").strip()
    if len(query) < 3:
        return []
    items = db.list_items(kind, None if include_resolved else "open")
    if category and category != "All":
        items = [i for i in items if i["category"] == category]
    if not items:
        return []
    ensure_embeddings(items)
    M = np.vstack([db.blob_to_vec(i["embedding"]) for i in items])
    sims = cosine_similarity(embed_texts([query]), M)[0]
    order = np.argsort(-sims)[:top_k]
    return [{**items[i], "similarity": float(sims[i])} for i in order]

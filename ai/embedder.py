"""Sentence-embedding wrapper (all-MiniLM-L6-v2).

The model is loaded once per process (lazily) and text embeddings for short,
repeated strings (e.g. locations, search queries) are cached in memory.
Item embeddings are persisted in SQLite, so they are computed only when an
item is created or edited.
"""
from __future__ import annotations

import threading
from functools import lru_cache
from typing import Iterable

import numpy as np

from config import MODEL_NAME


class ModelLoadError(RuntimeError):
    """Raised when the embedding model cannot be loaded."""


RECOVERY_HELP = (
    "The embedding model could not be loaded. Recovery steps:\n"
    "1. Make sure dependencies are installed: `pip install -r requirements.txt`.\n"
    f"2. The first run downloads `{MODEL_NAME}` (~90 MB) from huggingface.co, "
    "so an internet connection is required once.\n"
    "3. Behind a proxy/firewall? Set HTTPS_PROXY, or download the model manually "
    "and place it in `~/.cache/huggingface`.\n"
    "4. Then restart the app: `streamlit run app.py`."
)

_model = None
_lock = threading.Lock()


def get_model():
    """Load the SentenceTransformer once and reuse it."""
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                try:
                    from sentence_transformers import SentenceTransformer
                    _model = SentenceTransformer(MODEL_NAME)
                except Exception as exc:  # network, missing package, corrupt cache...
                    raise ModelLoadError(f"{exc}\n\n{RECOVERY_HELP}") from exc
    return _model


def item_text(name: str, description: str, category: str) -> str:
    """Text used for the semantic embedding of an item.

    Name + description + category are combined so that a short name such as
    "Wallet" is enriched by the free-text description. Missing description
    simply falls back to the name. Category and location are deliberately kept
    out of this text: they are handled as small, bounded side signals in
    matcher.py, which avoids double counting and stops shared category words
    from inflating similarity between unrelated items. `category` is accepted
    only so callers have a stable signature.
    """
    parts = [(name or "").strip(), (description or "").strip()]
    return ". ".join(p for p in parts if p) or (category or "unknown")


def embed_texts(texts: Iterable[str]) -> np.ndarray:
    """Encode texts into L2-normalised float32 vectors (shape: n x 384)."""
    texts = [t if t and t.strip() else "unknown" for t in texts]
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)
    vecs = get_model().encode(texts, normalize_embeddings=True,
                              show_progress_bar=False, convert_to_numpy=True)
    return vecs.astype(np.float32)


@lru_cache(maxsize=2048)
def _cached_one(text: str) -> bytes:
    return embed_texts([text])[0].tobytes()


def embed_one(text: str) -> np.ndarray:
    """Embed a single string with an in-memory cache (locations, queries)."""
    return np.frombuffer(_cached_one((text or "").strip().lower()), dtype=np.float32)

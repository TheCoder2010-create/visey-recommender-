from __future__ import annotations
from typing import Any

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except Exception:  # pragma: no cover
    SentenceTransformer = None  # type: ignore
    np = None  # type: ignore


class EmbeddingHelper:
    """Optional embedding helper using SentenceTransformers.

    If dependencies are missing, initialization will raise to signal caller to skip.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        if SentenceTransformer is None:
            raise RuntimeError("sentence-transformers not installed")
        if np is None:
            raise RuntimeError("numpy not available")
        self.model = SentenceTransformer(model_name)

    def encode(self, text: str):
        return self.model.encode(text, normalize_embeddings=True)

    def similarity(self, a: Any, b: Any) -> float:
        # cosine similarity for L2-normalized vectors
        return float((a @ b).item() if hasattr(a, "shape") else (a * b).sum())

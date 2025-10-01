from __future__ import annotations
from collections import Counter
from typing import Dict, List, Tuple

from ..storage.feedback_store import FeedbackStore

class PopularityService:
    """Computes popular or trending resources from feedback data."""

    def __init__(self, store: FeedbackStore | None = None) -> None:
        self.store = store or FeedbackStore()

    def top_resources(self, top_n: int = 10) -> List[Tuple[int, float]]:
        """Return top resources as (resource_id, score) sorted by score desc.
        Score blends count and average rating if available.
        """
        data = self.store.get_all_feedback()
        if not data:
            return []

        # Aggregate counts and ratings
        counts: Counter[int] = Counter()
        ratings: Dict[int, List[int]] = {}
        for _user_id, rid, rating in data:
            counts[rid] += 1
            if rating is not None:
                ratings.setdefault(rid, []).append(rating)

        scored: List[Tuple[int, float]] = []
        for rid, cnt in counts.items():
            avg_rating = sum(ratings.get(rid, []) or [3]) / len(ratings.get(rid, []) or [1])
            score = cnt + 0.5 * (avg_rating - 3)  # small rating boost
            scored.append((rid, float(score)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_n]

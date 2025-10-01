from __future__ import annotations
import os
import sqlite3
from typing import List, Tuple

from ..config import settings

class FeedbackStore:
    """SQLite-backed feedback storage for user-resource ratings and interactions."""

    def __init__(self, path: str | None = None) -> None:
        self.path = path or settings.SQLITE_FEEDBACK_PATH
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    user_id INTEGER NOT NULL,
                    resource_id INTEGER NOT NULL,
                    rating INTEGER,
                    ts DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, resource_id)
                )
                """
            )
            conn.commit()

    def upsert_feedback(self, user_id: int, resource_id: int, rating: int | None) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "REPLACE INTO feedback(user_id, resource_id, rating, ts) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                (user_id, resource_id, rating),
            )
            conn.commit()

    def get_user_feedback(self, user_id: int) -> List[Tuple[int, int | None]]:
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute(
                "SELECT resource_id, rating FROM feedback WHERE user_id=? ORDER BY ts DESC",
                (user_id,),
            ).fetchall()
        return [(int(r[0]), int(r[1]) if r[1] is not None else None) for r in rows]

    def get_all_feedback(self) -> List[Tuple[int, int, int | None]]:
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute(
                "SELECT user_id, resource_id, rating FROM feedback"
            ).fetchall()
        return [(int(r[0]), int(r[1]), int(r[2]) if r[2] is not None else None) for r in rows]

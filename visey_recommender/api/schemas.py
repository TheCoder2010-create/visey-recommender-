from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel

class RecommendResponseItem(BaseModel):
    resource_id: int
    title: Optional[str]
    link: Optional[str]
    score: float
    reason: str

class RecommendResponse(BaseModel):
    user_id: int
    items: List[RecommendResponseItem]

class FeedbackResponse(BaseModel):
    ok: bool

from __future__ import annotations
from typing import Dict, List, Tuple
import math
import time

import numpy as np
import structlog

from ..config import settings
from ..data.models import Resource, UserProfile, Recommendation
from ..features.engineer import build_resource_vector, build_user_vector, cosine_similarity
from ..services.popularity import PopularityService
from ..storage.feedback_store import FeedbackStore
from ..utils.metrics import track_time
from .matrix_factorization import MatrixFactorizationRecommender

logger = structlog.get_logger(__name__)

try:
    from ..embeddings.semantic import EmbeddingHelper  # optional
except Exception:  # pragma: no cover
    EmbeddingHelper = None  # type: ignore


class BaselineRecommender:
    """Content-based + simple collaborative filtering combiner with optional embeddings."""

    def __init__(self, feedback: FeedbackStore | None = None, popularity: PopularityService | None = None):
        self.feedback = feedback or FeedbackStore()
        self.popularity = popularity or PopularityService(self.feedback)
        self.mf_recommender = MatrixFactorizationRecommender(self.feedback)
        self.emb: EmbeddingHelper | None = None
        if EmbeddingHelper is not None and settings.EMB_WEIGHT > 0:
            try:
                self.emb = EmbeddingHelper()
            except Exception:
                self.emb = None

    def _implicit_tokens(self, user_id: int) -> List[str]:
        # Derive implicit tokens from past usage (resource ids used as tokens)
        interactions = self.feedback.get_user_feedback(user_id)
        tokens: List[str] = [f"resource:{rid}" for rid, _ in interactions]
        return tokens

    def _build_content_scores(self, profile: UserProfile, resources: List[Resource]) -> Dict[int, float]:
        implicit = self._implicit_tokens(profile.user_id)
        uvec = build_user_vector(profile, implicit)
        scores: Dict[int, float] = {}
        for r in resources:
            rvec = build_resource_vector(r)
            scores[r.id] = cosine_similarity(uvec, rvec)
        return scores

    def _build_collab_scores(self, user_id: int, resources: List[Resource]) -> Dict[int, float]:
        # Simple item-item co-occurrence: score by overlap with user's interacted items
        interactions = self.feedback.get_user_feedback(user_id)
        user_items = set([rid for rid, _ in interactions])
        if not user_items:
            return {r.id: 0.0 for r in resources}

        all_fb = self.feedback.get_all_feedback()
        # Build item -> set(users)
        item_users: Dict[int, set[int]] = {}
        for uid, rid, _rating in all_fb:
            item_users.setdefault(rid, set()).add(uid)

        def jaccard(a: set[int], b: set[int]) -> float:
            if not a or not b:
                return 0.0
            inter = len(a & b)
            union = len(a | b)
            return inter / union if union > 0 else 0.0

        # For candidate resource r, compute max similarity to items user interacted with
        scores: Dict[int, float] = {}
        for r in resources:
            if r.id in user_items:
                scores[r.id] = 0.0
                continue
            r_users = item_users.get(r.id, set())
            sim = 0.0
            for ui in user_items:
                sim = max(sim, jaccard(r_users, item_users.get(ui, set())))
            scores[r.id] = sim
        return scores

    def _embedding_scores(self, profile: UserProfile, resources: List[Resource]) -> Dict[int, float]:
        if not self.emb:
            return {r.id: 0.0 for r in resources}
        # Use profile text summary vs resource title/excerpt
        profile_text = \
            f"industry: {profile.industry}; stage: {profile.stage}; team: {profile.team_size}; funding: {profile.funding}; location: {profile.location}"
        pvec = self.emb.encode(profile_text)
        scores: Dict[int, float] = {}
        for r in resources:
            text = f"{r.title} {r.excerpt}".strip()
            rvec = self.emb.encode(text)
            scores[r.id] = self.emb.similarity(pvec, rvec)
        return scores

    def _explanations(self, profile: UserProfile, resource: Resource) -> str:
        reasons: List[str] = []
        # Heuristics based on matching tokens
        if profile.industry and resource.meta and str(profile.industry).lower() in str(resource.meta).lower():
            reasons.append("industry match")
        if profile.stage and resource.meta and str(profile.stage).lower() in str(resource.meta).lower():
            reasons.append("stage relevance")
        if profile.location and resource.meta and str(profile.location).lower() in str(resource.meta).lower():
            reasons.append("region relevance")
        if not reasons:
            reasons.append("similar to your past activity")
        return ", ".join(reasons)

    @track_time("baseline_recommendation")
    def recommend(self, profile: UserProfile, resources: List[Resource], top_n: int | None = None) -> List[Recommendation]:
        if top_n is None:
            top_n = settings.TOP_N
        if not resources:
            logger.warning("no_resources_for_recommendation", user_id=profile.user_id)
            return []

        logger.info("generating_recommendations", 
                   user_id=profile.user_id, 
                   n_resources=len(resources), 
                   top_n=top_n)

        # Get different types of scores
        cb = self._build_content_scores(profile, resources)
        cf = self._build_collab_scores(profile.user_id, resources)
        emb = self._embedding_scores(profile, resources) if settings.EMB_WEIGHT > 0 else {r.id: 0.0 for r in resources}
        
        # Get matrix factorization scores
        mf_scores = self._get_mf_scores(profile, resources)

        # popularity for cold start boost
        pop_pairs = self.popularity.top_resources(top_n=100)
        max_pop = max([p for _, p in pop_pairs], default=1.0)
        pop_scores: Dict[int, float] = {rid: (score / max_pop if max_pop > 0 else 0.0) for rid, score in pop_pairs}

        # Combine all scores with weights
        combined: List[Tuple[int, float]] = []
        for r in resources:
            # Base score combination
            score = (
                settings.CONTENT_WEIGHT * cb.get(r.id, 0.0)
                + settings.COLLAB_WEIGHT * cf.get(r.id, 0.0)
                + settings.POP_WEIGHT * pop_scores.get(r.id, 0.0)
                + settings.EMB_WEIGHT * emb.get(r.id, 0.0)
            )
            
            # Add matrix factorization score if available
            mf_score = mf_scores.get(r.id, 0.0)
            if mf_score > 0:
                score += 0.2 * mf_score  # Additional weight for MF
            
            combined.append((r.id, float(score)))

        # Apply diversity filtering
        combined = self._apply_diversity_filter(combined, resources)

        combined.sort(key=lambda x: x[1], reverse=True)
        top = combined[:top_n]
        
        # Build recommendations with reasons
        id_to_resource: Dict[int, Resource] = {r.id: r for r in resources}
        recs: List[Recommendation] = []
        for rid, score in top:
            r = id_to_resource.get(rid)
            if not r:
                continue
            reason = self._explanations(profile, r)
            recs.append(Recommendation(resource_id=rid, score=float(score), reason=reason, title=r.title, link=r.link))
        
        logger.info("recommendations_generated", 
                   user_id=profile.user_id, 
                   count=len(recs),
                   avg_score=sum(rec.score for rec in recs) / len(recs) if recs else 0)
        
        return recs
    
    def _get_mf_scores(self, profile: UserProfile, resources: List[Resource]) -> Dict[int, float]:
        """Get matrix factorization scores."""
        try:
            mf_recs = self.mf_recommender.recommend(profile, resources, top_n=len(resources))
            return {rec.resource_id: rec.score for rec in mf_recs}
        except Exception as e:
            logger.warning("mf_scoring_failed", user_id=profile.user_id, error=str(e))
            return {}
    
    def _apply_diversity_filter(self, scored_items: List[Tuple[int, float]], resources: List[Resource]) -> List[Tuple[int, float]]:
        """Apply diversity filtering to avoid too similar recommendations."""
        if len(scored_items) <= 10:
            return scored_items
        
        # Create resource lookup
        resource_dict = {r.id: r for r in resources}
        
        # Group by categories to ensure diversity
        category_counts = {}
        filtered_items = []
        
        for resource_id, score in scored_items:
            resource = resource_dict.get(resource_id)
            if not resource or not resource.categories:
                filtered_items.append((resource_id, score))
                continue
            
            # Get primary category
            primary_category = resource.categories[0] if resource.categories else "uncategorized"
            
            # Limit items per category
            if category_counts.get(primary_category, 0) < 3:  # Max 3 per category
                filtered_items.append((resource_id, score))
                category_counts[primary_category] = category_counts.get(primary_category, 0) + 1
        
        return filtered_items

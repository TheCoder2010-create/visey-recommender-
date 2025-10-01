from __future__ import annotations
import hashlib
from typing import Dict, List, Tuple
import numpy as np

from ..data.models import Resource, UserProfile

VECTOR_SIZE = 256  # lightweight hashing trick dimension


def _tokenize_profile(p: UserProfile) -> List[str]:
    toks: List[str] = []
    if p.industry:
        toks.append(f"industry:{p.industry.lower()}")
    if p.stage:
        toks.append(f"stage:{p.stage.lower()}")
    if p.team_size:
        toks.append(f"team:{p.team_size.lower()}")
    if p.funding:
        toks.append(f"funding:{p.funding.lower()}")
    if p.location:
        toks.append(f"location:{p.location.lower()}")
    return toks


def _tokenize_resource(r: Resource) -> List[str]:
    toks: List[str] = []
    toks.extend([f"cat:{c}" for c in r.categories])
    toks.extend([f"tag:{t}" for t in r.tags])
    # include selected custom fields if present
    for k, v in (r.meta or {}).items():
        if isinstance(v, (str, int)):
            toks.append(f"meta:{k}:{str(v).lower()}")
    return toks


def _hash_to_vec(tokens: List[str]) -> np.ndarray:
    vec = np.zeros(VECTOR_SIZE, dtype=np.float32)
    if not tokens:
        return vec
    for t in tokens:
        h = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16)
        idx = h % VECTOR_SIZE
        vec[idx] += 1.0
    # l2 normalize
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def build_user_vector(profile: UserProfile, implicit_tokens: List[str] | None = None) -> np.ndarray:
    tokens = _tokenize_profile(profile)
    if implicit_tokens:
        tokens.extend([f"implicit:{tok}" for tok in implicit_tokens])
    return _hash_to_vec(tokens)


def build_resource_vector(resource: Resource) -> np.ndarray:
    return _hash_to_vec(_tokenize_resource(resource))


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    if a.shape != b.shape:
        return 0.0
    num = float(np.dot(a, b))
    den = float(np.linalg.norm(a) * np.linalg.norm(b))
    return num / den if den > 0 else 0.0

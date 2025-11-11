from __future__ import annotations

from typing import Iterable, List, Optional

import numpy as np
import torch
from sqlalchemy.orm import Session

from ..models.user_reviews import User_Reviews
from ..models.products import Products
from ..services.product_service import update_sentiment_score_and_label

# ------------------------------------------------------------------
# HuggingFace SentenceTransformer (optional). Fallback to heuristic
# if the model or dependencies aren't available.
# ------------------------------------------------------------------
_MODEL = None
_POS_EMBS = None
_NEG_EMBS = None
_MODEL_NAME = "dangvantuan/vietnamese-document-embedding"
_DEVICE = "cpu"

_POSITIVE_ANCHORS = [
    "rất tốt",
    "tuyệt vời",
    "hài lòng",
    "xuất sắc",
    "chất lượng",
    "đáng mua",
    "ổn",
]
_NEGATIVE_ANCHORS = [
    "tệ",
    "kém",
    "thất vọng",
    "hỏng",
    "lỗi",
    "quá tệ",
    "kém chất lượng",
]


def _select_device() -> str:
    """Pick best available device: CUDA > MPS > CPU."""
    try:
        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"


def _load_model():
    global _MODEL, _DEVICE
    if _MODEL is not None:
        return _MODEL
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        _DEVICE = _select_device()
        _MODEL = SentenceTransformer(_MODEL_NAME, trust_remote_code=True, device=_DEVICE)
        try:
            _MODEL.to(_DEVICE)  # type: ignore[attr-defined]
        except Exception:
            pass
    except Exception:
        _MODEL = None
        _DEVICE = "cpu"
    return _MODEL


def _ensure_anchor_embeddings():
    global _POS_EMBS, _NEG_EMBS
    if _POS_EMBS is not None and _NEG_EMBS is not None:
        return _POS_EMBS, _NEG_EMBS
    model = _load_model()
    if model is None:
        return None, None
    pos = model.encode(_POSITIVE_ANCHORS, convert_to_tensor=True, normalize_embeddings=True)
    neg = model.encode(_NEGATIVE_ANCHORS, convert_to_tensor=True, normalize_embeddings=True)
    try:
        pos = pos.to(_DEVICE)
        neg = neg.to(_DEVICE)
    except Exception:
        pass
    _POS_EMBS, _NEG_EMBS = pos, neg
    return _POS_EMBS, _NEG_EMBS


def _score_with_model(texts: List[str]) -> Optional[List[float]]:
    model = _load_model()
    pos, neg = _ensure_anchor_embeddings()
    if model is None or pos is None or neg is None:
        return None

    arr = model.encode(texts, convert_to_tensor=True, normalize_embeddings=True)
    try:
        arr = arr.to(_DEVICE)
    except Exception:
        pass
    # cosine similarity since embeddings are normalized
    pos_sim = arr @ pos.T  # (n_texts, n_pos)
    neg_sim = arr @ neg.T  # (n_texts, n_neg)
    pos_mean = pos_sim.mean(dim=1)
    neg_mean = neg_sim.mean(dim=1)
    raw = pos_mean - neg_mean  # roughly in [-2, 2]
    scores = torch.clamp(raw / 2.0, -1.0, 1.0)
    return scores.detach().cpu().tolist()


def analyze_comment(text: str) -> float:
    """Analyze sentiment using embedding model if available, else heuristic.

    Returns score in [-1, 1].
    """
    if not text:
        return 0.0
    scores = _score_with_model([text])
    if scores is not None:
        return float(scores[0])

    # Heuristic fallback (no model available)
    t = text.lower()
    positives = ["tuyệt", "tốt", "ok", "hài lòng", "ưng", "đẹp", "xuất sắc", "chất lượng"]
    negatives = ["tệ", "kém", "xấu", "thất vọng", "dở", "lỗi", "hỏng", "chậm"]
    score = 0
    for w in positives:
        if w in t:
            score += 1
    for w in negatives:
        if w in t:
            score -= 1
    return max(-1.0, min(1.0, score / 3.0))


def label_sentiment(score: float) -> str:
    if score >= 0.6:
        return "Tốt"
    if score >= 0.2:
        return "Trung bình"
    return "Kém"


def _collect_comments_for_product(db: Session, product: Products) -> List[str]:
    """Collect comments from User_Reviews and/or Tiki based on availability.

    Rule:
    - If External_ID is missing: only use User_Reviews.
    - If External_ID exists:
        - If product has user reviews: combine both sources (user + Tiki).
        - If no user reviews: use only Tiki reviews.
    """
    comments: List[str] = []

    # Fetch user reviews (comments)
    user_reviews: List[User_Reviews] = (
        db.query(User_Reviews)
        .filter(User_Reviews.Product_ID == product.Product_ID)
        .all()
    )
    user_texts = [(r.Comment or "").strip() for r in user_reviews if (r.Comment or "").strip()]

    if product.External_ID is None:
        return user_texts  # only source available
    from .crawler_tiki_service import get_product_reviews
    # External_ID exists → consider Tiki
    tiki_texts: List[str] = get_product_reviews(int(product.External_ID)) or []

    if user_texts:
        comments.extend(user_texts)
        comments.extend(tiki_texts)
    else:
        comments.extend(tiki_texts)

    return comments


def update_product_sentiment(db: Session, product_id: int) -> Optional[float]:
    """Compute sentiment score from reviews (user + Tiki per rule) and update product."""
    product: Optional[Products] = (
        db.query(Products).filter(Products.Product_ID == product_id).first()
    )
    if not product:
        return None

    comments = _collect_comments_for_product(db, product)
    comments = [c for c in comments if c]

    # If no text comments at all, optionally fallback to user ratings
    if not comments:
        user_reviews: List[User_Reviews] = (
            db.query(User_Reviews)
            .filter(User_Reviews.Product_ID == product_id)
            .all()
        )
        if not user_reviews:
            update_sentiment_score_and_label(db, product_id, score=None, label=None)
            return None
        scores: List[float] = []
        for r in user_reviews:
            rating = (r.Rating or 0)
            # map 1..5 to [-1..1]
            s = (max(1, min(5, rating)) - 3) / 2.0
            scores.append(s)
        avg = sum(scores) / len(scores) if scores else 0.0
        label = label_sentiment(avg)
        update_sentiment_score_and_label(db, product_id, score=avg, label=label)
        return avg

    # Analyze text comments with model if available
    scores = _score_with_model(comments)
    if scores is None:
        scores = [analyze_comment(t) for t in comments]

    if not scores:
        update_sentiment_score_and_label(db, product_id, score=None, label=None)
        return None
    avg = sum(scores) / len(scores)
    label = label_sentiment(avg)
    update_sentiment_score_and_label(db, product_id, score=avg, label=label)
    return avg


def analyze_bulk(comments: Iterable[str]) -> List[float]:
    texts = [c for c in comments if c]
    if not texts:
        return []
    scores = _score_with_model(texts)
    if scores is not None:
        return [float(s) for s in scores]
    return [analyze_comment(c) for c in texts]


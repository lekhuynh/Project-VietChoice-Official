from __future__ import annotations

from typing import Iterable, List, Optional
import numpy as np
import torch
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from ..models.user_reviews import User_Reviews
from ..models.products import Products
from ..services.product_service import update_sentiment_score_and_label

# ==========================================================
# Model config
# ==========================================================
_MODEL = None
_POS_EMBS = None
_NEG_EMBS = None
_MODEL_NAME = "dangvantuan/vietnamese-document-embedding"
_MODEL_REVISION = "6fa4e2f"
_DEVICE = "cpu"

# ==========================================================
# Anchors (tối ưu – rút gọn – giảm lệch)
# ==========================================================
_POSITIVE_ANCHORS = [
    "rất tốt", "tuyệt vời", "ưng ý", "hài lòng",
    "chất lượng tốt", "đáng mua", "đúng mô tả",
    "giao nhanh", "đẹp", "uy tín",
]

_NEGATIVE_ANCHORS = [
    "tệ", "rất tệ", "kém chất lượng", "thất vọng",
    "fake", "hàng nhái", "lừa đảo", "sai mô tả",
    "bị lỗi", "không dùng được",
]


# ==========================================================
# Device selection
# ==========================================================
def _select_device() -> str:
    try:
        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"


# ==========================================================
# Load embedding model
# ==========================================================
def _load_model():
    global _MODEL, _DEVICE
    if _MODEL is not None:
        return _MODEL
    try:
        from sentence_transformers import SentenceTransformer
        _DEVICE = _select_device()
        _MODEL = SentenceTransformer(
            _MODEL_NAME,
            revision=_MODEL_REVISION,
            trust_remote_code=True,
            device=_DEVICE,
            cache_folder="/app/hf_cache"
        )
    except Exception:
        _MODEL = None
        _DEVICE = "cpu"
    return _MODEL


# ==========================================================
# Encode anchors
# ==========================================================
def _ensure_anchor_embeddings():
    global _POS_EMBS, _NEG_EMBS
    if _POS_EMBS is not None and _NEG_EMBS is not None:
        return _POS_EMBS, _NEG_EMBS

    model = _load_model()
    if model is None:
        return None, None

    pos = model.encode(_POSITIVE_ANCHORS, normalize_embeddings=True)
    neg = model.encode(_NEGATIVE_ANCHORS, normalize_embeddings=True)

    _POS_EMBS = np.array(pos)
    _NEG_EMBS = np.array(neg)

    return _POS_EMBS, _NEG_EMBS


# ==========================================================
# Compute score (tối ưu – không âm oan)
# ==========================================================
def _compute_score(pos_mean: float, neg_mean: float) -> float:
    raw = pos_mean - neg_mean
    score = np.tanh(raw * 1.5)   # scale cực đẹp [-1,1]
    return float(score)


# ==========================================================
# Score using model
# ==========================================================
def _score_with_model(texts: List[str]) -> Optional[List[float]]:
    model = _load_model()
    pos_embs, neg_embs = _ensure_anchor_embeddings()
    if model is None or pos_embs is None or neg_embs is None:
        return None

    # Encode text
    arr = model.encode(texts, normalize_embeddings=True)
    arr = np.array(arr)

    # Cosine similarity chuẩn
    pos_sim = cosine_similarity(arr, pos_embs).mean(axis=1)
    neg_sim = cosine_similarity(arr, neg_embs).mean(axis=1)

    scores = [_compute_score(float(p), float(n)) for p, n in zip(pos_sim, neg_sim)]
    return scores


# ==========================================================
# Analyze comment
# ==========================================================
def analyze_comment(text: str) -> float:
    if not text:
        return 0.0
    scores = _score_with_model([text])
    if scores is not None:
        return float(scores[0])

    # fallback heuristic
    t = text.lower()
    positives = ["tốt", "tuyệt", "ưng", "hài lòng", "đáng mua", "đúng mô tả"]
    negatives = ["tệ", "kém", "thất vọng", "fake", "nhái", "lừa đảo"]

    score = 0
    score += sum(1 for w in positives if w in t)
    score -= sum(1 for w in negatives if w in t)

    return max(-1.0, min(1.0, score / 3.0))


# ==========================================================
# Sentiment label
# ==========================================================
def label_sentiment(score: float) -> str:
    if score >= 0.4:
        return "positive"
    if score >= -0.1:
        return "neutral"
    return "negative"


# ==========================================================
# Collect comments
# ==========================================================
def _collect_comments_for_product(db: Session, product: Products) -> List[str]:
    comments: List[str] = []

    user_reviews: List[User_Reviews] = (
        db.query(User_Reviews)
        .filter(User_Reviews.Product_ID == product.Product_ID)
        .all()
    )
    user_texts = [(r.Comment or "").strip() for r in user_reviews if r.Comment]

    if product.External_ID is None:
        return user_texts

    from .crawler_tiki_service import get_product_reviews
    tiki_texts: List[str] = get_product_reviews(int(product.External_ID)) or []

    if user_texts:
        comments.extend(user_texts)
        comments.extend(tiki_texts)
    else:
        comments.extend(tiki_texts)

    return comments


# ==========================================================
# UPDATE PRODUCT SENTIMENT
# ==========================================================
def update_product_sentiment(db: Session, product_id: int) -> Optional[float]:
    product: Optional[Products] = (
        db.query(Products).filter(Products.Product_ID == product_id).first()
    )
    if not product:
        return None

    comments = _collect_comments_for_product(db, product)
    comments = [c for c in comments if c]

    if not comments:
        user_reviews = (
            db.query(User_Reviews)
            .filter(User_Reviews.Product_ID == product_id)
            .all()
        )
        if not user_reviews:
            update_sentiment_score_and_label(db, product_id, None, None)
            return None

        scores = []
        for r in user_reviews:
            rating = (r.Rating or 0)
            s = (max(1, min(5, rating)) - 3) / 2.0
            scores.append(s)

        avg = sum(scores) / len(scores)
        label = label_sentiment(avg)
        update_sentiment_score_and_label(db, product_id, avg, label)
        return avg

    scores = _score_with_model(comments)
    if scores is None:
        scores = [analyze_comment(t) for t in comments]

    avg = float(np.mean(scores))
    label = label_sentiment(avg)
    update_sentiment_score_and_label(db, product_id, avg, label)
    return avg

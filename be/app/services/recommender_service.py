from sqlalchemy import case, desc, and_, or_
from sqlalchemy.orm import Session
from typing import Sequence
from ..models.products import Products
from ..services.risk_service import evaluate_risk
from ..cache import get_json, set_json


def recommend_best_in_category(db: Session, product_id: int, limit: int = 5) -> Sequence[Products]:
    """
    Gợi ý sản phẩm:
    - Cùng Category_ID
    - Loại sentiment kém, risk cao, review quá ít (<3)
    - Giá ~70% - 130% sản phẩm gốc
    - Ưu tiên sentiment_score > avg_rating > review_count
    """

    base = db.query(Products).filter(Products.Product_ID == product_id).first()
    if not base or not base.Category_ID:
        return []

    price = float(base.Price) if base.Price is not None else None

    min_price = price * 0.7 if price else 0
    max_price = price * 1.3 if price else 999999999

    candidates = (
        db.query(Products)
        .filter(
            Products.Category_ID == base.Category_ID,
            Products.Product_ID != product_id,
            Products.Is_Active == True,
            or_(Products.Sentiment_Label != "Kém", Products.Sentiment_Label.is_(None)),
            or_(Products.Review_Count >= 3, Products.Review_Count.is_(None)),
            and_(Products.Price >= min_price, Products.Price <= max_price),
        )
        .order_by(
            desc(case((Products.Sentiment_Score.isnot(None), 1), else_=0)),
            desc(Products.Sentiment_Score),
            desc(Products.Avg_Rating),
            desc(Products.Review_Count)
        )
        .limit(100)  # tránh quét quá nhiều
        .all()
    )

    safe_products = []
    for p in candidates:
        cache_key = f"cache:risk:{p.Product_ID}"
        risk = get_json(cache_key)
        if not risk:
            risk = evaluate_risk(p, db)
            set_json(cache_key, risk, ttl_seconds=3600)
        if risk.get("risk_score", 1) < 0.6:
            safe_products.append(p)
        if len(safe_products) >= limit:
            break

    return safe_products

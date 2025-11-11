from sqlalchemy import case, desc, and_,  or_
from sqlalchemy.orm import Session
from typing import Sequence
from ..models.products import Products
from ..services.risk_service import evaluate_risk 


def recommend_best_in_category(db: Session, product_id: int, limit: int = 5) -> Sequence[Products]:
    """
    Gợi ý sản phẩm:
    - Cùng Category_ID
    - Không lấy sản phẩm sentiment Kém
    - Không lấy sản phẩm có RISK cao
    - Không lấy sản phẩm review quá ít (Review_Count < 3)
    - Chỉ chọn sản phẩm giá tương đương ±30%
    - Ưu tiên: Sentiment_Score > Avg_Rating > Review_Count
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

            # Không recommend sản phẩm sentiment kém
            or_(Products.Sentiment_Label != "Kém", Products.Sentiment_Label.is_(None)),

            # Không recommend sản phẩm quá ít đánh giá
            or_(Products.Review_Count >= 3, Products.Review_Count.is_(None)),

            # Giá tương đương
            and_(Products.Price >= min_price, Products.Price <= max_price),
        )
        .order_by(
            desc(case((Products.Sentiment_Score.isnot(None), 1), else_=0)),
            desc(Products.Sentiment_Score),
            desc(Products.Avg_Rating),
            desc(Products.Review_Count)
        )
        .all()
    )

    # ✅ Thêm điều kiện BACKLIST (RISK FILTER)
    safe_products = []
    for p in candidates:
        risk = evaluate_risk(p, db)
        if risk["risk_score"] < 0.6:  # chỉ lấy sản phẩm RISK thấp hoặc trung bình
            safe_products.append(p)
        if len(safe_products) >= limit:
            break

    return safe_products

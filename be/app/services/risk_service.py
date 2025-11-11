from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.products import Products

def evaluate_risk(product: Products, db: Session):
    reasons = []

    # ===== 1) So sánh giá so với trung bình cùng danh mục =====
    category_avg = db.query(func.avg(Products.Price)).filter(
        Products.Category_ID == product.Category_ID
    ).scalar()

    price_score = 0
    if category_avg and product.Price:
        price_ratio = float(product.Price) / float(category_avg)
        if price_ratio < 0.6:
            price_score = 1.0
            reasons.append("Giá thấp hơn đáng kể so với mức trung bình thị trường.")
        elif price_ratio < 0.8:
            price_score = 0.5
            reasons.append("Giá thấp hơn thị trường, cần kiểm tra kỹ.")

    # ===== 2) Cảm xúc (Sentiment) =====
    neg_ratio = 0
    if product.Positive_Percent is not None:
        neg_ratio = 1 - (product.Positive_Percent / 100)
        if neg_ratio > 0.35:
            reasons.append("Tỷ lệ đánh giá tiêu cực cao.")

    # ===== 3) Độ tin cậy (Review Count) =====
    trust_score = 0.5  # mặc định khi review ít
    if product.Review_Count and product.Review_Count >= 5:
        trust_score = (product.Positive_Percent or 0) / 100
    else:
        reasons.append("Chưa đủ đánh giá để xác thực chất lượng sản phẩm.")

    # ===== 4) Tổng hợp Risk Score =====
    risk_score = (
        price_score * 0.45 +
        neg_ratio   * 0.35 +
        (1 - trust_score) * 0.20
    )

    # ===== 5) Phân loại mức độ =====
    if risk_score < 0.3:
        level = "Thấp"
    elif risk_score < 0.6:
        level = "Trung bình"
    else:
        level = "Cao"

    return {
        "risk_score": round(risk_score, 2),
        "risk_level": level,
        "reasons": reasons
    }

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from ..models.product_view import Product_Views


def add_view_history(db: Session, user, product_id: int):
    """
    Lưu lịch sử xem chi tiết sản phẩm (chỉ khi có user).
    """
    if not user:
        return None

    existing = (
        db.query(Product_Views)
        .filter(
            Product_Views.User_ID == user.User_ID,
            Product_Views.Product_ID == product_id,
        )
        .first()
    )

    if existing:
        existing.Viewed_At = datetime.now(timezone.utc)
        db.commit()
        return existing

    view = Product_Views(User_ID=user.User_ID, Product_ID=product_id)
    db.add(view)
    db.commit()
    db.refresh(view)
    return view

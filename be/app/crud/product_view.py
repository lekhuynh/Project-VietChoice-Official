from ..models.product_view import Product_Views

def create_or_update_view(db, user_id: int, product_id: int):
    existing = db.query(Product_Views).filter_by(User_ID=user_id, Product_ID=product_id).first()
    if existing:
        import datetime
        existing.Viewed_At = datetime.now(datetime.timezone.utc)  # cập nhật thời gian xem gần nhất
    else:
        new_view = Product_Views(User_ID=user_id, Product_ID=product_id)
        db.add(new_view)
    db.commit()

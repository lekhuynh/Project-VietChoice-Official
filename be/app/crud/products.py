from typing import Optional, Sequence, Dict, Any

from sqlalchemy.orm import Session

from ..models.products import Products

from app.models.categories import Categories


def get_by_id(db: Session, product_id: int) -> Optional[Products]:
    return db.query(Products).filter(Products.Product_ID == product_id).first()


def get_by_external_id(db: Session, external_id: int) -> Optional[Products]:
    return db.query(Products).filter(Products.External_ID == external_id).first()


def list_products(db: Session, skip: int = 0, limit: int = 100) -> Sequence[Products]:
    return db.query(Products).offset(skip).limit(limit).all()


def create_product(db: Session, data: Dict[str, Any]) -> Products:
    product = Products(**data)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product: Products, data: Dict[str, Any]) -> Products:
    for k, v in data.items():
        setattr(product, k, v)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product: Products) -> None:
    db.delete(product)
    db.commit()


def get_products_by_category(db: Session, category_id: int, limit: int = 20, skip: int = 0) -> Sequence[Products]:
    """List products by category id."""
    return (
        db.query(Products)
        .filter(Products.Category_ID == category_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_top_rated_products(db: Session, limit: int = 10) -> Sequence[Products]:
    """Return top products sorted by Avg_Rating desc then Review_Count desc."""
    return (
        db.query(Products)
        .order_by(Products.Avg_Rating.desc(), Products.Review_Count.desc())
        .limit(limit)
        .all()
    )

def create_or_update_by_external_id(db: Session, data: dict):
    existing = (
        db.query(Products)
        .filter(
            Products.External_ID == data.get("External_ID"),
            Products.Source == data.get("Source", "Tiki"),
        )
        .first()
    )

    if existing:
        # ✅ Cập nhật chỉ các field hợp lệ (tránh lỗi key không tồn tại trong model)
        for key, value in data.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing

    # ✅ Nếu chưa có, tạo mới
    new_product = Products(**{k: v for k, v in data.items() if hasattr(Products, k)})
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


def update_sentiment(db: Session, external_id: int, score: Optional[float], label: Optional[str]):
    product = db.query(Products).filter(Products.External_ID == external_id).first()
    if not product:
        return None
    product.Sentiment_Score = score
    product.Sentiment_Label = label
    db.commit()
    return product

# =========================================================
# BỔ SUNG CÁC HÀM THIẾU ĐỂ ROUTES KHÔNG LỖI
# =========================================================

def get_all(db: Session):
    """Trả về toàn bộ danh sách sản phẩm."""
    return db.query(Products).all()


def get_all_tiki_products(db: Session):
    """Trả về các sản phẩm có Source = 'Tiki' và có External_ID."""
    return db.query(Products).filter(
        Products.Source == "Tiki",
        Products.External_ID.isnot(None)
    ).all()


def delete(db: Session, product_id: int) -> bool:
    """Xóa sản phẩm theo Product_ID."""
    product = db.query(Products).filter(Products.Product_ID == product_id).first()
    if not product:
        return False
    db.delete(product)
    db.commit()
    return True


def get_all_external_ids(db):
    """
    Lấy toàn bộ External_ID hiện có trong bảng Products.
    Dùng để kiểm tra trùng khi crawl dữ liệu mới từ Tiki.
    """
    result = db.query(Products.External_ID).filter(Products.External_ID.isnot(None)).all()
    # Trả về danh sách flatten [123, 456, 789]
    return [r[0] for r in result if r[0] is not None]




# def get_products_by_filter(
#     db: Session,
#     min_price=None,
#     max_price=None,
#     brand=None,
#     min_rating=None,
#     sort=None,
#     is_vietnam_origin=False,
#     is_vietnam_brand=False,
#     positive_over=None,
#     category_path=None
# ):
#     query = db.query(Products)

#     # Lọc theo khoảng giá
#     if min_price is not None and max_price is not None:
#         query = query.filter(Products.Price.between(min_price, max_price))
#     elif min_price is not None:
#         query = query.filter(Products.Price >= min_price)
#     elif max_price is not None:
#         query = query.filter(Products.Price <= max_price)

#     # Lọc theo thương hiệu
#     if brand:
#         brand_list = [b.strip() for b in brand.split(",")]
#         query = query.filter(Products.Brand.in_(brand_list))

#     # Lọc theo rating
#     if min_rating:
#         query = query.filter(Products.Avg_Rating >= min_rating)

#     # 🇻🇳 Lọc hàng Việt Nam
#     if is_vietnam_origin:
#         query = query.filter(Products.Origin.ilike("%Việt Nam%"))
#     if is_vietnam_brand:
#         query = query.filter(Products.Brand_country.ilike("%Việt Nam%"))
#     if positive_over:
#         query = query.filter(Products.Positive_Percent >= positive_over)

#     # Lọc theo danh mục (nếu có)
#     if category_path:
#         query = query.join(Categories, Products.Category_ID == Categories.Category_ID)
#         query = query.filter(Categories.Category_Path.like(f"{category_path}%"))

#     # Sắp xếp
#     if sort == "price_asc":
#         query = query.order_by(Products.Price.asc())
#     elif sort == "price_desc":
#         query = query.order_by(Products.Price.desc())
#     elif sort == "rating_desc":
#         query = query.order_by(Products.Avg_Rating.desc())

#     return query.all()



def get_products_by_category_and_filters(
    db: Session,
    lv1=None, lv2=None, lv3=None, lv4=None, lv5=None,
    min_price=None, max_price=None,
    brand=None, min_rating=None,
    sort=None,
    is_vietnam_origin=False, is_vietnam_brand=False,
    positive_over=None
):
    query = db.query(Products).join(Categories, Products.Category_ID == Categories.Category_ID)

    # --- Lọc danh mục theo cấp ---
    if lv5:
        query = query.filter(Categories.Category_Lv5 == lv5)
    elif lv4:
        query = query.filter(Categories.Category_Lv4 == lv4)
    elif lv3:
        query = query.filter(Categories.Category_Lv3 == lv3)
    elif lv2:
        query = query.filter(Categories.Category_Lv2 == lv2)
    elif lv1:
        query = query.filter(Categories.Category_Lv1 == lv1)

    # --- Lọc giá ---
    if min_price is not None:
        query = query.filter(Products.Price >= min_price)
    if max_price is not None:
        query = query.filter(Products.Price <= max_price)

    # --- Lọc thương hiệu ---
    if brand:
        brands = [b.strip() for b in brand.split(",")]
        query = query.filter(Products.Brand.in_(brands))

    # --- Lọc đánh giá ---
    if min_rating:
        query = query.filter(Products.Avg_Rating >= min_rating)

    # --- 🇻🇳 Hàng Việt Nam ---
    if is_vietnam_origin:
        query = query.filter(Products.Origin.ilike("%Việt Nam%"))
    if is_vietnam_brand:
        query = query.filter(Products.Brand_country.ilike("%Việt Nam%"))
    if positive_over:
        query = query.filter(Products.Positive_Percent >= positive_over)

    # --- Sắp xếp ---
    if sort == "price_asc":
        query = query.order_by(Products.Price.asc())
    elif sort == "price_desc":
        query = query.order_by(Products.Price.desc())
    elif sort == "rating_desc":
        query = query.order_by(Products.Avg_Rating.desc())

    return query.all()

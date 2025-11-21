from typing import Optional, Sequence, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ..models.products import Products

from app.models.categories import Categories
from app.models.search_history_products import Search_History_Products

from sqlalchemy import or_, func

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


def get_products_by_category_and_filters(
    db: Session,
    lv1=None, lv2=None, lv3=None, lv4=None, lv5=None,
    min_price=None, max_price=None,
    brand=None, min_rating=None,
    sort=None,
    skip: int = 0,
    limit: int = 20,
    is_vietnam_origin=False, is_vietnam_brand=False,
    positive_over=None,
):
    query = (
        db.query(Products)
        .join(Categories, Products.Category_ID == Categories.Category_ID)
    )

    # --- CATEGORY FILTER ---
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

    # --- PRICE ---
    if min_price is not None:
        query = query.filter(Products.Price >= min_price)
    if max_price is not None:
        query = query.filter(Products.Price <= max_price)

    # --- BRAND ---
    if brand:
        brands = [b.strip() for b in brand.split(",")]
        query = query.filter(Products.Brand.in_(brands))

    # --- RATING ---
    if min_rating is not None:
        query = query.filter(Products.Avg_Rating >= min_rating)

    # --- VIETNAM ---
    if is_vietnam_origin:
        query = query.filter(func.lower(Products.Origin).like("%việt nam%"))
    if is_vietnam_brand:
        query = query.filter(func.lower(Products.Brand_country).like("%việt nam%"))

    # --- POSITIVE ---
    if positive_over is not None:
        query = query.filter(Products.Positive_Percent >= positive_over)

    # --- AI SMART SCORE (DEFAULT SORT) ---
    score_expr = (
        (func.coalesce(Products.Sentiment_Score, 0) * 0.4)
        + (func.coalesce(Products.Avg_Rating, 0) * 0.3)
        + (func.log(func.coalesce(Products.Review_Count, 0) + 1) * 0.2)
        + (func.coalesce(Products.Positive_Percent, 0) * 0.1)
    )

    # --- SORT ---
    if not sort:
        query = query.order_by(score_expr.desc())
    else:
        if sort == "price_asc":
            query = query.order_by(Products.Price.asc())
        elif sort == "price_desc":
            query = query.order_by(Products.Price.desc())
        elif sort == "rating_desc":
            query = query.order_by(Products.Avg_Rating.desc())
        elif sort == "review_desc":
            query = query.order_by(Products.Review_Count.desc())
        elif sort == "positive_desc":
            query = query.order_by(Products.Positive_Percent.desc())
        else:
            query = query.order_by(score_expr.desc())  # fallback

    total = query.count()
    items = query.offset(skip).limit(limit).all()

    return items, total

def search_products_by_keyword_and_filters(
    db: Session,
    keyword: Optional[str] = None,
    limit: int = 20,
    skip: int = 0,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    sort: Optional[str] = None,
    is_vietnam_origin: bool = False,
    is_vietnam_brand: bool = False,
    positive_over: Optional[int] = None
):
    query = db.query(Products)

    # --- SEARCH ---
    if keyword:
        kw = f"%{keyword.lower()}%"
        query = query.filter(
            or_(
                func.lower(Products.Product_Name).like(kw),
                func.lower(Products.Brand).like(kw),
            )
        )

    # --- FILTERS ---
    if brand:
        brand_list = [b.strip() for b in brand.split(",")]
        query = query.filter(Products.Brand.in_(brand_list))

    if min_price is not None:
        query = query.filter(Products.Price >= min_price)

    if max_price is not None:
        query = query.filter(Products.Price <= max_price)

    if min_rating is not None:
        query = query.filter(Products.Avg_Rating >= min_rating)

    if is_vietnam_origin:
        query = query.filter(func.lower(Products.Origin).like("%việt nam%"))

    if is_vietnam_brand:
        query = query.filter(func.lower(Products.Brand_country).like("%việt nam%"))

    if positive_over is not None:
        query = query.filter(Products.Positive_Percent >= positive_over)

    # --- SCORE ---
    score_expr = (
        (func.coalesce(Products.Sentiment_Score, 0) * 0.4)
        + (func.coalesce(Products.Avg_Rating, 0) * 0.3)
        + (func.log(func.coalesce(Products.Review_Count, 0) + 1) * 0.2)
        + (func.coalesce(Products.Positive_Percent, 0) * 0.1)
    )

    # --- SORT ---
    if not sort:
        query = query.order_by(score_expr.desc())
    else:
        if sort == "price_asc":
            query = query.order_by(Products.Price.asc())
        elif sort == "price_desc":
            query = query.order_by(Products.Price.desc())
        elif sort == "rating_desc":
            query = query.order_by(Products.Avg_Rating.desc())
        elif sort == "review_desc":
            query = query.order_by(Products.Review_Count.desc())
        elif sort == "positive_desc":
            query = query.order_by(Products.Positive_Percent.desc())
        else:
            query = query.order_by(score_expr.desc())  # fallback

    total = query.count()
    items = query.offset(skip).limit(limit).all()

    return items, total



def get_tiki_products_older_than(db: Session, *, hours: int) -> Sequence[Products]:
    """List Tiki products whose Updated_At is older than given hours."""
    return (
        db.query(Products)
        .filter(
            Products.Source == "Tiki",
            Products.External_ID.isnot(None),
            or_(
                Products.Updated_At <= func.dateadd(func.hour, -hours, func.sysutcdatetime()),
                Products.Updated_At.is_(None),
            ),
        )
        .all()
    )


def get_outstanding_product(
    db: Session,
    *,
    limit: int = 10,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
):
    """Top sản phẩm nổi bật theo điểm AI (sentiment/rating/review/positive) + lượt tìm kiếm.

    - Luôn có order_by trước limit để tránh lỗi OFFSET/LIMIT trên MSSQL.
    - Cho phép lọc thêm theo brand và khoảng giá.
    - Bổ sung điểm cộng theo lượt tìm kiếm (search count) qua bảng Search_History_Products.
    """
    # Subquery đếm số lần sản phẩm xuất hiện trong lịch sử tìm kiếm
    search_counts_sq = (
        db.query(
            Search_History_Products.Product_ID.label("pid"),
            func.count(Search_History_Products.ID).label("search_count"),
        )
        .group_by(Search_History_Products.Product_ID)
        .subquery()
    )

    search_count = func.coalesce(search_counts_sq.c.search_count, 0)

    score_expr = (
        (func.coalesce(Products.Sentiment_Score, 0) * 0.35)
        + (func.coalesce(Products.Avg_Rating, 0) * 0.3)
        + (func.log(func.coalesce(Products.Review_Count, 0) + 1) * 0.2)
        + (func.coalesce(Products.Positive_Percent, 0) * 0.1)
        + (func.log(search_count + 1) * 0.05)  # Điểm cộng từ lượt tìm kiếm
    )

    query = db.query(Products)

    if brand:
        brands = [b.strip() for b in brand.split(",") if b.strip()]
        if brands:
            query = query.filter(Products.Brand.in_(brands))

    if min_price is not None:
        query = query.filter(Products.Price >= min_price)
    if max_price is not None:
        query = query.filter(Products.Price <= max_price)

    return (
        query
        .outerjoin(search_counts_sq, Products.Product_ID == search_counts_sq.c.pid)
        .order_by(score_expr.desc())
        .limit(limit)
        .all()
    )

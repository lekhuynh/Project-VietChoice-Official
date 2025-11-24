from typing import Any, Dict, Optional, Sequence
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func, case

from ..crud import products as product_crud
from ..models.products import Products
from ..models.categories import Categories


def get_product_detail(db: Session, product_id: int) -> Optional[Products]:
    return product_crud.get_by_id(db, product_id)


def get_products_by_category(db: Session, category_id: int, limit: int = 20, skip: int = 0) -> Sequence[Products]:
    return product_crud.get_products_by_category(db, category_id, limit=limit, skip=skip)


def list_products(db: Session, limit: int = 100, skip: int = 0) -> Sequence[Products]:
    return product_crud.list_products(db, skip=skip, limit=limit)


def update_sentiment_score_and_label(
    db: Session,
    product_id: int,
    *,
    score: Optional[float],
    label: Optional[str],
) -> Optional[Products]:
    prod = product_crud.get_by_id(db, product_id)
    if not prod:
        return None
    patch: Dict[str, Any] = {"Sentiment_Score": score, "Sentiment_Label": label}
    return product_crud.update_product(db, prod, patch)


def filter_products_service(
    db: Session,
    lv1=None,
    lv2=None,
    lv3=None,
    lv4=None,
    lv5=None,
    min_price=None,
    max_price=None,
    brand=None,
    min_rating=None,
    sort=None,
    skip: int = 0,
    limit: int = 20,
    is_vietnam_origin=False,
    is_vietnam_brand=False,
    positive_over=None,
):
    items, total = product_crud.get_products_by_category_and_filters(
        db=db,
        lv1=lv1,
        lv2=lv2,
        lv3=lv3,
        lv4=lv4,
        lv5=lv5,
        min_price=min_price,
        max_price=max_price,
        brand=brand,
        min_rating=min_rating,
        sort=sort,
        skip=skip,
        limit=limit,
        is_vietnam_origin=is_vietnam_origin,
        is_vietnam_brand=is_vietnam_brand,
        positive_over=positive_over,
    )
    return items, total


def search_products_service(
    db: Session,
    keyword: Optional[str] = None,
    limit: int = 20,
    skip: int = 0,
    lv1: Optional[str] = None,
    lv2: Optional[str] = None,
    lv3: Optional[str] = None,
    lv4: Optional[str] = None,
    lv5: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    sort: Optional[str] = None,
    is_vietnam_origin: bool = False,
    is_vietnam_brand: bool = False,
    positive_over: Optional[int] = None,
):
    items, total = product_crud.search_products_by_keyword_and_filters(
        db=db,
        keyword=keyword,
        limit=limit,
        skip=skip,
        lv1=lv1,
        lv2=lv2,
        lv3=lv3,
        lv4=lv4,
        lv5=lv5,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        sort=sort,
        is_vietnam_origin=is_vietnam_origin,
        is_vietnam_brand=is_vietnam_brand,
        positive_over=positive_over,
    )
    return items, total

"""Đây là service lấy danh sách sản phẩm nổi bật dựa trên điểm số AI và lượt tìm kiếm cho adminu"""

def get_outstanding_product_service(
    db: Session,
    limit: int = 10,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
):
    """Admin: lấy top sản phẩm nổi bật theo điểm AI + lượt tìm kiếm."""
    return product_crud.get_outstanding_product(
        db,
        limit=limit,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
    )


# ---------- Biểu đồ tỷ lệ cảm xúc theo danh mục (ADMIN) ----------
def get_sentiment_by_category(
    db: Session,
    *,
    lv1: Optional[str] = None,
    lv2: Optional[str] = None,
    lv3: Optional[str] = None,
    lv4: Optional[str] = None,
    lv5: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    group_by: str = "category",
    min_count: int = 1,
):
    """Thống kê tỷ lệ cảm xúc theo danh mục (admin analytics).

    - group_by: 'category' (Category_ID) hoặc 'lv1'...'lv5'.
    - Đếm Positive/Neutral/Negative dựa trên Sentiment_Label (case-insensitive).
    - Có thể lọc theo lv1..lv5, khoảng thời gian (from_date/to_date) dựa trên Updated_At.
    """

    # Chuẩn hóa sentiment về 3 nhãn để tổng hợp
    sentiment_lower = func.lower(func.trim(func.coalesce(Products.Sentiment_Label, "")))

    # Map both English and Vietnamese labels into unified buckets
    positive_aliases = [
        "positive", "tốt", "tot", "tích cực", "tich cuc", "tichcuc",
        "tuyệt vời", "tuyet voi", "hài lòng", "hai long",
    ]
    negative_aliases = [
        "negative", "kém", "kem", "xấu", "xau", "tệ", "te",
        "thất vọng", "that vong", "không tốt", "khong tot",
    ]

    positive_pred = sentiment_lower.in_(positive_aliases)
    negative_pred = sentiment_lower.in_(negative_aliases)

    positive_count = func.sum(case((positive_pred, 1), else_=0))
    negative_count = func.sum(case((negative_pred, 1), else_=0))
    neutral_count = func.sum(case(((~positive_pred) & (~negative_pred), 1), else_=0))

    query = db.query(
        Categories.Category_ID,
        Categories.Category_Lv1,
        Categories.Category_Lv2,
        Categories.Category_Lv3,
        Categories.Category_Lv4,
        Categories.Category_Lv5,
        func.count(Products.Product_ID).label("total_cnt"),
        positive_count.label("positive_cnt"),
        neutral_count.label("neutral_cnt"),
        negative_count.label("negative_cnt"),
    ).join(Categories, Products.Category_ID == Categories.Category_ID)

    # Filters by category levels
    if lv1:
        query = query.filter(Categories.Category_Lv1 == lv1)
    if lv2:
        query = query.filter(Categories.Category_Lv2 == lv2)
    if lv3:
        query = query.filter(Categories.Category_Lv3 == lv3)
    if lv4:
        query = query.filter(Categories.Category_Lv4 == lv4)
    if lv5:
        query = query.filter(Categories.Category_Lv5 == lv5)

    # Time filters based on Updated_At (fallback Created_At if Updated_At null)
    if from_date:
        query = query.filter(Products.Updated_At >= from_date)
    if to_date:
        query = query.filter(Products.Updated_At <= to_date)

    # Grouping columns
    group_by = (group_by or "category").lower()
    if group_by == "lv5":
        grouping = [Categories.Category_Lv1, Categories.Category_Lv2, Categories.Category_Lv3, Categories.Category_Lv4, Categories.Category_Lv5]
        label_levels = 5
    elif group_by == "lv4":
        grouping = [Categories.Category_Lv1, Categories.Category_Lv2, Categories.Category_Lv3, Categories.Category_Lv4]
        label_levels = 4
    elif group_by == "lv3":
        grouping = [Categories.Category_Lv1, Categories.Category_Lv2, Categories.Category_Lv3]
        label_levels = 3
    elif group_by == "lv2":
        grouping = [Categories.Category_Lv1, Categories.Category_Lv2]
        label_levels = 2
    elif group_by == "lv1":
        grouping = [Categories.Category_Lv1]
        label_levels = 1
    else:
        grouping = [Categories.Category_ID, Categories.Category_Lv1, Categories.Category_Lv2, Categories.Category_Lv3, Categories.Category_Lv4, Categories.Category_Lv5]
        label_levels = 5

    query = query.group_by(*grouping)

    rows = query.all()

    # Aggregate counts per group
    stats = {}
    for r in rows:
        # Build key from grouping columns
        levels = [
            getattr(r, "Category_Lv1", None),
            getattr(r, "Category_Lv2", None),
            getattr(r, "Category_Lv3", None),
            getattr(r, "Category_Lv4", None),
            getattr(r, "Category_Lv5", None),
        ]
        if group_by == "category":
            key_values = [getattr(r, "Category_ID", None)]
            label_levels_data = levels  # giữ tên danh mục để hiển thị
            key = ("category", key_values[0])
        else:
            key_values = levels[:label_levels]
            label_levels_data = key_values
            key = (group_by, tuple(key_values))

        if key not in stats:
            stats[key] = {
                "category_id": getattr(r, "Category_ID", None) if group_by == "category" else None,
                "levels": label_levels_data,
                "positive": 0,
                "neutral": 0,
                "negative": 0,
            }

        stats[key]["positive"] += r.positive_cnt or 0
        stats[key]["neutral"] += r.neutral_cnt or 0
        stats[key]["negative"] += r.negative_cnt or 0

    # Build response
    data = []
    for key, val in stats.items():
        total = val["positive"] + val["neutral"] + val["negative"]
        if total < min_count:
            continue
        levels = val["levels"]
        # label: join available levels with " > "
        label_parts = [lvl for lvl in levels if lvl]
        label = " > ".join(label_parts) if label_parts else "Unknown"
        data.append({
            "label": label,
            "category_id": val["category_id"],
            "total": total,
            "positive": val["positive"],
            "neutral": val["neutral"],
            "negative": val["negative"],
            "positive_pct": round(val["positive"] * 100.0 / total, 2) if total else 0.0,
            "neutral_pct": round(val["neutral"] * 100.0 / total, 2) if total else 0.0,
            "negative_pct": round(val["negative"] * 100.0 / total, 2) if total else 0.0,
        })

    return {
        "group_by": group_by,
        "filters": {
            "lv1": lv1, "lv2": lv2, "lv3": lv3, "lv4": lv4, "lv5": lv5,
            "from_date": from_date.isoformat() if from_date else None,
            "to_date": to_date.isoformat() if to_date else None,
            "min_count": min_count,
        },
        "data": data,
    }

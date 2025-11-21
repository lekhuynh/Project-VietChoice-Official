# Tổng hợp các thao tác quản trị hệ thống cho admin.

# Các endpoint:
# 1. GET /admin/dashboard
#    - Thống kê sản phẩm, user, đánh giá, danh mục...
#    - Requires: require_admin

# 2. GET /admin/logs
#    - Xem log hệ thống
#    - Requires: require_admin
# Có thể viết thêm các endpoint khác có trong dự án này

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from app.core.security import require_admin
#from app.services.auto_update_service import auto_update_sentiment
from ..services.product_service import (
    search_products_service,
    filter_products_service,
)
from ..models.products import Products

router = APIRouter(prefix="/admin", tags=["Admin"])

#@router.post("/auto-update-sentiment", dependencies=[Depends(require_admin)])
#def run_auto_update(db: Session = Depends(get_db)):
 #   """
  #  ⚙️ Admin endpoint: Cập nhật lại sentiment cho sản phẩm cũ hơn 24h.
   # """
    #result = auto_update_sentiment(db)
    #return result

from ..services import user_service
# ---- Ví Dụ ----
@router.get("/admin/list", dependencies=[Depends(require_admin)])
def list_all_users(db: Session = Depends(get_db)):
    return user_service.get_all_users(db)


@router.put("/admin/{user_id}/role", dependencies=[Depends(require_admin)])
def update_user_role(user_id: int, role: str, db: Session = Depends(get_db)):
    return user_service.change_user_role(db, user_id, role)


@router.delete("/admin/{user_id}", dependencies=[Depends(require_admin)])
def remove_user(user_id: int, db: Session = Depends(get_db)):
    return user_service.delete_user(db, user_id)


# ------------------------------------------------------------
# ADMIN: TRA C��C/L��C S���N PH��"M
# ------------------------------------------------------------
def _serialize_product(product: Products) -> dict:
    return {
        "Product_ID": product.Product_ID,
        "Product_Name": product.Product_Name,
        "Brand": product.Brand,
        "Image_URL": product.Image_URL,
        "Product_URL": product.Product_URL,
        "Price": float(product.Price) if product.Price is not None else None,
        "Avg_Rating": product.Avg_Rating,
        "Review_Count": product.Review_Count,
        "Positive_Percent": product.Positive_Percent,
        "Sentiment_Score": product.Sentiment_Score,
        "Sentiment_Label": product.Sentiment_Label,
        "Origin": product.Origin,
        "Brand_country": product.Brand_country,
        "Source": product.Source,
    }


@router.get("/products/search", dependencies=[Depends(require_admin)])
def admin_search_products(
    q: str,
    limit: int = Query(20, ge=1, le=50),
    skip: int = Query(0, ge=0),
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    brand: Optional[str] = None,
    min_rating: Optional[float] = None,
    sort: Optional[str] = None,
    db: Session = Depends(get_db),
):
    keyword = (q or "").strip()
    if not keyword:
        return {"total": 0, "skip": skip, "limit": limit, "count": 0, "results": []}

    items, total = search_products_service(
        db=db,
        keyword=keyword,
        limit=limit,
        skip=skip,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        sort=sort,
    )
    results = [_serialize_product(p) for p in items]
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "count": len(results),
        "results": results,
    }


@router.get("/products/by-category", dependencies=[Depends(require_admin)])
def admin_filter_products_by_category(
    lv1: Optional[str] = None,
    lv2: Optional[str] = None,
    lv3: Optional[str] = None,
    lv4: Optional[str] = None,
    lv5: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    brand: Optional[str] = None,
    min_rating: Optional[float] = None,
    sort: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    is_vietnam_origin: bool = False,
    is_vietnam_brand: bool = False,
    positive_over: Optional[int] = None,
    db: Session = Depends(get_db)
):
    items, total = filter_products_service(
        db=db,
        lv1=lv1, lv2=lv2, lv3=lv3, lv4=lv4, lv5=lv5,
        min_price=min_price, max_price=max_price,
        brand=brand, min_rating=min_rating,
        sort=sort,
        skip=skip,
        limit=limit,
        is_vietnam_origin=is_vietnam_origin,
        is_vietnam_brand=is_vietnam_brand,
        positive_over=positive_over,
    )
    results = [_serialize_product(p) for p in items]
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "count": len(results),
        "results": results,
    }

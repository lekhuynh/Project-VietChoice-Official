from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import require_admin
from app.models.products import Products

# Services
from app.services.auto_update_service import auto_update_products
from app.services.system_flag_service import (
    disable_auto_update,
    enable_auto_update,
    get_auto_update_status,
)
from app.services import user_service
from app.services.product_service import (
    search_products_service,
    filter_products_service,
    get_outstanding_product_service,
)

# =====================================================================
# ADMIN ROUTER
# =====================================================================
router = APIRouter(prefix="/admin", tags=["Admin"])


# =====================================================================
# 1) AUTO UPDATE CONTROL
# =====================================================================

@router.post("/auto-update/enable", operation_id="admin_enable_auto_update")
def admin_enable_auto_update(db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    ok = enable_auto_update(db)
    if not ok:
        raise HTTPException(status_code=500, detail="Không bật được auto-update flag.")
    return {"message": "Auto update ENABLED", "enabled": True}


@router.post("/auto-update/disable", operation_id="admin_disable_auto_update")
def admin_disable_auto_update(db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    ok = disable_auto_update(db)
    if not ok:
        raise HTTPException(status_code=500, detail="Không tắt được auto-update flag.")
    return {"message": "Auto update DISABLED", "enabled": False}


@router.get("/auto-update/status", operation_id="admin_get_auto_update_status")
def admin_auto_update_status(db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    return get_auto_update_status(db)


@router.post("/auto-update/run-now", operation_id="admin_run_auto_update_now")
def admin_run_auto_update_now(db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    stats = auto_update_products(
        db,
        older_than_hours=0,
        limit=50,
        workers=4,
    )
    return {"message": "Auto update executed manually.", "stats": stats}


# =====================================================================
# 2) USER MANAGEMENT (Admin)
# =====================================================================

@router.get("/users", operation_id="admin_list_users")
def admin_list_all_users(db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    return user_service.get_all_users(db)


@router.put("/users/{user_id}/role", operation_id="admin_update_user_role")
def admin_update_user_role(
    user_id: int,
    role: str,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    return user_service.change_user_role(db, user_id, role)


@router.delete("/users/{user_id}", operation_id="admin_delete_user")
def admin_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    return user_service.delete_user(db, user_id)


# =====================================================================
# 3) PRODUCT SEARCH (Admin)
# =====================================================================

def _serialize_product(product: Products) -> dict:
    return {
        "Product_ID": product.Product_ID,
        "Product_Name": product.Product_Name,
        "Brand": product.Brand,
        "Image_URL": product.Image_URL,
        "Product_URL": product.Product_URL,
        "Price": float(product.Price) if product.Price else None,
        "Avg_Rating": product.Avg_Rating,
        "Review_Count": product.Review_Count,
        "Positive_Percent": product.Positive_Percent,
        "Sentiment_Score": product.Sentiment_Score,
        "Sentiment_Label": product.Sentiment_Label,
        "Origin": product.Origin,
        "Brand_country": product.Brand_country,
        "Source": product.Source,
    }


@router.get("/products/search", operation_id="admin_search_products")
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
    _: dict = Depends(require_admin),
):
    items, total = search_products_service(
        db=db,
        keyword=q.strip(),
        limit=limit,
        skip=skip,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        sort=sort,
    )
    results = [_serialize_product(p) for p in items]
    return {"total": total, "count": len(results), "results": results}


# =====================================================================
# 4) FILTER PRODUCTS BY CATEGORY (Admin)
# =====================================================================

@router.get("/products/by-category", operation_id="admin_filter_products_by_category")
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
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    items, total = filter_products_service(
        db=db,
        lv1=lv1, lv2=lv2, lv3=lv3, lv4=lv4, lv5=lv5,
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
    results = [_serialize_product(p) for p in items]
    return {"total": total, "count": len(results), "results": results}


# =====================================================================
# 5) OUTSTANDING PRODUCTS
# =====================================================================

@router.get("/products/outstanding", operation_id="admin_outstanding_products")
def admin_outstanding_products(
    limit: int = Query(10, ge=1, le=50),
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin)
):
    items = get_outstanding_product_service(
        db=db,
        limit=limit,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
    )
    return {"total": len(items), "results": [_serialize_product(p) for p in items]}

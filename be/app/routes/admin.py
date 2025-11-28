from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.services.auto_update_service import auto_update_products
from app.services.system_flag_service import (
    disable_auto_update,
    enable_auto_update,
    get_auto_update_status,
)
from ..core.security import require_admin
from ..crud import products as product_crud, users as user_crud
from ..database import get_db
from ..models.products import Products
from ..schemas.products import ProductCreate, ProductUpdate
from ..schemas.users import UserCreate
from ..services import admin_service, user_service
from ..services.product_service import (
    filter_products_service,
    get_outstanding_product_service,
    get_sentiment_by_category,
    search_products_service,
)

router = APIRouter(prefix="/admin", tags=["Admin"])


# ---------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------
@router.get("/dashboard", dependencies=[Depends(require_admin)])
def get_dashboard(db: Session = Depends(get_db)):
    return admin_service.get_dashboard_stats(db)


# ---------------------------------------------------------------------
# Products CRUD
# ---------------------------------------------------------------------
@router.get("/products", dependencies=[Depends(require_admin)])
def list_products(search: Optional[str] = Query(None), db: Session = Depends(get_db)):
    products = product_crud.list_products(db, skip=0, limit=1000)
    if search:
        q = search.lower()
        products = [
            p
            for p in products
            if (p.Product_Name and q in p.Product_Name.lower()) or (p.Brand and q in p.Brand.lower())
        ]
    return [
        {
            "Product_ID": p.Product_ID,
            "Product_Name": p.Product_Name,
            "Brand": p.Brand,
            "Category_ID": p.Category_ID,
            "Price": float(p.Price) if p.Price else None,
            "Avg_Rating": float(p.Avg_Rating) if p.Avg_Rating else None,
            "Review_Count": p.Review_Count,
            "Positive_Percent": round(float(p.Positive_Percent), 1) if p.Positive_Percent else None,
            "Sentiment_Label": p.Sentiment_Label,
            "Is_Active": p.Is_Active,
            "Created_At": p.Created_At.isoformat() if p.Created_At else None,
            "Updated_At": p.Updated_At.isoformat() if p.Updated_At else None,
            "Description": p.Description,
        }
        for p in products
    ]


@router.post("/products", dependencies=[Depends(require_admin)])
def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    data = {
        "Product_Name": product_data.product_name,
        "Brand": product_data.brand,
        "Category_ID": product_data.category_id,
        "Price": product_data.price,
        "Description": product_data.description,
        "Is_Active": product_data.is_active if product_data.is_active is not None else True,
    }
    product = product_crud.create_product(db, data)
    return {
        "Product_ID": product.Product_ID,
        "Product_Name": product.Product_Name,
        "Brand": product.Brand,
        "Category_ID": product.Category_ID,
        "Price": float(product.Price) if product.Price else None,
        "Description": product.Description,
        "Is_Active": product.Is_Active,
        "Created_At": product.Created_At.isoformat() if product.Created_At else None,
        "Updated_At": product.Updated_At.isoformat() if product.Updated_At else None,
    }


@router.put("/products/{product_id}", dependencies=[Depends(require_admin)])
def update_product(product_id: int, product_data: ProductUpdate, db: Session = Depends(get_db)):
    product = product_crud.get_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_dict = {}
    if product_data.product_name is not None:
        update_dict["Product_Name"] = product_data.product_name
    if product_data.brand is not None:
        update_dict["Brand"] = product_data.brand
    if product_data.category_id is not None:
        update_dict["Category_ID"] = product_data.category_id
    if product_data.price is not None:
        update_dict["Price"] = product_data.price
    if product_data.description is not None:
        update_dict["Description"] = product_data.description
    if product_data.is_active is not None:
        update_dict["Is_Active"] = product_data.is_active

    updated = product_crud.update_product(db, product, update_dict)
    return {
        "Product_ID": updated.Product_ID,
        "Product_Name": updated.Product_Name,
        "Brand": updated.Brand,
        "Category_ID": updated.Category_ID,
        "Price": float(updated.Price) if updated.Price else None,
        "Is_Active": updated.Is_Active,
        "Updated_At": updated.Updated_At.isoformat() if updated.Updated_At else None,
    }


@router.delete("/products/{product_id}", dependencies=[Depends(require_admin)])
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = product_crud.get_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product_crud.delete_product(db, product)
    return {"message": f"Product {product_id} deleted successfully"}


# ---------------------------------------------------------------------
# Users (deduplicated)
# ---------------------------------------------------------------------
@router.get("/users", dependencies=[Depends(require_admin)])
def list_users(search: Optional[str] = Query(None), db: Session = Depends(get_db)):
    users = user_service.get_all_users(db, skip=0, limit=1000)
    if search:
        q = search.lower()
        users = [
            u
            for u in users
            if (u.User_Name and q in u.User_Name.lower())
            or (u.User_Email and q in u.User_Email.lower())
            or (u.Role and q in u.Role.lower())
        ]
    return [
        {
            "User_ID": u.User_ID,
            "User_Name": u.User_Name,
            "User_Email": u.User_Email,
            "Role": u.Role,
            "Created_At": u.Created_At.isoformat() if u.Created_At else None,
        }
        for u in users
    ]


@router.post("/users", dependencies=[Depends(require_admin)])
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    user = user_crud.create_user(
        db,
        email=user_data.email,
        name=user_data.name,
        password_plain=user_data.password,
        role=user_data.role if hasattr(user_data, "role") else "user",
    )
    return {
        "User_ID": user.User_ID,
        "User_Name": user.User_Name,
        "User_Email": user.User_Email,
        "Role": user.Role,
        "Created_At": user.Created_At.isoformat() if user.Created_At else None,
    }


@router.put("/users/{user_id}", dependencies=[Depends(require_admin)])
def update_user(user_id: int, user_data: dict, db: Session = Depends(get_db)):
    updated = user_service.admin_update_user(
        db,
        user_id,
        {
            "name": user_data.get("User_Name"),
            "email": user_data.get("User_Email"),
            "role": user_data.get("Role"),
        },
    )
    return {
        "User_ID": updated.User_ID,
        "User_Name": updated.User_Name,
        "User_Email": updated.User_Email,
        "Role": updated.Role,
    }


@router.put("/users/{user_id}/role", dependencies=[Depends(require_admin)])
def update_user_role(user_id: int, role: str, db: Session = Depends(get_db)):
    return user_service.change_user_role(db, user_id, role)


@router.delete("/users/{user_id}", dependencies=[Depends(require_admin)])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    return user_service.delete_user(db, user_id)


# ---------------------------------------------------------------------
# Auto update flags
# ---------------------------------------------------------------------
@router.post("/auto-update/enable", dependencies=[Depends(require_admin)])
def admin_enable_auto_update(db: Session = Depends(get_db)):
    ok = enable_auto_update(db)
    if not ok:
        raise HTTPException(status_code=500, detail="Không bật được auto-update flag.")
    return {"message": "Auto update ENABLED", "enabled": True}


@router.post("/auto-update/disable", dependencies=[Depends(require_admin)])
def admin_disable_auto_update(db: Session = Depends(get_db)):
    ok = disable_auto_update(db)
    if not ok:
        raise HTTPException(status_code=500, detail="Không tắt được auto-update flag.")
    return {"message": "Auto update DISABLED", "enabled": False}


@router.get("/auto-update/status", dependencies=[Depends(require_admin)])
def admin_auto_update_status(db: Session = Depends(get_db)):
    return get_auto_update_status(db)


@router.post("/auto-update/run-now", dependencies=[Depends(require_admin)])
def admin_run_auto_update_now(db: Session = Depends(get_db)):
    stats = auto_update_products(
        db,
        older_than_hours=0,
        limit=None,
        workers=10,
    )
    return {"message": "Auto update executed manually.", "stats": stats}


# ---------------------------------------------------------------------
# Product search/filter (admin)
# ---------------------------------------------------------------------
def _serialize_product(product: Products) -> dict:
    return {
        "Product_ID": product.Product_ID,
        "Product_Name": product.Product_Name,
        "Brand": product.Brand,
        "Category_ID": product.Category_ID,
        "Price": float(product.Price) if product.Price else None,
        "Is_Active": product.Is_Active,
        "Created_At": product.Created_At.isoformat() if product.Created_At else None,
    }


@router.get("/products/search", dependencies=[Depends(require_admin)], operation_id="admin_search_products")
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


@router.get("/products/by-category", dependencies=[Depends(require_admin)], operation_id="admin_filter_products_by_category")
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
):
    items, total = filter_products_service(
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
    results = [_serialize_product(p) for p in items]
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "count": len(results),
        "results": results,
    }


@router.get("/products/outstanding", dependencies=[Depends(require_admin)], operation_id="admin_outstanding_products")
def admin_outstanding_products(
    limit: int = Query(10, ge=1, le=50),
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    db: Session = Depends(get_db),
):
    items = get_outstanding_product_service(
        db=db,
        limit=limit,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
    )
    results = [_serialize_product(p) for p in items]
    return {"total": len(results), "results": results}


# ---------------------------------------------------------------------
# Analytics & featured
# ---------------------------------------------------------------------
@router.get("/analytics/sentiment-by-category", dependencies=[Depends(require_admin)], operation_id="admin_analytics_sentiment_by_category")
def analytics_sentiment_by_category(
    group_by: str = Query("category", regex="^(category|lv1|lv2|lv3|lv4|lv5)$"),
    lv1: Optional[str] = None,
    lv2: Optional[str] = None,
    lv3: Optional[str] = None,
    lv4: Optional[str] = None,
    lv5: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    min_count: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    def _parse_dt(val: Optional[str]) -> Optional[datetime]:
        if not val:
            return None
        try:
            return datetime.fromisoformat(val)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format: {val}. Use ISO format YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS",
            )

    from_dt = _parse_dt(from_date)
    to_dt = _parse_dt(to_date)

    return get_sentiment_by_category(
        db=db,
        lv1=lv1,
        lv2=lv2,
        lv3=lv3,
        lv4=lv4,
        lv5=lv5,
        from_date=from_dt,
        to_date=to_dt,
        group_by=group_by,
        min_count=min_count,
    )


@router.get("/charts/sentiment", dependencies=[Depends(require_admin)])
def get_sentiment_chart(db: Session = Depends(get_db)):
    return admin_service.get_sentiment_chart_data(db)


@router.get("/charts/trends", dependencies=[Depends(require_admin)])
def get_trend_chart(db: Session = Depends(get_db)):
    return admin_service.get_trend_data(db)


@router.get("/featured-products", dependencies=[Depends(require_admin)])
def get_featured_products(db: Session = Depends(get_db)):
    return admin_service.get_featured_products(db)


# ---------------------------------------------------------------------
# Activity logs placeholder
# ---------------------------------------------------------------------
@router.get("/logs", dependencies=[Depends(require_admin)])
def get_logs(db: Session = Depends(get_db)):
    return []

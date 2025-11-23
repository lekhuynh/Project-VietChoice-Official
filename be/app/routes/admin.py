# Tổng hợp các thao tác quản trị hệ thống cho admin.

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..core.security import require_admin
from ..services.auto_update_service import auto_update_sentiment
from ..services import admin_service, user_service, product_service
from ..crud import products as product_crud, users as user_crud
from ..schemas.products import ProductCreate, ProductUpdate
from ..schemas.users import UserCreate
from ..models.products import Products
from ..models.users import Users

router = APIRouter(prefix="/admin", tags=["Admin"])


# ============================================================
# DASHBOARD
# ============================================================
@router.get("/dashboard", dependencies=[Depends(require_admin)])
def get_dashboard(db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    return admin_service.get_dashboard_stats(db)


# ============================================================
# PRODUCTS CRUD
# ============================================================
@router.get("/products", dependencies=[Depends(require_admin)])
def list_products(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List all products with optional search."""
    products = product_crud.list_products(db, skip=0, limit=1000)
    
    if search:
        search_lower = search.lower()
        products = [
            p for p in products
            if (p.Product_Name and search_lower in p.Product_Name.lower())
            or (p.Brand and search_lower in p.Brand.lower())
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
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db)
):
    """Create a new product."""
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
        "Is_Active": product.Is_Active,
        "Created_At": product.Created_At.isoformat() if product.Created_At else None,
    }


@router.put("/products/{product_id}", dependencies=[Depends(require_admin)])
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db)
):
    """Update a product."""
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
def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Delete a product."""
    product = product_crud.get_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product_crud.delete_product(db, product)
    return {"message": f"Product {product_id} deleted successfully"}


# ============================================================
# USERS CRUD
# ============================================================
@router.get("/users", dependencies=[Depends(require_admin)])
def list_users(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List all users with optional search."""
    users = user_service.get_all_users(db, skip=0, limit=1000)
    
    if search:
        search_lower = search.lower()
        users = [
            u for u in users
            if (u.User_Name and search_lower in u.User_Name.lower())
            or (u.User_Email and search_lower in u.User_Email.lower())
            or (u.Role and search_lower in u.Role.lower())
        ]
    
    return [
        {
            "User_ID": u.User_ID,
            "User_Name": u.User_Name,
            "User_Email": u.User_Email,
            "Role": u.Role,
            "Created_At": u.Created_At.isoformat() if u.Created_At else None,
            "lastActive": None,  # TODO: Implement last active tracking
        }
        for u in users
    ]


@router.post("/users", dependencies=[Depends(require_admin)])
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new user."""
    user = user_crud.create_user(
        db,
        email=user_data.email,
        name=user_data.name,
        password_plain=user_data.password,
        role=user_data.role if hasattr(user_data, 'role') else "user"
    )
    return {
        "User_ID": user.User_ID,
        "User_Name": user.User_Name,
        "User_Email": user.User_Email,
        "Role": user.Role,
        "Created_At": user.Created_At.isoformat() if user.Created_At else None,
    }


@router.put("/users/{user_id}", dependencies=[Depends(require_admin)])
def update_user(
    user_id: int,
    user_data: dict,
    db: Session = Depends(get_db)
):
    """Update a user."""
    updated = user_service.admin_update_user(
        db,
        user_id,
        {
            "name": user_data.get("User_Name"),
            "email": user_data.get("User_Email"),
            "role": user_data.get("Role"),
        }
    )
    return {
        "User_ID": updated.User_ID,
        "User_Name": updated.User_Name,
        "User_Email": updated.User_Email,
        "Role": updated.Role,
    }


@router.delete("/users/{user_id}", dependencies=[Depends(require_admin)])
def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Delete a user."""
    return user_service.delete_user(db, user_id)


# ============================================================
# ACTIVITY LOGS
# ============================================================
@router.get("/logs", dependencies=[Depends(require_admin)])
def get_logs(db: Session = Depends(get_db)):
    """Get activity logs (simplified - can be enhanced with actual logging system)."""
    # For now, return empty array or basic activity
    # TODO: Implement proper activity logging
    return []


# ============================================================
# CHARTS & ANALYTICS
# ============================================================
@router.get("/charts/sentiment", dependencies=[Depends(require_admin)])
def get_sentiment_chart(db: Session = Depends(get_db)):
    """Get sentiment chart data by category."""
    return admin_service.get_sentiment_chart_data(db)


@router.get("/charts/trends", dependencies=[Depends(require_admin)])
def get_trend_chart(db: Session = Depends(get_db)):
    """Get trend chart data."""
    return admin_service.get_trend_data(db)


@router.get("/featured-products", dependencies=[Depends(require_admin)])
def get_featured_products(db: Session = Depends(get_db)):
    """Get featured products."""
    return admin_service.get_featured_products(db)


# ============================================================
# AUTO UPDATE
# ============================================================
@router.post("/auto-update-sentiment", dependencies=[Depends(require_admin)])
def run_auto_update(db: Session = Depends(get_db)):
    """
    ⚙️ Admin endpoint: Cập nhật lại sentiment cho sản phẩm cũ hơn 24h.
    """
    result = auto_update_sentiment(db)
    return result

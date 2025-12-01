from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.favorite_service import (
    add_favorite,
    get_user_favorites_with_products,
    remove_favorite,
    remove_all_favorites
)
from app.core.security import get_optional_user

router = APIRouter(prefix="/favorite", tags=["Favorites"])

# ============================================================
# 1️⃣ THÊM SẢN PHẨM YÊU THÍCH
# ============================================================
@router.post("/add/{product_id}")
def add_favorite_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user)
):
    """
    Thêm sản phẩm vào danh sách yêu thích của user hiện tại.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    favorite = add_favorite(db, user_id=current_user.User_ID, product_id=product_id)
    return {"message": "Product added to favorites", "favorite": favorite}


# ============================================================
# 2️⃣ LẤY DANH SÁCH SẢN PHẨM YÊU THÍCH
# ============================================================
@router.get("/list")
def get_favorite_products(
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user)
):
    """
    Lấy danh sách sản phẩm yêu thích của user hiện tại.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    favorites = get_user_favorites_with_products(db, user_id=current_user.User_ID)
    return {"user_id": current_user.User_ID, "favorites": favorites}


# ============================================================
# 3️⃣ XOÁ SẢN PHẨM KHỎI DANH SÁCH YÊU THÍCH
# ============================================================
@router.delete("/remove/{product_id}")
def remove_favorite_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user)
):
    """
    Xoá sản phẩm khỏi danh sách yêu thích của user hiện tại.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    deleted = remove_favorite(db, user_id=current_user.User_ID, product_id=product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found in favorites")

    return {"message": "Product removed from favorites"}

# ============================================================
# 4️⃣ XOÁ TOÀN BỘ DANH SÁCH YÊU THÍCH
# ============================================================
@router.delete("/remove_all")
def remove_all_favorite_products(
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user)
):
    """
    Xoá toàn bộ danh sách yêu thích của user hiện tại.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    deleted_count = remove_all_favorites(db, user_id=current_user.User_ID)
    return {
        "message": f"Deleted {deleted_count} favorite items",
        "user_id": current_user.User_ID
    }

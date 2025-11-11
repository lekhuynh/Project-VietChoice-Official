from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..crud import search_history as history_crud
from ..models.product_view import Product_Views
from ..models.products import Products
from ..core.security import get_optional_user, get_current_user

router = APIRouter(prefix="/users", tags=["User History"])

# ======================================================
# 1️⃣ LỊCH SỬ TÌM KIẾM
# ======================================================
@router.get("/search")
def get_my_search_history(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Lấy lịch sử tìm kiếm của user đang đăng nhập.
    """
    user_id = current_user.User_ID
    histories = history_crud.list_by_user(db, user_id)

    if not histories:
        return {"user_id": user_id, "history": []}

    result = []
    for h in histories:
        linked_products = history_crud.get_history_results(db, h.History_ID)
        result.append({
            "History_ID": h.History_ID,
            "Query": h.Query,
            "Result_Count": h.Result_Count,
            "Created_At": h.Created_At,
            "Products": [
                {
                    "Product_ID": p.Product_ID,
                    "Product_Name": p.Product_Name,
                    "Image_URL": p.Image_URL,
                    "Price": p.Price,
                    "Avg_Rating": p.Avg_Rating,
                } for p in linked_products
            ]
        })
    return {"user_id": user_id, "history": result}


# ======================================================
# 2️⃣ LỊCH SỬ ĐÃ XEM
# ======================================================
@router.get("/viewed")
def get_my_view_history(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Lấy lịch sử sản phẩm đã xem chi tiết (của user hiện tại).
    """
    user_id = current_user.User_ID
    views = (
        db.query(Product_Views, Products)
        .join(Products, Product_Views.Product_ID == Products.Product_ID)
        .filter(Product_Views.User_ID == user_id)
        .order_by(Product_Views.Viewed_At.desc())
        .all()
    )

    if not views:
        return {"user_id": user_id, "viewed": []}

    result = []
    for v, p in views:
        result.append({
            "Viewed_At": v.Viewed_At,
            "Product_ID": p.Product_ID,
            "Product_Name": p.Product_Name,
            "Image_URL": p.Image_URL,
            "Price": p.Price,
            "Avg_Rating": p.Avg_Rating,
        })

    return {"user_id": user_id, "viewed": result}


# ======================================================
# 3️⃣ XOÁ TOÀN BỘ HOẶC 1 LỊCH SỬ TÌM KIẾM
# ======================================================
@router.delete("/delete/search/{history_id:int}")
def delete_search_history(history_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Xoá 1 lịch sử tìm kiếm cụ thể (theo History_ID).
    """
    history = history_crud.get_by_id(db, history_id)
    if not history or history.User_ID != current_user.User_ID:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch sử tìm kiếm này")
    db.delete(history)
    db.commit()
    return {"message": f"Đã xoá lịch sử tìm kiếm ID {history_id}"}


@router.delete("/delete/search")
def delete_all_search_history(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Xoá toàn bộ lịch sử tìm kiếm của user hiện tại.
    """
    history_crud.delete_all_by_user(db, current_user.User_ID)
    return {"message": "Đã xoá tất cả lịch sử tìm kiếm"}


# ======================================================
# 4️⃣ XOÁ LỊCH SỬ SẢN PHẨM ĐÃ XEM
# ======================================================
@router.delete("/delete/viewed/{product_id:int}")
def delete_view_history_item(product_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Xoá 1 sản phẩm trong lịch sử đã xem.
    """
    view = db.query(Product_Views).filter(
        Product_Views.Product_ID == product_id,
        Product_Views.User_ID == current_user.User_ID
    ).first()
    if not view:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch sử xem sản phẩm này")
    db.delete(view)
    db.commit()
    return {"message": f"Đã xoá sản phẩm ID {product_id} khỏi lịch sử xem"}


@router.delete("/delete/viewed")
def delete_all_view_history(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Xoá toàn bộ lịch sử xem sản phẩm của user hiện tại.
    """
    db.query(Product_Views).filter(Product_Views.User_ID == current_user.User_ID).delete()
    db.commit()
    return {"message": "Đã xoá tất cả lịch sử xem sản phẩm"}

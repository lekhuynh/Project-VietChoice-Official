from datetime import timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.security import get_current_user, get_optional_user
from ..crud import search_history as history_crud
from ..database import get_db
from ..models.product_view import Product_Views
from ..models.products import Products

router = APIRouter(prefix="/users", tags=["User History"])

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def _to_vn(dt):
    """
    Convert datetime to Vietnam timezone.
    - If naive: treat as already Vietnam local and attach tzinfo.
    - If aware: convert to Vietnam timezone.
    """
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=VN_TZ)
    else:
        dt = dt.astimezone(VN_TZ)
    return dt.isoformat()


# ======================================================
# 1) LỊCH SỬ TÌM KIẾM
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
            "Created_At": _to_vn(h.Created_At),
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
# 2) LỊCH SỬ ĐÃ XEM
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
            "Viewed_At": _to_vn(v.Viewed_At),
            "Product_ID": p.Product_ID,
            "Product_Name": p.Product_Name,
            "Image_URL": p.Image_URL,
            "Price": p.Price,
            "Avg_Rating": p.Avg_Rating,
        })

    return {"user_id": user_id, "viewed": result}


# ======================================================
# 3) XÓA TOÀN BỘ HOẶC 1 LỊCH SỬ TÌM KIẾM
# ======================================================
@router.delete("/delete/search/{history_id:int}")
def delete_search_history(history_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Xóa 1 lịch sử tìm kiếm cụ thể (theo History_ID).
    """
    history = history_crud.get_by_id(db, history_id)
    if not history or history.User_ID != current_user.User_ID:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch sử tìm kiếm này")
    db.delete(history)
    db.commit()
    return {"message": f"Đã xóa lịch sử tìm kiếm ID {history_id}"}


@router.delete("/delete/search")
def delete_all_search_history(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Xóa toàn bộ lịch sử tìm kiếm của user hiện tại.
    """
    history_crud.delete_all_by_user(db, current_user.User_ID)
    return {"message": "Đã xóa tất cả lịch sử tìm kiếm"}


# ======================================================
# 4) XÓA LỊCH SỬ SẢN PHẨM ĐÃ XEM
# ======================================================
@router.delete("/delete/viewed/{product_id:int}")
def delete_view_history_item(product_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Xóa 1 sản phẩm trong lịch sử đã xem.
    """
    view = db.query(Product_Views).filter(
        Product_Views.Product_ID == product_id,
        Product_Views.User_ID == current_user.User_ID
    ).first()
    if not view:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch sử xem sản phẩm này")
    db.delete(view)
    db.commit()
    return {"message": f"Đã xóa sản phẩm ID {product_id} khỏi lịch sử xem"}


@router.delete("/delete/viewed")
def delete_all_view_history(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Xóa toàn bộ lịch sử xem sản phẩm của user hiện tại.
    """
    db.query(Product_Views).filter(Product_Views.User_ID == current_user.User_ID).delete()
    db.commit()
    return {"message": "Đã xóa tất cả lịch sử xem sản phẩm"}

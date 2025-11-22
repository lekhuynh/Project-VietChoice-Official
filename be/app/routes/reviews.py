from datetime import timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.crud import user_reviews as review_crud

router = APIRouter(prefix="/reviews", tags=["Reviews"])
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

def _to_vn(dt):
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.astimezone(VN_TZ)

# ============================
# 1️⃣ CREATE REVIEW
# ============================
@router.post("/")
def create_review(data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    product_id = data.get("product_id")
    rating     = data.get("rating")
    comment    = data.get("comment")
    try:
        if not product_id or not rating:
            raise HTTPException(400, "Thiếu product_id hoặc rating")

        review = review_crud.create_review(
            db,
            user_id=current_user.User_ID,
            product_id=product_id,
            rating=rating,
            comment=comment
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    return {
        "review_id": review.Review_ID,
        "user_id": review.User_ID,
        "product_id": review.Product_ID,
        "rating": review.Rating,
        "comment": review.Comment,
        "created_at": _to_vn(review.Created_At).isoformat() if review.Created_At else None,
        "message": "Đánh giá đã được tạo"
    }

# ============================
# 2️⃣ GET REVIEWS BY PRODUCT
# ============================
@router.get("/product/{product_id}")
def get_reviews_by_product(product_id: int, db: Session = Depends(get_db)):
    reviews = review_crud.list_by_product(db, product_id)
    return [
        {
            "review_id": r.Review_ID,
            "user_id": r.User_ID,
            "product_id": r.Product_ID,
            "rating": r.Rating,
            "comment": r.Comment,
            "created_at": _to_vn(r.Created_At).isoformat() if r.Created_At else None
        }
        for r in reviews
    ]

# ============================
# 3️⃣ GET REVIEWS BY USER
# ============================
@router.get("/user")
def get_reviews_by_user(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    reviews = review_crud.list_by_user(db, current_user.User_ID)
    return [
        {
            "review_id": r.Review_ID,
            "user_id": r.User_ID,
            "product_id": r.Product_ID,
            "rating": r.Rating,
            "comment": r.Comment,
            "created_at": _to_vn(r.Created_At).isoformat() if r.Created_At else None
        }
        for r in reviews
    ]

# ============================
# 4️⃣ UPDATE REVIEW
# ============================
@router.put("/{review_id}")
def update_review(review_id: int, data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    review = review_crud.get_by_id(db, review_id)
    if not review:
        raise HTTPException(404, "Không tìm thấy review")
    if review.User_ID != current_user.User_ID:
        raise HTTPException(403, "Không có quyền sửa review này")

    updated = review_crud.update_review(
        db,
        review,
        rating=data.get("rating"),
        comment=data.get("comment")
    )

    return {
        "review_id": updated.Review_ID,
        "user_id": updated.User_ID,
        "product_id": updated.Product_ID,
        "rating": updated.Rating,
        "comment": updated.Comment,
        "created_at": _to_vn(updated.Created_At).isoformat() if updated.Created_At else None,
        "message": "Đã cập nhật đánh giá"
    }

# ============================
# 5️⃣ DELETE REVIEW
# ============================
@router.delete("/{review_id}")
def delete_review(review_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    review = review_crud.get_by_id(db, review_id)
    if not review:
        raise HTTPException(404, "Không tìm thấy review")
    if review.User_ID != current_user.User_ID:
        raise HTTPException(403, "Không có quyền xóa review này")

    review_crud.delete_review(db, review)

    return {
        "review_id": review_id,
        "message": "Đã xóa đánh giá"
    }
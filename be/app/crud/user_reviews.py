from typing import Optional, Sequence

from sqlalchemy.orm import Session

from ..models.user_reviews import User_Reviews


def get_by_id(db: Session, review_id: int) -> Optional[User_Reviews]:
    return db.query(User_Reviews).filter(User_Reviews.Review_ID == review_id).first()


def list_by_product(db: Session, product_id: int, skip: int = 0, limit: int = 100) -> Sequence[User_Reviews]:
    return (
        db.query(User_Reviews)
        .filter(User_Reviews.Product_ID == product_id)
        .order_by(User_Reviews.Created_At.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def list_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> Sequence[User_Reviews]:
    return (
        db.query(User_Reviews)
        .filter(User_Reviews.User_ID == user_id)
        .order_by(User_Reviews.Created_At.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


from sqlalchemy.exc import IntegrityError

def create_review(db: Session, *, user_id: int, product_id: int, rating: int, comment: str | None = None):
    review = User_Reviews(User_ID=user_id, Product_ID=product_id, Rating=rating, Comment=comment)
    db.add(review)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("User đã review sản phẩm này rồi. Vui lòng cập nhật thay vì tạo mới.")
    db.refresh(review)
    return review



def update_review(db: Session, review: User_Reviews, *, rating: Optional[int] = None, comment: Optional[str] = None) -> User_Reviews:
    if rating is not None:
        review.Rating = rating
    if comment is not None:
        review.Comment = comment
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def delete_review(db: Session, review: User_Reviews) -> None:
    db.delete(review)
    db.commit()

def get_average_rating(db: Session, product_id: int) -> float | None:
    """Return average rating for a product, or None if no reviews."""
    from sqlalchemy import func

    row = db.query(func.avg(User_Reviews.Rating)).filter(User_Reviews.Product_ID == product_id).first()
    return float(row[0]) if row and row[0] is not None else None


def get_top_rated_products(db: Session, limit: int = 10):
    """Return (Product_ID, avg_rating, review_count) sorted by avg_rating desc then count desc."""
    from sqlalchemy import func

    rows = (
        db.query(
            User_Reviews.Product_ID,
            func.avg(User_Reviews.Rating).label("avg_rating"),
            func.count(User_Reviews.Review_ID).label("cnt"),
        )
        .group_by(User_Reviews.Product_ID)
        .order_by(func.avg(User_Reviews.Rating).desc(), func.count(User_Reviews.Review_ID).desc())
        .limit(limit)
        .all()
    )
    return [(r[0], float(r[1]), int(r[2])) for r in rows]

def get_user_product_review(db: Session, user_id: int, product_id: int):
    return (
        db.query(User_Reviews)
        .filter(
            User_Reviews.User_ID == user_id,
            User_Reviews.Product_ID == product_id
        )
        .first()
    )

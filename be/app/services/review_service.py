from typing import Optional, Sequence

from sqlalchemy.orm import Session

from ..crud import user_reviews as reviews_crud
from ..models.user_reviews import User_Reviews
from ..models.products import Products


def _refresh_avg_rating(db: Session, product_id: int) -> Optional[float]:
    avg = reviews_crud.get_average_rating(db, product_id)
    prod = db.query(Products).filter(Products.Product_ID == product_id).first()
    if not prod:
        return avg
    prod.Avg_Rating = avg if avg is not None else None
    db.add(prod)
    db.commit()
    return avg


def add_review(db: Session, user_id: int, product_id: int, rating: int, comment: str | None = None) -> User_Reviews:
    review = reviews_crud.create_review(db, user_id=user_id, product_id=product_id, rating=rating, comment=comment)
    _refresh_avg_rating(db, product_id)
    return review


def get_reviews_by_product(db: Session, product_id: int, skip: int = 0, limit: int = 100) -> Sequence[User_Reviews]:
    return reviews_crud.list_by_product(db, product_id, skip=skip, limit=limit)


def get_reviews_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> Sequence[User_Reviews]:
    return reviews_crud.list_by_user(db, user_id, skip=skip, limit=limit)


def delete_review(db: Session, review_id: int) -> bool:
    review = reviews_crud.get_by_id(db, review_id)
    if not review:
        return False
    pid = review.Product_ID
    reviews_crud.delete_review(db, review)
    _refresh_avg_rating(db, pid)
    return True

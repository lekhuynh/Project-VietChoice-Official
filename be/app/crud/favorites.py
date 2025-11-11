from typing import Optional, Sequence

from sqlalchemy.orm import Session

from ..models.favorites import Favorites


def exists(db: Session, *, user_id: int, product_id: int) -> bool:
    return (
        db.query(Favorites)
        .filter(Favorites.User_ID == user_id, Favorites.Product_ID == product_id)
        .first()
        is not None
    )


def add(db: Session, *, user_id: int, product_id: int) -> Favorites:
    fav = Favorites(User_ID=user_id, Product_ID=product_id)
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return fav


def remove(db: Session, *, user_id: int, product_id: int) -> int:
    q = db.query(Favorites).filter(Favorites.User_ID == user_id, Favorites.Product_ID == product_id)
    count = q.count()
    q.delete(synchronize_session=False)
    db.commit()
    return count


def list_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> Sequence[Favorites]:
    return (
        db.query(Favorites)
        .filter(Favorites.User_ID == user_id)
        .order_by(Favorites.Created_At.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_most_favorited_products(db: Session, limit: int = 10):
    """Return list of (Product_ID, favorites_count) sorted by count desc."""
    from sqlalchemy import func

    rows = (
        db.query(Favorites.Product_ID, func.count(Favorites.Product_ID).label("cnt"))
        .group_by(Favorites.Product_ID)
        .order_by(func.count(Favorites.Product_ID).desc())
        .limit(limit)
        .all()
    )
    return [(r[0], r[1]) for r in rows]

def remove_all(db: Session, user_id: int) -> int:
    """
    Xóa tất cả sản phẩm yêu thích của user.
    """
    deleted = db.query(Favorites).filter(Favorites.User_ID == user_id).delete()
    db.commit()
    return deleted
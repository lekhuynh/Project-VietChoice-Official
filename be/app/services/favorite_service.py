from typing import Sequence

from sqlalchemy.orm import Session

from ..crud import favorites as fav_crud
from ..models.favorites import Favorites


def add_favorite(db: Session, user_id: int, product_id: int) -> Favorites:
    if fav_crud.exists(db, user_id=user_id, product_id=product_id):
        existing = fav_crud.list_by_user(db, user_id, limit=1)
        return existing[0] if existing else fav_crud.add(db, user_id=user_id, product_id=product_id)
    return fav_crud.add(db, user_id=user_id, product_id=product_id)


def remove_favorite(db: Session, user_id: int, product_id: int) -> int:
    return fav_crud.remove(db, user_id=user_id, product_id=product_id)


def get_user_favorites(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> Sequence[Favorites]:
    return fav_crud.list_by_user(db, user_id, skip=skip, limit=limit)


def remove_all_favorites(db: Session, user_id: int) -> int:
    """XA3a toA�n b��T danh sA�ch yA�u thA-ch c��a user. Tr��� v��? s��` b���n ghi �`A� xA3a."""
    from ..crud import favorites as fav_crud
    return fav_crud.remove_all(db, user_id=user_id)

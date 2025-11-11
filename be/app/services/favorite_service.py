from typing import Sequence

from sqlalchemy.orm import Session

from ..crud import favorites as fav_crud
from ..models.favorites import Favorites


def add_favorite(db: Session, user_id: int, product_id: int) -> Favorites:
    if fav_crud.exists(db, user_id=user_id, product_id=product_id):
        # Return existing-like object by adding then fetching list head to keep it simple
        # but better to query the exact record
        favs = fav_crud.list_by_user(db, user_id, limit=1)
        return favs[0] if favs else fav_crud.add(db, user_id=user_id, product_id=product_id)
    return fav_crud.add(db, user_id=user_id, product_id=product_id)


def remove_favorite(db: Session, user_id: int, product_id: int) -> int:
    return fav_crud.remove(db, user_id=user_id, product_id=product_id)


def get_user_favorites(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> Sequence[Favorites]:
    return fav_crud.list_by_user(db, user_id, skip=skip, limit=limit)


def is_favorited(db: Session, user_id: int, product_id: int) -> bool:
    return fav_crud.exists(db, user_id=user_id, product_id=product_id)

def remove_all_favorites(db: Session, user_id: int) -> int:
    """
    Xóa toàn bộ danh sách yêu thích của user.
    Trả về số bản ghi đã xóa.
    """
    from ..crud import favorites as fav_crud
    return fav_crud.remove_all(db, user_id=user_id)
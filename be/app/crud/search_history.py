from typing import Optional, Sequence

from sqlalchemy.orm import Session

from ..models.search_history import Search_History

from ..models.product_view import Product_Views

def get_by_id(db: Session, history_id: int) -> Optional[Search_History]:
    return db.query(Search_History).filter(Search_History.History_ID == history_id).first()


def list_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> Sequence[Search_History]:
    return (
        db.query(Search_History)
        .filter(Search_History.User_ID == user_id)
        .order_by(Search_History.Created_At.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_history(db: Session, *, user_id: int, query: str, result_count: int = 0) -> Search_History:
    history = Search_History(User_ID=user_id, Query=query, Result_Count=result_count)
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


def link_history_to_products(db: Session, *, history_id: int, product_ids: list[int]) -> int:
    """Bulk link a history to product ids; returns number of links created."""
    from ..models.search_history_products import Search_History_Products

    created = 0
    for pid in product_ids:
        link = Search_History_Products(History_ID=history_id, Product_ID=pid)
        db.add(link)
        created += 1
    db.commit()
    return created


def get_history_results(db: Session, history_id: int):
    """Return list of Products associated with a search history."""
    from ..models.search_history_products import Search_History_Products
    from ..models.products import Products

    return (
        db.query(Products)
        .join(Search_History_Products, Search_History_Products.Product_ID == Products.Product_ID)
        .filter(Search_History_Products.History_ID == history_id)
        .all()
    )


def clear_user_history(db: Session, user_id: int) -> int:
    """Delete all search history records for a user. Returns deleted count."""
    q = db.query(Search_History).filter(Search_History.User_ID == user_id)
    count = q.count()
    q.delete(synchronize_session=False)
    db.commit()
    return count

def delete_all_by_user(db: Session, user_id: int):
    count = db.query(Search_History).filter(Search_History.User_ID == user_id).delete()
    db.commit()
    return count

def search_products(db: Session, query_text: str, limit: int = 50):
    """Simple text search over Products name or exact barcode match."""
    from sqlalchemy import or_
    from ..models.products import Products

    q = (
        db.query(Products)
        .filter(
            or_(
                Products.Product_Name.ilike(f"%{query_text}%"),
                Products.Barcode == query_text,
            )
        )
        .limit(limit)
    )
    return q.all()

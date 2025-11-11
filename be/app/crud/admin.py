from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.users import Users
from ..models.products import Products
from ..models.search_history import Search_History
from ..models.search_history_products import Search_History_Products
from ..models.favorites import Favorites
from ..models.user_reviews import User_Reviews


def get_user_statistics(db: Session, active_days: int = 30) -> Dict[str, int]:
    """Return basic user stats: total and active within N days."""
    total = db.query(func.count(Users.User_ID)).scalar() or 0
    since = datetime.utcnow() - timedelta(days=active_days)
    # Active = users having at least one search since 'since'
    active = (
        db.query(func.count(func.distinct(Search_History.User_ID)))
        .filter(Search_History.Created_At >= since)
        .scalar()
        or 0
    )
    return {"total_users": int(total), "active_users": int(active)}


def get_product_statistics(db: Session) -> Dict[str, object]:
    """Return product stats including totals and counts by category."""
    total = db.query(func.count(Products.Product_ID)).scalar() or 0
    by_category = (
        db.query(Products.Category_ID, func.count(Products.Product_ID))
        .group_by(Products.Category_ID)
        .all()
    )
    by_category_list = [(int(cid), int(cnt)) for cid, cnt in by_category if cid is not None]
    return {"total_products": int(total), "by_category": by_category_list}


def get_search_trends(db: Session, limit: int = 10) -> List[Tuple[str, int]]:
    """Return most searched queries and their counts."""
    rows = (
        db.query(Search_History.Query, func.count(Search_History.History_ID))
        .group_by(Search_History.Query)
        .order_by(func.count(Search_History.History_ID).desc())
        .limit(limit)
        .all()
    )
    return [(q or "", int(c)) for q, c in rows]


def get_favorite_trends(db: Session, limit: int = 10) -> List[Tuple[int, int]]:
    """Return most favorited products (Product_ID, count)."""
    rows = (
        db.query(Favorites.Product_ID, func.count(Favorites.ID))
        .group_by(Favorites.Product_ID)
        .order_by(func.count(Favorites.ID).desc())
        .limit(limit)
        .all()
    )
    return [(int(pid), int(c)) for pid, c in rows]


def get_review_summary(db: Session, product_id: Optional[int] = None, limit: int = 10):
    """Return review summary: for a product or top products overall."""
    if product_id is not None:
        row = (
            db.query(
                func.avg(User_Reviews.Rating).label("avg_rating"),
                func.count(User_Reviews.Review_ID).label("cnt"),
            )
            .filter(User_Reviews.Product_ID == product_id)
            .first()
        )
        avg_rating = float(row[0]) if row and row[0] is not None else None
        cnt = int(row[1]) if row and row[1] is not None else 0
        return {"product_id": product_id, "avg_rating": avg_rating, "review_count": cnt}

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
    return [(int(pid), float(avg), int(cnt)) for pid, avg, cnt in rows]


def purge_inactive_products(db: Session, months: int = 3, dry_run: bool = True) -> int:
    """Compute or purge products not searched within N months.

    Warning: Deleting may violate FKs (Favorites, Reviews). Default is dry_run.
    Returns number of products that would be deleted (or were deleted if dry_run=False).
    """
    since = datetime.utcnow() - timedelta(days=30 * months)

    # Products with no search history link since 'since'
    recent_product_ids = (
        db.query(Search_History_Products.Product_ID)
        .join(Search_History, Search_History.History_ID == Search_History_Products.History_ID)
        .filter(Search_History.Created_At >= since)
        .distinct()
        .subquery()
    )

    stale = db.query(Products).filter(~Products.Product_ID.in_(recent_product_ids))
    count = stale.count()
    if dry_run:
        return int(count)

    stale.delete(synchronize_session=False)
    db.commit()
    return int(count)


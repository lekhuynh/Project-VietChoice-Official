from typing import Dict, List, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.users import Users
from ..models.products import Products
from ..models.search_history import Search_History
from ..models.user_reviews import User_Reviews
from ..models.favorites import Favorites


def get_system_overview(db: Session) -> Dict[str, int]:
    users = db.query(func.count(Users.User_ID)).scalar() or 0
    products = db.query(func.count(Products.Product_ID)).scalar() or 0
    searches = db.query(func.count(Search_History.History_ID)).scalar() or 0
    reviews = db.query(func.count(User_Reviews.Review_ID)).scalar() or 0
    return {
        "users": int(users),
        "products": int(products),
        "searches": int(searches),
        "reviews": int(reviews),
    }


def get_recent_searches(db: Session, limit: int = 10) -> List[Search_History]:
    return (
        db.query(Search_History)
        .order_by(Search_History.Created_At.desc())
        .limit(max(1, limit))
        .all()
    )


def get_top_products(db: Session, limit: int = 10) -> List[Tuple[int, int]]:
    rows = (
        db.query(Products.Product_ID, Products.Review_Count)
        .order_by(Products.Review_Count.desc(), Products.Avg_Rating.desc())
        .limit(max(1, limit))
        .all()
    )
    return [(int(pid), int(rc or 0)) for pid, rc in rows]


def get_user_activity(db: Session, limit: int = 10) -> Dict[str, int]:
    favs = db.query(func.count(Favorites.ID)).scalar() or 0
    revs = db.query(func.count(User_Reviews.Review_ID)).scalar() or 0
    return {"favorites": int(favs), "reviews": int(revs)}

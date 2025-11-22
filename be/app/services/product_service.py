from typing import Any, Dict, Optional, Sequence

from sqlalchemy.orm import Session

from ..crud import products as product_crud
from ..models.products import Products


def get_product_detail(db: Session, product_id: int) -> Optional[Products]:
    return product_crud.get_by_id(db, product_id)


def get_products_by_category(db: Session, category_id: int, limit: int = 20, skip: int = 0) -> Sequence[Products]:
    return product_crud.get_products_by_category(db, category_id, limit=limit, skip=skip)


def list_products(db: Session, limit: int = 100, skip: int = 0) -> Sequence[Products]:
    return product_crud.list_products(db, skip=skip, limit=limit)


def update_sentiment_score_and_label(
    db: Session,
    product_id: int,
    *,
    score: Optional[float],
    label: Optional[str],
) -> Optional[Products]:
    prod = product_crud.get_by_id(db, product_id)
    if not prod:
        return None
    patch: Dict[str, Any] = {"Sentiment_Score": score, "Sentiment_Label": label}
    return product_crud.update_product(db, prod, patch)


def filter_products_service(
    db: Session,
    lv1=None,
    lv2=None,
    lv3=None,
    lv4=None,
    lv5=None,
    min_price=None,
    max_price=None,
    brand=None,
    min_rating=None,
    sort=None,
    skip: int = 0,
    limit: int = 20,
    is_vietnam_origin=False,
    is_vietnam_brand=False,
    positive_over=None,
):
    items, total = product_crud.get_products_by_category_and_filters(
        db=db,
        lv1=lv1,
        lv2=lv2,
        lv3=lv3,
        lv4=lv4,
        lv5=lv5,
        min_price=min_price,
        max_price=max_price,
        brand=brand,
        min_rating=min_rating,
        sort=sort,
        skip=skip,
        limit=limit,
        is_vietnam_origin=is_vietnam_origin,
        is_vietnam_brand=is_vietnam_brand,
        positive_over=positive_over,
    )
    return items, total


def search_products_service(
    db: Session,
    keyword: Optional[str] = None,
    limit: int = 20,
    skip: int = 0,
    lv1: Optional[str] = None,
    lv2: Optional[str] = None,
    lv3: Optional[str] = None,
    lv4: Optional[str] = None,
    lv5: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    sort: Optional[str] = None,
    is_vietnam_origin: bool = False,
    is_vietnam_brand: bool = False,
    positive_over: Optional[int] = None,
):
    items, total = product_crud.search_products_by_keyword_and_filters(
        db=db,
        keyword=keyword,
        limit=limit,
        skip=skip,
        lv1=lv1,
        lv2=lv2,
        lv3=lv3,
        lv4=lv4,
        lv5=lv5,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        sort=sort,
        is_vietnam_origin=is_vietnam_origin,
        is_vietnam_brand=is_vietnam_brand,
        positive_over=positive_over,
    )
    return items, total


def get_outstanding_product_service(
    db: Session,
    limit: int = 10,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
):
    """Admin: l���y top s���n ph��cm n��i b��-t theo �`i���m AI + l�����t tA�m ki���m."""
    return product_crud.get_outstanding_product(
        db,
        limit=limit,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
    )

from typing import Any, Dict, Optional, Sequence

from sqlalchemy.orm import Session

from ..crud import products as product_crud
from ..models.products import Products



def create_or_update_product(db: Session, product_data: Dict[str, Any]) -> Products:
    """Upsert product by External_ID.

    Updates basic fields when product exists; otherwise creates new one.
    """
    ext_id = product_data.get("External_ID") or product_data.get("external_id")
    if ext_id is not None:
        existing = product_crud.get_by_external_id(db, int(ext_id))
        if existing:
            patch: Dict[str, Any] = {}
            for key in [
                "Price",
                "Avg_Rating",
                "Review_Count",
                "Positive_Percent",
                "Sentiment_Score",
                "Sentiment_Label",
                "Image_URL",
                "Product_URL",
                "Barcode",
                "Brand",
                "Origin",
                "Attributes",
                "Is_Authentic",
                "Is_Active",
            ]:
                if key in product_data and product_data[key] is not None:
                    patch[key] = product_data[key]
            return product_crud.update_product(db, existing, patch)

    # Normalize keys from snake_case to DB columns if needed
    mapped = {
        "Source": product_data.get("Source") or product_data.get("source"),
        "External_ID": ext_id,
        "Barcode": product_data.get("Barcode") or product_data.get("barcode"),
        "Product_Name": product_data.get("Product_Name") or product_data.get("product_name"),
        "Brand": product_data.get("Brand") or product_data.get("brand"),
        "Category_ID": product_data.get("Category_ID") or product_data.get("category_id"),
        "Image_URL": product_data.get("Image_URL") or product_data.get("image_url"),
        "Product_URL": product_data.get("Product_URL") or product_data.get("product_url"),
        "Price": product_data.get("Price") or product_data.get("price"),
        "Avg_Rating": product_data.get("Avg_Rating") or product_data.get("avg_rating"),
        "Review_Count": product_data.get("Review_Count") or product_data.get("review_count"),
        "Positive_Percent": product_data.get("Positive_Percent") or product_data.get("positive_percent"),
        "Sentiment_Score": product_data.get("Sentiment_Score") or product_data.get("sentiment_score"),
        "Sentiment_Label": product_data.get("Sentiment_Label") or product_data.get("sentiment_label"),
        "Attributes": product_data.get("Attributes") or product_data.get("attributes"),
        "Origin": product_data.get("Origin") or product_data.get("origin"),
        "Is_Authentic": product_data.get("Is_Authentic") or product_data.get("is_authentic"),
        "Is_Active": product_data.get("Is_Active") or product_data.get("is_active"),
    }
    return product_crud.create_product(db, {k: v for k, v in mapped.items() if v is not None})


def get_product_by_external_id(db: Session, external_id: int) -> Optional[Products]:
    return product_crud.get_by_external_id(db, external_id)


def get_product_detail(db: Session, product_id: int) -> Optional[Products]:
    return product_crud.get_by_id(db, product_id)


def get_products_by_category(db: Session, category_id: int, limit: int = 20, skip: int = 0) -> Sequence[Products]:
    return product_crud.get_products_by_category(db, category_id, limit=limit, skip=skip)


def list_products(db: Session, limit: int = 100, skip: int = 0) -> Sequence[Products]:
    return product_crud.list_products(db, skip=skip, limit=limit)


def update_sentiment_score_and_label(db: Session, product_id: int, *, score: Optional[float], label: Optional[str]) -> Optional[Products]:
    prod = product_crud.get_by_id(db, product_id)
    if not prod:
        return None
    patch: Dict[str, Any] = {"Sentiment_Score": score, "Sentiment_Label": label}
    return product_crud.update_product(db, prod, patch)


def filter_products_service(
    db: Session,
    lv1=None, lv2=None, lv3=None, lv4=None, lv5=None,
    min_price=None, max_price=None,
    brand=None, min_rating=None,
    sort=None,
    skip: int = 0,
    limit: int = 20,
    is_vietnam_origin=False, is_vietnam_brand=False,
    positive_over=None,
):
    items, total = product_crud.get_products_by_category_and_filters(
        db=db,
        lv1=lv1, lv2=lv2, lv3=lv3, lv4=lv4, lv5=lv5,
        min_price=min_price, max_price=max_price,
        brand=brand, min_rating=min_rating,
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
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    sort: Optional[str] = None,
    is_vietnam_origin: bool = False,
    is_vietnam_brand: bool = False,
    positive_over: Optional[int] = None
):
    items, total = product_crud.search_products_by_keyword_and_filters(
        db=db,
        keyword=keyword,
        limit=limit,
        skip=skip,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        sort=sort,
        is_vietnam_origin=is_vietnam_origin,
        is_vietnam_brand=is_vietnam_brand,
        positive_over=positive_over
    )

    return items, total

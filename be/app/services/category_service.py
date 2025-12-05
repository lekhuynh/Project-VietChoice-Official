from typing import Any, Dict

from sqlalchemy.exc import IntegrityError

from sqlalchemy.orm import Session

from ..crud import categories as cat_crud
from ..models.categories import Categories


def create_or_get_category(db: Session, source: str, category_data: Dict[str, Any]) -> Categories:
    """Create category if not exists by (Source, Category_Path)."""
    data = {
        "Source": source or category_data.get("Source") or category_data.get("source") or "Tiki",
        "Category_Lv1": category_data.get("Category_Lv1") or category_data.get("category_lv1"),
        "Category_Lv2": category_data.get("Category_Lv2") or category_data.get("category_lv2"),
        "Category_Lv3": category_data.get("Category_Lv3") or category_data.get("category_lv3"),
        "Category_Lv4": category_data.get("Category_Lv4") or category_data.get("category_lv4"),
        "Category_Lv5": category_data.get("Category_Lv5") or category_data.get("category_lv5"),
        "Category_Path": category_data.get("Category_Path") or category_data.get("category_path"),
    }
    data = cat_crud.ensure_path_fields(data)
    existing = cat_crud.get_by_source_path(db, source=data["Source"], category_path=data["Category_Path"])
    if existing:
        return existing
    try:
        return cat_crud.create_category(db, data)
    except IntegrityError:
        # Another worker may have inserted the same category concurrently.
        db.rollback()
        existing = cat_crud.get_by_source_path(db, source=data["Source"], category_path=data["Category_Path"])
        if existing:
            return existing
        # If still not found, re-raise to surface the original issue.
        raise

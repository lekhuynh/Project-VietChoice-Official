from typing import Any, Dict, Optional, Sequence

from sqlalchemy.orm import Session

from ..crud import categories as cat_crud
from ..models.categories import Categories

from collections import defaultdict
import json

def create_or_get_category(db: Session, source: str, category_data: Dict[str, Any]) -> Categories:
    """Create category if not exists by (Source, Category_Path)."""
    # Normalize and ensure path
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
    return cat_crud.create_category(db, data)


def get_category_by_id(db: Session, category_id: int) -> Optional[Categories]:
    return cat_crud.get_by_id(db, category_id)


def get_category_by_path(db: Session, source: str, path: str) -> Optional[Categories]:
    return cat_crud.get_by_source_path(db, source=source, category_path=path)


def list_categories(db: Session, source: Optional[str] = None, q: Optional[str] = None, level: Optional[int] = None, limit: int = 100, offset: int = 0) -> Sequence[Categories]:
    if source or q or level is not None:
        return cat_crud.list_categories_advanced(db, source=source, q=q, level=level, limit=limit, offset=offset)
    return cat_crud.list_categories(db, skip=offset, limit=limit)

# -------------------------------
# TẠO CÂY DANH MỤC (TREE)
# -------------------------------
def build_category_tree(db: Session, source: str = "Tiki"):
    categories = cat_crud.list_categories_advanced(db, source=source, limit=10000)
    tree = defaultdict(dict)

    for c in categories:
        levels = [
            c.Category_Lv1, c.Category_Lv2,
            c.Category_Lv3, c.Category_Lv4, c.Category_Lv5
        ]
        lv = [x for x in levels if x]
        current = tree
        for name in lv:
            if name not in current:
                current[name] = {}
            current = current[name]
    return json.loads(json.dumps(tree))

# -------------------------------
# THÊM DANH MỤC MỚI
# -------------------------------
def add_category(db: Session, source: str, levels: list[str]):
    return cat_crud.get_or_create_chain(db, source=source, names=levels)

# -------------------------------
# LẤY DANH MỤC PHÂN TRANG
# -------------------------------
def get_all_categories(db: Session, skip: int = 0, limit: int = 100):
    return cat_crud.list_categories(db, skip, limit)

# -------------------------------
# XOÁ TOÀN BỘ DANH MỤC
# -------------------------------
def remove_all_categories(db: Session):
    from app.models.categories import Categories
    count = db.query(Categories).delete()
    db.commit()
    return count


# Service cho phần danh mục dạng phẳng
from sqlalchemy.orm import Session
from app.crud.categories import get_level1, get_children


def map_flat(c):
    return {
        "Category_ID": c.Category_ID,
        "name": c.Category_Path.split(">")[-1].strip(),
        "path": c.Category_Path,
        "level": c.Level_Count
    }


def get_roots(db: Session, source: str):
    return [map_flat(c) for c in get_level1(db, source)]


def get_child_list(db: Session, category_id: int):
    children = get_children(db, category_id)
    if not children:
        return []
    return [map_flat(c) for c in children]

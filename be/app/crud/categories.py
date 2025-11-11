from typing import Optional, Sequence, Dict, Any

from sqlalchemy.orm import Session

from ..models.categories import Categories


def get_by_id(db: Session, category_id: int) -> Optional[Categories]:
    return db.query(Categories).filter(Categories.Category_ID == category_id).first()


def get_by_source_path(db: Session, *, source: str, category_path: str) -> Optional[Categories]:
    return (
        db.query(Categories)
        .filter(Categories.Source == source, Categories.Category_Path == category_path)
        .first()
    )


def list_categories(db: Session, skip: int = 0, limit: int = 100) -> Sequence[Categories]:
    return db.query(Categories).offset(skip).limit(limit).all()


def create_category(db: Session, data: Dict[str, Any]) -> Categories:
    category = Categories(**data)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category: Categories, data: Dict[str, Any]) -> Categories:
    # Apply patch
    for k, v in data.items():
        setattr(category, k, v)
    # If any level fields or path are in patch, rebuild Category_Path and Level_Count
    level_keys = {"Category_Lv1", "Category_Lv2", "Category_Lv3", "Category_Lv4", "Category_Lv5", "Category_Path"}
    if any(k in data for k in level_keys):
        updated = ensure_path_fields({
            "Source": getattr(category, "Source", "Tiki") or "Tiki",
            "Category_Lv1": category.Category_Lv1,
            "Category_Lv2": category.Category_Lv2,
            "Category_Lv3": category.Category_Lv3,
            "Category_Lv4": category.Category_Lv4,
            "Category_Lv5": category.Category_Lv5,
            "Category_Path": category.Category_Path,
            "Level_Count": getattr(category, "Level_Count", None),
        })
        category.Category_Path = updated["Category_Path"]
        category.Level_Count = updated["Level_Count"]
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def normalize_name(name: str) -> str:
    """Basic normalization: strip and collapse internal spaces."""
    if name is None:
        return ""
    s = " ".join(str(name).strip().split())
    return s


def ensure_path_fields(d: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure Category_Path and Level_Count are consistent with Lv1..Lv5.

    - Build path as 'Lv1 > Lv2 > ...' skipping empty levels.
    - Level_Count is number of non-empty levels.
    - Default Source to 'Tiki' if missing.
    """
    lv = [normalize_name(d.get("Category_Lv1")), normalize_name(d.get("Category_Lv2")), normalize_name(d.get("Category_Lv3")), normalize_name(d.get("Category_Lv4")), normalize_name(d.get("Category_Lv5"))]
    parts = [p for p in lv if p]
    d["Category_Path"] = d.get("Category_Path") or " > ".join(parts)
    d["Level_Count"] = len(parts)
    d["Source"] = d.get("Source") or "Tiki"
    return d


def list_categories_advanced(
    db: Session,
    *,
    source: Optional[str] = None,
    q: Optional[str] = None,
    level: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
) -> Sequence[Categories]:
    """Filter categories by source, prefix/path contains, level; sorted by path."""
    query = db.query(Categories)
    if source:
        query = query.filter(Categories.Source == source)
    if q:
        # search in path or any level name
        like = f"%{q}%"
        query = query.filter(
            (Categories.Category_Path.ilike(like))
            | (Categories.Category_Lv1.ilike(like))
            | (Categories.Category_Lv2.ilike(like))
            | (Categories.Category_Lv3.ilike(like))
            | (Categories.Category_Lv4.ilike(like))
            | (Categories.Category_Lv5.ilike(like))
        )
    if level is not None:
        query = query.filter(Categories.Level_Count == level)
    return query.order_by(Categories.Category_Path.asc()).offset(offset).limit(limit).all()


def upsert_from_breadcrumbs(db: Session, *, source: str, breadcrumbs: Sequence[Dict[str, Any]]) -> Categories:
    """Create or fetch a category from breadcrumb list of names.

    breadcrumbs: list of items with at least a 'name' field.
    Returns the final (leaf) category.
    """
    names = [normalize_name(b.get("name") or b.get("Name") or "") for b in breadcrumbs]
    return get_or_create_chain(db, source=source or "Tiki", names=names)


def get_or_create_chain(db: Session, *, source: str, names: Sequence[str]) -> Categories:
    """Get or create a chain of categories according to names as Lv1..Lv5, return leaf."""
    data = {
        "Source": source or "Tiki",
        "Category_Lv1": names[0] if len(names) > 0 else None,
        "Category_Lv2": names[1] if len(names) > 1 else None,
        "Category_Lv3": names[2] if len(names) > 2 else None,
        "Category_Lv4": names[3] if len(names) > 3 else None,
        "Category_Lv5": names[4] if len(names) > 4 else None,
    }
    data = ensure_path_fields(data)
    existing = get_by_source_path(db, source=data["Source"], category_path=data["Category_Path"])
    if existing:
        return existing
    return create_category(db, data)


def rebuild_is_leaf_flags(db: Session, source: Optional[str] = None) -> int:
    """No-op: schema no longer contains Is_Leaf. Kept for backward compatibility."""
    return 0


def search_tree_prefix(db: Session, *, source: str, prefix: str, limit: int = 50) -> Sequence[Categories]:
    """Find categories whose path starts with given prefix (case-insensitive)."""
    like = f"{prefix}%"
    return (
        db.query(Categories)
        .filter(Categories.Source == (source or "Tiki"), Categories.Category_Path.ilike(like))
        .order_by(Categories.Category_Path.asc())
        .limit(limit)
        .all()
    )


def stats_by_level(db: Session, source: Optional[str] = None) -> Dict[int, int]:
    """Return mapping level -> count for admin overview."""
    from sqlalchemy import func

    q = db.query(Categories.Level_Count, func.count(Categories.Category_ID)).group_by(Categories.Level_Count)
    if source:
        q = q.filter(Categories.Source == source)
    rows = q.all()
    return {int(level): int(cnt) for level, cnt in rows if level is not None}


def bulk_import_paths(db: Session, *, source: str, rows: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    """Bulk import categories from rows with Lv fields or Category_Path.

    Skips rows that would violate (Source, Category_Path) uniqueness.
    Returns counters.
    """
    inserted = 0
    skipped = 0
    errors = 0
    for row in rows:
        try:
            data = {
                "Source": source or row.get("Source") or "Tiki",
                "Category_Lv1": row.get("Category_Lv1"),
                "Category_Lv2": row.get("Category_Lv2"),
                "Category_Lv3": row.get("Category_Lv3"),
                "Category_Lv4": row.get("Category_Lv4"),
                "Category_Lv5": row.get("Category_Lv5"),
                "Category_Path": row.get("Category_Path"),
            }
            data = ensure_path_fields(data)
            if get_by_source_path(db, source=data["Source"], category_path=data["Category_Path"]):
                skipped += 1
                continue
            create_category(db, data)
            inserted += 1
        except Exception:
            db.rollback()
            errors += 1
    return {"inserted": inserted, "skipped": skipped, "errors": errors}


# crud cho danh mục
from sqlalchemy.orm import Session
from app.models.categories import Categories


def get_level1(db: Session, source: str):
    return db.query(Categories).filter(
        Categories.Source == source,
        Categories.Level_Count == 1
    ).all()


def get_by_id(db: Session, category_id: int):
    return db.query(Categories).filter(
        Categories.Category_ID == category_id
    ).first()


def get_children(db: Session, category_id: int):
    parent = get_by_id(db, category_id)
    if not parent:
        return None

    return db.query(Categories).filter(
        Categories.Source == parent.Source,
        Categories.Category_Path.like(parent.Category_Path + " >%"),
        Categories.Level_Count == parent.Level_Count + 1
    ).all()

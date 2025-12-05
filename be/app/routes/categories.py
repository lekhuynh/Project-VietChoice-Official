from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.categories import Categories
from ..cache import get_json, set_json

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("/tree")
def get_categories_tree(db: Session = Depends(get_db)):
    """
    Trả về toàn bộ danh mục dạng cây (nested JSON).
    """
    cache_key = "cache:category:tree"
    cached = get_json(cache_key)
    if cached:
        return cached

    rows = (
        db.query(
            Categories.Category_Lv1,
            Categories.Category_Lv2,
            Categories.Category_Lv3,
            Categories.Category_Lv4,
            Categories.Category_Lv5,
        )
        .filter(Categories.Category_Lv1.isnot(None))
        .all()
    )

    tree = {}

    for r in rows:
        lv1, lv2, lv3, lv4, lv5 = r

        if lv1 not in tree:
            tree[lv1] = {"name": lv1, "children": {}}

        node = tree[lv1]["children"]

        if lv2:
            if lv2 not in node:
                node[lv2] = {"name": lv2, "children": {}}
            node = node[lv2]["children"]

        if lv3:
            if lv3 not in node:
                node[lv3] = {"name": lv3, "children": {}}
            node = node[lv3]["children"]

        if lv4:
            if lv4 not in node:
                node[lv4] = {"name": lv4, "children": {}}
            node = node[lv4]["children"]

        if lv5:
            if lv5 not in node:
                node[lv5] = {"name": lv5, "children": {}}

    def dict_to_list(node_dict):
        return [
            {
                "name": v["name"],
                "children": dict_to_list(v["children"]) if v["children"] else [],
            }
            for v in node_dict.values()
        ]

    result = dict_to_list(tree)
    set_json(cache_key, result, ttl_seconds=21600)
    return result

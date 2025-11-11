from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.categories import Categories

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("/tree")
def get_categories_tree(db: Session = Depends(get_db)):
    """
    Trả về toàn bộ danh mục dạng cây (nested JSON).
    Mỗi cấp trong Category_Lv1 → Lv5 sẽ được nhóm theo thứ tự.
    """
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

        # Cấp 1
        if lv1 not in tree:
            tree[lv1] = {"name": lv1, "children": {}}

        node = tree[lv1]["children"]

        # Cấp 2
        if lv2:
            if lv2 not in node:
                node[lv2] = {"name": lv2, "children": {}}
            node = node[lv2]["children"]

        # Cấp 3
        if lv3:
            if lv3 not in node:
                node[lv3] = {"name": lv3, "children": {}}
            node = node[lv3]["children"]

        # Cấp 4
        if lv4:
            if lv4 not in node:
                node[lv4] = {"name": lv4, "children": {}}
            node = node[lv4]["children"]

        # Cấp 5
        if lv5:
            if lv5 not in node:
                node[lv5] = {"name": lv5, "children": {}}

    # Chuyển từ dict → list để FE dễ dùng
    def dict_to_list(node_dict):
        return [
            {
                "name": v["name"],
                "children": dict_to_list(v["children"]) if v["children"] else [],
            }
            for v in node_dict.values()
        ]

    return dict_to_list(tree)

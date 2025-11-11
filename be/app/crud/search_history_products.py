from typing import Sequence

from sqlalchemy.orm import Session

from ..models.search_history_products import Search_History_Products


def link_product(db: Session, *, history_id: int, product_id: int) -> Search_History_Products:
    link = Search_History_Products(History_ID=history_id, Product_ID=product_id)
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def list_by_history(db: Session, history_id: int) -> Sequence[Search_History_Products]:
    return db.query(Search_History_Products).filter(Search_History_Products.History_ID == history_id).all()


def unlink_product(db: Session, *, link: Search_History_Products) -> None:
    db.delete(link)
    db.commit()


from sqlalchemy.orm import Session
from ..crud import search_history as history_crud


def save_search_history(db: Session, user, query: str, results: list[dict]):
    """
    Lưu lịch sử tìm kiếm nếu có user hợp lệ.
    """
    if not user:
        return None

    count = len(results or [])
    history = history_crud.create_history(
        db,
        user_id=user.User_ID,
        query=query,
        result_count=count
    )

    if count > 0:
        ids = [p.get("Product_ID") for p in results if "Product_ID" in p]
        if ids:
            history_crud.link_history_to_products(
                db, history_id=history.History_ID, product_ids=ids
            )
    return history

from __future__ import annotations
from typing import Any, Dict, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..crud import products as product_crud
from app.database import SessionLocal
from app.models.products import Products
from app.services import crawler_tiki_service as tiki
from app.services.crawler_tiki_service import get_reviews_summary
from app.services.sentiment_service import update_product_sentiment

def _refresh_single_product(db: Session, product: Products) -> Dict[str, Any]:
    detail = tiki.get_product_detail(int(product.External_ID))
    # -------- CASE 1: TIKI XÓA THẬT (404) --------
    if detail == "NOT_FOUND":
        updated = product_crud.update_product(db, product, {"Is_Active": False})
        return {
            "product_id": updated.Product_ID,
            "external_id": updated.External_ID,
            "status": "deactivated_404",
        }
    # -------- CASE 2: API ERROR → KHÔNG deactivate --------
    if detail == "API_ERROR" or detail is None:
        return {
            "product_id": product.Product_ID,
            "external_id": product.External_ID,
            "status": "skipped_api_error",
        }

    # -------- CASE 3: CHECK tồn kho --------
    inv = detail.get("inventory_status")
    deactivate_states = ["out_of_stock", "discontinued", "unavailable"]

    # 3A. Hết hàng → deactivate
    if inv in deactivate_states:
        updated = product_crud.update_product(db, product, {"Is_Active": False})
        return {
            "product_id": updated.Product_ID,
            "external_id": updated.External_ID,
            "status": f"deactivated_{inv}",
        }

    # 3B. Còn hàng → set active
    if inv == "available":
        product_crud.update_product(db, product, {"Is_Active": True})

    # 3C. Các trường hợp NULL/unknown → skip
    if inv not in deactivate_states and inv != "available":
        return {
            "product_id": product.Product_ID,
            "external_id": product.External_ID,
            "status": f"skipped_inventory_{inv}",
        }

    # -------- CASE 4: UPDATE FULL DATA --------
    summary = get_reviews_summary(int(product.External_ID))

    thumb = detail.get("thumbnail_url")
    full_img = thumb.replace("/cache/280x280", "") if thumb else None

    patch = {
        "Image_URL": thumb,
        "Image_Full_URL": full_img,
        "Price": detail.get("price"),
        "Avg_Rating": summary.get("rating_average"),
        "Review_Count": summary.get("reviews_count"),
        "Positive_Percent": summary.get("positive_percent"),
        "Is_Active": True,
    }

    patch = {k: v for k, v in patch.items() if v is not None}

    updated = product_crud.update_product(db, product, patch)

    sentiment_score = update_product_sentiment(db, updated.Product_ID)

    return {
        "product_id": updated.Product_ID,
        "external_id": updated.External_ID,
        "status": "updated",
        "sentiment_score": sentiment_score,
    }

def _process_product(product_id: int, external_id: int) -> Dict[str, Any]:
    """Worker: mở Session riêng để thread-safe."""
    local_db = SessionLocal()
    try:
        prod = (
            local_db.query(Products)
            .filter(Products.Product_ID == product_id)
            .first()
        )
        if not prod:
            return {
                "product_id": product_id,
                "external_id": external_id,
                "status": "missing",
            }
        return _refresh_single_product(local_db, prod)
    except Exception as exc:  # noqa: BLE001
        local_db.rollback()
        return {
            "product_id": product_id,
            "external_id": external_id,
            "status": "error",
            "error": str(exc),
        }
    finally:
        local_db.close()


def auto_update_products(
    db: Session,
    *,
    older_than_hours: int = 12,
    limit: Optional[int] = None,
    workers: int = 8,
) -> Dict[str, Any]:

    products = product_crud.get_tiki_products_older_than(db, hours=older_than_hours)
    work_items: List[tuple[int, int]] = [
        (p.Product_ID, int(p.External_ID))
        for p in products
        if p.External_ID
    ]

    if limit and limit > 0:
        work_items = work_items[:limit]

    total = len(work_items)

    # stats auto tạo dynamic
    stats: Dict[str, Any] = {
        "total": total,
        "items": [],
    }

    if total == 0:
        print("[AutoUpdate] Không có sản phẩm nào cần cập nhật.")
        return stats

    print(
        f"[AutoUpdate] Bắt đầu batch: total={total}, "
        f"older_than_hours={older_than_hours}, workers={workers}"
    )

    processed = 0
    progress_step = max(1, total // 10)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_process_product, pid, ext_id): (pid, ext_id)
            for pid, ext_id in work_items
        }

        for future in as_completed(futures):

            pid, ext_id = futures[future]

            try:
                result = future.result()
            except Exception as exc:
                result = {
                    "product_id": pid,
                    "external_id": ext_id,
                    "status": "error",
                    "error": str(exc),
                }

            status = result.get("status", "unknown")

            # Tự tạo counter, khỏi cần if-else
            stats[status] = stats.get(status, 0) + 1

            stats["items"].append(result)

            processed += 1
            if processed % progress_step == 0 or processed == total:
                print(
                    f"[AutoUpdate] Progress: {processed}/{total} "
                    + ", ".join([f"{k}={v}" for k, v in stats.items() if k not in ("total","items")])
                )

    print(
        "\n[AutoUpdate] Hoàn tất batch:",
        ", ".join([f"{k}={v}" for k, v in stats.items() if k not in ("items")])
    )

    return stats

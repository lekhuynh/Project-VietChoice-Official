from __future__ import annotations
from typing import Any, Dict, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

# ===============================================================
#  AUTO UPDATE PRODUCTS SERVICE
# ---------------------------------------------------------------
# 🎯 Mục tiêu:
# - Tự động cập nhật lại dữ liệu sản phẩm trong bảng Products
# - Lấy dữ liệu mới nhất từ API Tiki cho mỗi sản phẩm.
# - Nếu sản phẩm không còn tồn tại trên Tiki → đánh dấu Is_Active = False.
# - Cập nhật đồng thời:
#     • Price
#     • Avg_Rating  
#     • Review_Count
#     • Positive_Percent
# ---------------------------------------------------------------
# 🔁 Quy trình xử lý:
# 1️⃣ Lấy toàn bộ danh sách sản phẩm từ bảng Products.
# 2️⃣ Với mỗi sản phẩm:
#     - Gọi API https://tiki.vn/api/v2/products/{External_ID}
#     - Nếu không trả dữ liệu hoặc lỗi → gán Is_Active = False.
#     - Nếu có dữ liệu:
#           Cập nhật các trường chi tiết sản phẩm mới nhất.
#           Cập nhật điểm rating, review_count, positive_percent.
#     - Gọi get_product_reviews(product_id) để lấy comment mới.
#     - Gọi update_product_sentiment(db, product_id)
#           → cập nhật lại Sentiment_Score & Sentiment_Label.
# 3️⃣ Ghi log số sản phẩm được cập nhật, số sản phẩm bị vô hiệu hóa.
# 4️⃣ Cập nhật Updated_At = NOW() để đánh dấu lần cập nhật cuối.
# 5️⃣ Commit sau mỗi sản phẩm (hoặc batch commit nếu muốn tối ưu).
#
# ---------------------------------------------------------------
# ⚙️ Các hàm liên quan cần dùng:
# - get_product_detail(product_id)       → crawler_tiki.py
# - get_product_reviews(product_id)      → crawler_tiki.py
# - update_product_sentiment(db, id)     → sentiment_analysis.py
#
# ---------------------------------------------------------------
# 📦 Dữ liệu lưu lại trong DB:
# | Cột                | Nguồn dữ liệu          |
# |--------------------|------------------------|
# | Price              | API Tiki               |
# | Avg_Rating         | API Tiki               |
# | Review_Count       | API Tiki               |
# | Positive_Percent   | API Tiki               |
# | Sentiment_Score    | Sentiment Analysis     |
# | Sentiment_Label    | Sentiment Analysis     |
# | Updated_At         | Local UTC time         |
# | Is_Active          | False nếu bị xóa       |
#
# ---------------------------------------------------------------
# 🧠 Mở rộng gợi ý:
# - Thêm retry logic khi gọi API (thử lại 3 lần nếu lỗi).
# - Thêm scheduler chạy tự động mỗi 24h hoặc mỗi tuần.
# - Ghi log chi tiết sản phẩm nào bị xóa / cập nhật thành công.
# ---------------------------------------------------------------
# 📂 File liên quan:
# - app/services/auto_update_service.py      (file chính)
# - app/services/crawler_tiki.py             (gọi API Tiki)
# - app/services/sentiment_analysis.py       (phân tích cảm xúc)
# - app/routes/admin_routes.py               (endpoint thủ công)
# ---------------------------------------------------------------
# ✅ Endpoint gợi ý:
# POST /admin/force-update-products
#    → Thực hiện cập nhật toàn bộ sản phẩm trong DB.
# ---------------------------------------------------------------
# ===============================================================
# app/services/auto_update_service.py

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..crud import products as product_crud
from ..services import sentiment_service

def auto_update_sentiment(db: Session):
    """
    Tự động cập nhật sentiment cho các sản phẩm cũ hơn 24h
    """
    try:
        # Lấy thời điểm 24h trước
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # Lấy các sản phẩm cần cập nhật (có Updated_At cũ hơn 24h hoặc chưa có sentiment)
        products_to_update = product_crud.get_products_need_sentiment_update(db, cutoff_time)
        
        updated_count = 0
        for product in products_to_update:
            try:
                # Cập nhật sentiment cho sản phẩm
                sentiment_service.update_product_sentiment(db, product.Product_ID)
                updated_count += 1
            except Exception as e:
                print(f"Error updating sentiment for product {product.Product_ID}: {e}")
                continue
        
        return {
            "status": "success",
            "message": f"Auto-update completed. Updated {updated_count} products.",
            "updated_count": updated_count,
            "total_checked": len(products_to_update)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Auto-update failed: {str(e)}"
        }
from sqlalchemy.orm import Session

from app.crud import products as product_crud
from app.database import SessionLocal
from app.models.products import Products
from app.services import crawler_tiki_service as tiki
from app.services.crawler_tiki_service import get_reviews_summary
from app.services.sentiment_service import update_product_sentiment


def _refresh_single_product(db: Session, product: Products) -> Dict[str, Any]:
    """Cập nhật 1 sản phẩm: price/rating/review/positive + sentiment."""
    detail = tiki.get_product_detail(int(product.External_ID))
    if not detail:
        updated = product_crud.update_product(db, product, {"Is_Active": False})
        return {
            "product_id": updated.Product_ID,
            "external_id": updated.External_ID,
            "status": "deactivated",
        }

    summary = get_reviews_summary(int(product.External_ID))
    
    #lấy thumbnail và tạo ảnh full-size
    thumb = detail.get("thumbnail_url")
    # Tạo ảnh full-size bằng cách bỏ cache/280x280
    full_img = None
    if thumb:
        full_img = thumb.replace("/cache/280x280", "")
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
    """Refresh các trường động cho sản phẩm Tiki cũ hơn N giờ thông qua threadpool."""
    products = product_crud.get_tiki_products_older_than(db, hours=older_than_hours)
    work_items: List[tuple[int, int]] = [
        (p.Product_ID, int(p.External_ID))
        for p in products
        if p.External_ID
    ]
    if limit and limit > 0:
        work_items = work_items[:limit]

    total = len(work_items)
    stats = {
        "total": total,
        "updated": 0,
        "deactivated": 0,
        "errors": 0,
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
    progress_step = max(1, total // 10)  # log mỗi 10% hoặc ít nhất mỗi 1 item

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_process_product, pid, ext_id): (pid, ext_id)
            for pid, ext_id in work_items
        }
        for future in as_completed(futures):
            pid, ext_id = futures[future]
            try:
                result = future.result()
            except Exception as exc:  # noqa: BLE001
                result = {
                    "product_id": pid,
                    "external_id": ext_id,
                    "status": "error",
                    "error": str(exc),
                }

            status = result.get("status")
            if status == "updated":
                stats["updated"] += 1
            elif status == "deactivated":
                stats["deactivated"] += 1
            elif status == "error":
                stats["errors"] += 1

            stats["items"].append(result)

            processed += 1
            if processed % progress_step == 0 or processed == total:
                print(
                    f"[AutoUpdate] Progress: {processed}/{total} "
                    f"(updated={stats['updated']}, "
                    f"deactivated={stats['deactivated']}, "
                    f"errors={stats['errors']})"
                )

    print(
        f"[AutoUpdate] Hoàn tất batch: total={stats['total']}, "
        f"updated={stats['updated']}, "
        f"deactivated={stats['deactivated']}, "
        f"errors={stats['errors']}"
    )
    return stats

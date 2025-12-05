from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import os
import tempfile
from app.models.products import Products
from app.models.categories import Categories
import math
from ..database import get_db
from ..services import crawler_tiki_service as tiki
from ..services import barcode_service
from ..services.product_service import filter_products_service
from ..crud import products as product_crud
from ..core.security import get_optional_user
from ..services.search_history_service import save_search_history
from ..services.view_history_service import add_view_history
from ..services.chat_intent_service import parse_search_intent
from ..services.product_service import search_products_service
from ..tasks.crawler import enqueue_crawl_keyword, enqueue_crawl_barcode, enqueue_scan_image, enqueue_scan_barcode_image
from ..cache import get_json, set_json
from typing import Optional, List, Dict



# Job status helper
from ..tasks.job_status import get_job_status
router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/jobs/{job_id}")
def job_status(job_id: str):
    return get_job_status(job_id)


# ============================================================
# 1a TÌM KIẾM SẢN PHẨM THEO TÊN (TEXT SEARCH)
#============================================================
@router.get("/search")
async def search_product(
    q: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user)
):
    # 1. G?i Gemini ph?n t?ch
    intent = await parse_search_intent(q)

    # 2. N?u AI b?o ??y l? chat -> kh?ng c?o
    if intent.get("is_searching") is False:
        print(f"[Stop Crawl] Chat detected: '{q}'")
        return {
            "input_type": "chat",
            "query": q,
            "count": 0,
            "results": [],
            "ai_message": intent.get("message"),
        }

    # 3. Enqueue crawler thay v? ch?y tr?c ti?p
    refined_query = intent.get("product_name") or q
    print(f"[Search] '{q}' -> enqueue crawl for keyword: '{refined_query}'")

    job_id = enqueue_crawl_keyword(refined_query)

    return {
        "input_type": "product_search",
        "query": q,
        "refined_query": refined_query,
        "count": 0,
        "results": [],
        "ai_message": None,
        "job_id": job_id,
        "status": "queued",
    }

def _serialize_product(product: Products) -> dict:
    return {
        "Product_ID": product.Product_ID,
        "Product_Name": product.Product_Name,
        "Brand": product.Brand,
        "Image_URL": product.Image_URL,
        "Product_URL": product.Product_URL,
        "Price": float(product.Price) if product.Price else None,
        "Avg_Rating": product.Avg_Rating,
        "Review_Count": product.Review_Count,
        "Positive_Percent": product.Positive_Percent,
        "Sentiment_Score": product.Sentiment_Score,
        "Sentiment_Label": product.Sentiment_Label,
        "Origin": product.Origin,
        "Brand_country": product.Brand_country,
        "Source": product.Source,
    }

# ============================================================
# 1b TÌM KIẾM SẢN PHẨM TRONG CSDL (LOCAL SEARCH)
# ============================================================
@router.get("/search/local")
def search_product_local(
    q: str,
    limit: int = Query(20, ge=1, le=50),
    skip: int = Query(0, ge=0),
    lv1: Optional[str] = None,
    lv2: Optional[str] = None,
    lv3: Optional[str] = None,
    lv4: Optional[str] = None,
    lv5: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    brand: Optional[str] = None,
    min_rating: Optional[float] = None,
    sort: Optional[str] = None,
    is_vietnam_origin: Optional[bool] = False,
    is_vietnam_brand: Optional[bool] = False,
    positive_over: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user)
):
    keyword = (q or "").strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="Thi?u t? kh?a t?m ki?m")

    cache_key = (
        f"cache:search_local:{keyword}:{limit}:{skip}:"
        f"{lv1}:{lv2}:{lv3}:{lv4}:{lv5}:{min_price}:{max_price}:{brand}:"
        f"{min_rating}:{sort}:{is_vietnam_origin}:{is_vietnam_brand}:{positive_over}"
    )
    cached = get_json(cache_key)
    if cached:
        return cached

    items, total = search_products_service(
        db=db,
        keyword=keyword,
        limit=limit,
        skip=skip,
        lv1=lv1, lv2=lv2, lv3=lv3, lv4=lv4, lv5=lv5,
        min_price=min_price,
        max_price=max_price,
        brand=brand,
        min_rating=min_rating,
        sort=sort,
        is_vietnam_origin=is_vietnam_origin,
        is_vietnam_brand=is_vietnam_brand,
        positive_over=positive_over,
    )

    results = [_serialize_product(p) for p in items]

    if results:
        save_search_history(db, current_user, query=q, results=results)

    payload = {
        "input_type": "local_product_search",
        "query": q,
        "refined_query": keyword,
        "total": total,
        "skip": skip,
        "limit": limit,
        "count": len(results),
        "results": results
    }
    set_json(cache_key, payload, ttl_seconds=600)
    return payload

# ============================================================
# 2️⃣ TRA CỨU SẢN PHẨM THEO MÃ VẠCH (BARCODE)
# ============================================================
@router.get("/barcode/{barcode}")
def lookup_by_barcode(barcode: str, db: Session = Depends(get_db), current_user=Depends(get_optional_user)):
    """
    Tra c?u s?n ph?m qua m? v?ch.
    Thay v? c?o tr?c ti?p, enqueue v?o queue ?? worker x? l?.
    """
    if not barcode:
        raise HTTPException(status_code=400, detail="Thi?u m? v?ch")

    job_id = enqueue_crawl_barcode(barcode)
    return {
        "input_type": "barcode",
        "query": barcode,
        "count": 0,
        "results": [],
        "job_id": job_id,
        "status": "queued",
    }




# ============================================================
# 3️⃣ QUÉT ẢNH SẢN PHẨM (OCR)
# ============================================================
@router.post("/scan/image")
async def scan_product_image(file: UploadFile = File(...), db: Session = Depends(get_db), current_user=Depends(get_optional_user)):
    """
    Qu?t ?nh s?n ph?m -> enqueue job ?? OCR/crawl trong worker.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    job_id = enqueue_scan_image(tmp_path, filename=file.filename)
    return {
        "input_type": "image",
        "query": file.filename,
        "count": 0,
        "results": [],
        "job_id": job_id,
        "status": "queued",
    }

# ============================================================
# 3b️⃣ QUÉT MÃ VẠCH TỪ ẢNH (pyzbar)
# ============================================================
@router.post("/barcode/scan")
async def scan_barcode_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user)
):
    """
    Nh?n ?nh, decode barcode, enqueue crawler theo m? t?t nh?t.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename or "")[-1] or ".png") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    job_id = enqueue_scan_barcode_image(tmp_path)
    return {
        "input_type": "barcode_image",
        "query": file.filename,
        "count": 0,
        "results": [],
        "job_id": job_id,
        "status": "queued",
    }

# ============================================================
# 4️⃣ LẤY SẢN PHẨM THEO DANH MỤC VÀ BỘ LỌC
# ============================================================
from app.services.product_service import filter_products_service
from typing import Optional

@router.get("/by-category")
def get_products_by_category(
    lv1: Optional[str] = None,
    lv2: Optional[str] = None,
    lv3: Optional[str] = None,
    lv4: Optional[str] = None,
    lv5: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    brand: Optional[str] = None,
    min_rating: Optional[float] = None,
    sort: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    is_vietnam_origin: Optional[bool] = False,
    is_vietnam_brand: Optional[bool] = False,
    positive_over: Optional[int] = None,
    db: Session = Depends(get_db)
):
    items, total = filter_products_service(
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

    results = [_serialize_product(p) for p in items]

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "count": len(results),
        "results": results
    }

# ============================================================
# 4️⃣ LẤY CHI TIẾT SẢN PHẨM TRONG DB
# ============================================================
@router.get("/{product_id}")
def get_product_detail(product_id: int, db: Session = Depends(get_db), current_user=Depends(get_optional_user)):
    """
    Lấy thông tin chi tiết sản phẩm đã lưu trong DB (không cần crawler).
    """
    cache_key = f"cache:product:{product_id}"
    cached = get_json(cache_key)
    if cached:
        add_view_history(db, current_user, product_id)
        return cached

    product = product_crud.get_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm trong DB")
    add_view_history(db, current_user, product_id)
    data = {
        "Product_ID": product.Product_ID,
        "Product_Name": product.Product_Name,
        "Brand": product.Brand,
        "Category_ID": product.Category_ID,
        "Price": product.Price,
        "Avg_Rating": product.Avg_Rating,
        "Review_Count": product.Review_Count,
        "Positive_Percent": product.Positive_Percent,
        "Sentiment_Score": product.Sentiment_Score,
        "Sentiment_Label": product.Sentiment_Label,
        "Origin": product.Origin,
        "Brand_country": product.Brand_country,
        "Image_URL": product.Image_URL,
        "Product_URL": product.Product_URL,
        "Description": product.Description,
        "Is_Authentic": product.Is_Authentic,
        "Is_Active": product.Is_Active,
        "Source": product.Source,
        "Image_Full_URL": product.Image_Full_URL,
    }
    set_json(cache_key, data, ttl_seconds=600)
    return data

# ============================================================
# 5️⃣ CẬP NHẬT LẠI ĐIỂM SENTIMENT
# ============================================================
@router.put("/update_sentiment/{product_id}")
def update_sentiment(product_id: int, db: Session = Depends(get_db)):
    product = product_crud.get_by_id(db, product_id)
    if not product:
        raise HTTPException(404, "Kh?ng t?m th?y s?n ph?m trong DB")
    if product.Source != "Tiki" or not product.External_ID:
        raise HTTPException(400, "S?n ph?m n?y kh?ng ph?i t? Tiki ho?c thi?u External_ID")

    from ..tasks.sentiment import enqueue_update_sentiment

    job_id = enqueue_update_sentiment(product_id)
    return {"product_id": product_id, "external_id": product.External_ID, "job_id": job_id, "status": "queued"}


# =========================================================
# 6️⃣ CẬP NHẬT SENTIMENT HÀNG LOẠT
# =========================================================
@router.put("/update_all_sentiment")
def update_all_sentiment(db: Session = Depends(get_db)):
    """
    Enqueue sentiment update cho to?n b? s?n ph?m Tiki.
    """
    products = product_crud.get_all_tiki_products(db)
    from ..tasks.sentiment import enqueue_update_sentiment
    job_ids = [enqueue_update_sentiment(p.Product_ID) for p in products]
    return {"total": len(products), "job_ids": job_ids, "status": "queued"}


# =========================================================
# 7️⃣ CRUD CƠ BẢN
# =========================================================
@router.get("/")
def list_products(db: Session = Depends(get_db)):
    return product_crud.get_all(db)


@router.delete("/{product_id}")
def delete_products(product_id: int, db: Session = Depends(get_db)):
    ok = product_crud.delete(db, product_id)
    if not ok:
        raise HTTPException(404, "Không thể xóa sản phẩm (không tồn tại).")
    return {"message": f"Đã xóa sản phẩm ID {product_id}."}


# =========================================================
# 8️⃣ GỢI Ý SẢN PHẨM TỐT NHẤT
# =========================================================
@router.get("/recommend/best/{product_id}")
def recommend_best_products(product_id: int, limit: int = 5, db: Session = Depends(get_db)):
    """
    G?i ? s?n ph?m t?t nh?t c?ng danh m?c (?u ti?n sentiment/rating/review).
    """
    from ..services.recommender_service import recommend_best_in_category

    cache_key = f"cache:recommend:{product_id}:{limit}"
    cached = get_json(cache_key)
    if cached:
        return cached

    try:
        products = recommend_best_in_category(db, product_id, limit) or []
    except Exception:
        products = []

    # Serialize ra dict để FE luôn nhận đủ field và tránh object không JSON-serializable
    serialized = [_serialize_product(p) for p in products]

    set_json(cache_key, serialized, ttl_seconds=3600)
    return serialized

@router.get("/{product_id}/risk")
def get_product_risk(product_id: int, db: Session = Depends(get_db)):
    from ..tasks.risk import enqueue_risk_score

    job_id = enqueue_risk_score(product_id)
    return {"product_id": product_id, "job_id": job_id, "status": "queued"}

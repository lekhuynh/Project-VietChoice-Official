from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import os
import tempfile
from app.models.products import Products
from app.models.categories import Categories
from ..services.risk_service import evaluate_risk
from ..database import get_db
from ..services import crawler_tiki_service as tiki
from ..services.product_service import filter_products_service
from ..crud import products as product_crud
from ..core.security import get_optional_user
from ..services.search_history_service import save_search_history
from ..services.view_history_service import add_view_history

router = APIRouter(prefix="/products", tags=["Products"])

# ============================================================
# 1️⃣ TÌM KIẾM SẢN PHẨM THEO TÊN (TEXT SEARCH)
# ============================================================
@router.get("/search")
def search_product(q: str, db: Session = Depends(get_db), current_user=Depends(get_optional_user)):
    """
    Tìm kiếm sản phẩm theo từ khóa (tên sản phẩm).
    - Gọi Tiki crawler để lấy danh sách sản phẩm.
    """
    if not q:
        raise HTTPException(status_code=400, detail="Thiếu từ khóa tìm kiếm")

    results = tiki.crawl_by_text(db, q)
    if not results:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm phù hợp")
    save_search_history(db, current_user, query=q, results=results)
    return {
        "input_type": "text",
        "query": q,
        "count": len(results),
        "results": results
    }


# ============================================================
# 2️⃣ TRA CỨU SẢN PHẨM THEO MÃ VẠCH (BARCODE)
# ============================================================
@router.get("/barcode/{barcode}")
def lookup_by_barcode(barcode: str, db: Session = Depends(get_db), current_user=Depends(get_optional_user)):
    """
    Tra cứu sản phẩm qua mã vạch.
    - Gọi iCheck để lấy tên sản phẩm.
    - Nếu không có → fallback sang Tiki.
    """
    if not barcode:
        raise HTTPException(status_code=400, detail="Thiếu mã vạch")

    results = tiki.crawl_by_barcode(db, barcode)
    if not results:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm cho mã vạch này")
    save_search_history(db, current_user, query=barcode, results=results)
    return {
        "input_type": "barcode",
        "query": barcode,
        "count": len(results),
        "results": results
    }


# ============================================================
# 3️⃣ QUÉT ẢNH SẢN PHẨM (OCR)
# ============================================================
@router.post("/scan/image")
async def scan_product_image(file: UploadFile = File(...), db: Session = Depends(get_db), current_user=Depends(get_optional_user)):
    """
    Quét ảnh sản phẩm:
    - Lưu ảnh tạm.
    - Dùng OCR đọc chữ.
    - Tìm sản phẩm tương ứng trên Tiki.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        results = tiki.crawl_by_image(db, tmp_path)
        if not results:
            raise HTTPException(status_code=404, detail="Không nhận diện được hoặc không tìm thấy sản phẩm")
        save_search_history(db, current_user, query=file.filename, results=results)
        return {
            "input_type": "image",
            "query": file.filename,
            "count": len(results),
            "results": results
        }
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
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
    sort: Optional[str] = None,  # "price_asc" | "price_desc" | "rating_desc"
    is_vietnam_origin: Optional[bool] = False,
    is_vietnam_brand: Optional[bool] = False,
    positive_over: Optional[int] = None,
    db: Session = Depends(get_db)
):
    products = filter_products_service(
        db=db,
        lv1=lv1, lv2=lv2, lv3=lv3, lv4=lv4, lv5=lv5,
        min_price=min_price, max_price=max_price,
        brand=brand, min_rating=min_rating,
        sort=sort,
        is_vietnam_origin=is_vietnam_origin,
        is_vietnam_brand=is_vietnam_brand,
        positive_over=positive_over,
    )
    return products
# ============================================================
# 4️⃣ LẤY CHI TIẾT SẢN PHẨM TRONG DB
# ============================================================
@router.get("/{product_id}")
def get_product_detail(product_id: int, db: Session = Depends(get_db), current_user=Depends(get_optional_user)):
    """
    Lấy thông tin chi tiết sản phẩm đã lưu trong DB (không cần crawler).
    """
    product = product_crud.get_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm trong DB")
    add_view_history(db, current_user, product_id)
    return {
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
        "Source": product.Source
    }


# ============================================================
# 5️⃣ CẬP NHẬT LẠI ĐIỂM SENTIMENT
# ============================================================
@router.put("/update_sentiment/{product_id}")
def update_sentiment(product_id: int, db: Session = Depends(get_db)):
    product = product_crud.get_by_id(db, product_id)
    if not product:
        raise HTTPException(404, "Không tìm thấy sản phẩm trong DB")
    if product.Source != "Tiki" or not product.External_ID:
        raise HTTPException(400, "Sản phẩm này không phải từ Tiki hoặc thiếu External_ID")

    score = tiki.update_sentiment_from_tiki_reviews(db, int(product.External_ID))
    if score is None:
        return {
            "product_id": product_id,
            "external_id": product.External_ID,
            "message": "Sản phẩm chưa có review trên Tiki nên không phân tích được."
        }
    return {"product_id": product_id, "external_id": product.External_ID, "sentiment_score": score}


# =========================================================
# 6️⃣ CẬP NHẬT SENTIMENT HÀNG LOẠT
# =========================================================
@router.put("/update_all_sentiment")
def update_all_sentiment(db: Session = Depends(get_db)):
    """
    Cập nhật cảm xúc cho toàn bộ sản phẩm có Source='Tiki'.
    Dùng khi chạy cron 12h/lần hoặc cập nhật batch.
    """
    products = product_crud.get_all_tiki_products(db)
    updated = 0
    for p in products:
        score = tiki.update_sentiment_from_tiki_reviews(db, int(p.External_ID))
        if score:
            updated += 1
    return {"total": len(products), "updated": updated}


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
    Gợi ý sản phẩm tốt nhất cùng danh mục, ưu tiên:
    - Sentiment_Score cao nhất
    - Avg_Rating cao nhất
    - Review_Count nhiều nhất
    """
    from ..services.recommender_service import recommend_best_in_category

    products = recommend_best_in_category(db, product_id, limit)
    if not products:
        raise HTTPException(404, "Không tìm thấy sản phẩm gợi ý phù hợp.")
    return products

@router.get("/{product_id}/risk")
def get_product_risk(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Products).filter(Products.Product_ID == product_id).first()

    if not product:
        return {"detail": "Product not found"}

    risk = evaluate_risk(product)

    return {
        "Product_ID": product_id,
        "Risk_Score": risk["risk_score"],
        "Risk_Level": risk["risk_level"],
        "Reasons": risk["reasons"]
    }

# # =========================================================
# # 9️⃣ LẤY SẢN PHẨM THEO DANH MỤC
# # =========================================================
# from typing import Optional

# @router.get("/by-category")
# def get_products_by_category(
#     lv1: Optional[str] = Query(None),
#     lv2: Optional[str] = Query(None),
#     lv3: Optional[str] = Query(None),
#     lv4: Optional[str] = Query(None),
#     lv5: Optional[str] = Query(None),
#     db: Session = Depends(get_db),
# ):
#     query = db.query(Products).join(Categories, Products.Category_ID == Categories.Category_ID)

#     if lv1:
#         query = query.filter(Categories.Category_Lv1.ilike(f"%{lv1}%"))
#     if lv2:
#         query = query.filter(Categories.Category_Lv2.ilike(f"%{lv2}%"))
#     if lv3:
#         query = query.filter(Categories.Category_Lv3.ilike(f"%{lv3}%"))
#     if lv4:
#         query = query.filter(Categories.Category_Lv4.ilike(f"%{lv4}%"))
#     if lv5:
#         query = query.filter(Categories.Category_Lv5.ilike(f"%{lv5}%"))

#     return query.all()

# # =========================================================
# # Bộ lọc sản phẩm (dùng trong routes/products.py)
# # =========================================================

# @router.get("/filter")
# def filter_products(
#     db: Session = Depends(get_db),
#     min_price: float = Query(None),
#     max_price: float = Query(None),
#     brand: str = Query(None),
#     min_rating: float = Query(None),
#     sort: str = Query(None, description="price_asc | price_desc | rating_desc"),
#     is_vietnam_origin: bool = Query(False),
#     is_vietnam_brand: bool = Query(False),
#     positive_over: int = Query(None),
#     category_path: str = Query(None, description="vd: Đồ Chơi > Đồ chơi trẻ em")
# ):
#     """
#     Bộ lọc sản phẩm:
#     - Khoảng giá, thương hiệu, rating
#     - Sắp xếp: price_asc | price_desc | rating_desc
#     - Ưu tiên hàng Việt Nam
#     - Lọc theo danh mục (category_path)
#     """
#     return filter_products_service(
#         db=db,
#         min_price=min_price,
#         max_price=max_price,
#         brand=brand,
#         min_rating=min_rating,
#         sort=sort,
#         is_vietnam_origin=is_vietnam_origin,
#         is_vietnam_brand=is_vietnam_brand,
#         positive_over=positive_over,
#         category_path=category_path
#     )

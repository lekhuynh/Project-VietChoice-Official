from __future__ import annotations
import time
import json
from typing import Any, Dict, List, Optional
import math, threading
import requests
from sqlalchemy.orm import Session

from ..crud import products as product_crud
from ..services.category_service import create_or_get_category
from ..services.sentiment_service import analyze_comment, label_sentiment


# ============================================================
# =============== API CONSTANTS & HELPERS ====================
# ============================================================

TIKI_DETAIL_API = "https://tiki.vn/api/v2/products/{product_id}"
TIKI_REVIEWS_API = "https://tiki.vn/api/v2/reviews"


def _headers(referer: Optional[str] = None) -> dict:
    """Fake browser headers to bypass Tiki restrictions."""
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Referer": referer or "https://tiki.vn/",
    }

def fetch_tiki_reviews(product_id: int, limit: int = 20, page: int = 1, retry: int = 1) -> Optional[Dict[str, Any]]:
    """Lấy dữ liệu review từ API chính thức của Tiki."""
    params = {
        "limit": max(1, min(50, limit)),
        "include": "comments",
        "page": page,
        "product_id": int(product_id),
    }
    for _ in range(retry + 1):
        try:
            resp = requests.get(TIKI_REVIEWS_API, params=params, timeout=10)
            resp.encoding = 'utf-8'
            if resp.status_code == 200:
                return resp.json()
            time.sleep(0.4)
        except (requests.RequestException, json.JSONDecodeError):
            time.sleep(0.6)
            continue
    return None

# ============================================================
# =============== BASIC API CALLS =============================
# ============================================================

def get_product_detail(
    product_id: int,
    referer: Optional[str] = None,
    retry: int = 1
) -> Optional[Dict[str, Any]]:
    """Fetch product detail from Tiki API."""
    url = TIKI_DETAIL_API.format(product_id=int(product_id))
    for _ in range(retry + 1):
        try:
            resp = requests.get(url, headers=_headers(referer=referer), timeout=12)
            resp.encoding = 'utf-8'
            if resp.status_code != 200:
                time.sleep(0.4)
                continue
            return resp.json()
        except (requests.RequestException, json.JSONDecodeError):
            time.sleep(0.6)
            continue
    return None


def get_product_reviews(
    product_id: int,
    limit: int = 20, # Giới hạn số lượng review mỗi trang (mặc định 20)
    retry: int = 2
) -> List[str]:
    """
    Hàm dịch vụ TUẦN TỰ (Synchronous) lấy TOÀN BỘ đánh giá của sản phẩm.

    Thực hiện 3 bước:
    1. Lấy dữ liệu Page 1 và review_count.
    2. Tính total_pages = ceil(review_count / page_limit).
    3. Lặp tuần tự từ Page 1 đến total_pages để thu thập tất cả review.
    """
    all_reviews: List[str] = []
    # Giới hạn số lượng review yêu cầu cho mỗi trang (max 50)
    max_limit = min(50, limit) 

    # 1. GỌI API LẦN ĐẦU (PAGE 1) ĐỂ LẤY review_count
    params = {
        "limit": max_limit,
        "include": "comments",
        "page": 1,
        "product_id": int(product_id),
    }
    
    data: Dict[str, Any] = {}
    review_count: int = 0
    total_pages: int = 1
    
    # Thực hiện request đầu tiên (có retry)
    for _ in range(retry + 1):
        try:
            resp = requests.get(TIKI_REVIEWS_API, params=params, headers=_headers(), timeout=12)
            resp.encoding = "utf-8"
            if resp.status_code == 200:
                data = resp.json() or {}
                break
        except requests.RequestException:
            time.sleep(0.6)
            continue
    
    # 2. TÍNH TOÁN SỐ TRANG
    if not data:
        return []

    # Giả định: review_count nằm trong trường 'paging' -> 'total'
    review_count = data.get("paging", {}).get("total", 0) 
    
    if review_count > 0:
        # TÍNH TOÁN: review_count / max_limit và làm tròn lên
        total_pages = math.ceil(review_count / max_limit)
        
    print(f"Tổng số đánh giá: {review_count}. Tổng số trang cần lấy: {total_pages}")
    
    # 3. LẶP TUẦN TỰ QUA TẤT CẢ CÁC TRANG
    for page in range(1, total_pages + 1):
        
        # Nếu là page 1, sử dụng dữ liệu đã có (tối ưu hóa nhỏ)
        if page == 1:
            current_page_data = data
        else:
            # Request cho các trang tiếp theo
            params["page"] = page
            current_page_data = {}
            
            # Logic retry cho các trang tiếp theo
            for _ in range(retry + 1):
                try:
                    resp = requests.get(TIKI_REVIEWS_API, params=params, headers=_headers(), timeout=12)
                    resp.encoding = "utf-8"
                    if resp.status_code == 200:
                        current_page_data = resp.json() or {}
                        break
                except (requests.RequestException, json.JSONDecodeError):
                    time.sleep(0.6)
                    continue

        reviews_on_page = current_page_data.get("data") or []
        
        # 4. TRÍCH XUẤT NỘI DUNG ĐÁNH GIÁ (Logic gốc)
        for r in reviews_on_page:
            title = (r.get("title") or "").strip()
            content = (r.get("content") or "").strip()
            text = (title + ", " + content).strip() if (title or content) else ""
            if text:
                all_reviews.append(text)
                
    return all_reviews
# ============================================================
# =============== SENTIMENT UPDATE ===========================
# ============================================================

def update_sentiment_from_tiki_reviews(db: Session, product_id: int) -> Optional[float]:
    """Analyze Tiki reviews → compute sentiment score → update DB."""
    comments = get_product_reviews(product_id, limit=20)
    if not comments:
        product_crud.update_sentiment(db, product_id, score=None, label=None)
        return None

    scores = [analyze_comment(c) for c in comments if c]
    if not scores:
        product_crud.update_sentiment(db, product_id, score=None, label=None)
        return None

    avg_score = sum(scores) / len(scores)
    label = label_sentiment(avg_score)
    product_crud.update_sentiment(db, product_id, score=avg_score, label=label)
    return avg_score


# ============================================================
# =============== MAIN CRAWLER LOGIC =========================
# ============================================================

def crawl_and_save_tiki_product(db: Session, product_id: int) -> Optional[Dict[str, Any]]:
    """Fetch data from Tiki APIs (detail + reviews), parse, and save to DB."""
    product_data = get_product_detail(product_id)
    if not product_data:
        return None

    # ---------------------------
    # Lấy danh mục (breadcrumbs)
    # ---------------------------
    breadcrumbs = product_data.get("breadcrumbs", []) or []

    # ✅ Loại bỏ breadcrumb là sản phẩm (category_id == 0 hoặc url chứa product_id)
    breadcrumbs = [
        b for b in breadcrumbs
        if (isinstance(b.get("category_id"), int) and b.get("category_id") > 0)
        and str(product_id) not in (b.get("url") or "")
    ]

    category_id = None

    if breadcrumbs:
        # Map các cấp danh mục
        category_dict = {
            "Category_Lv1": breadcrumbs[0].get("name") if len(breadcrumbs) > 0 else None,
            "Category_Lv2": breadcrumbs[1].get("name") if len(breadcrumbs) > 1 else None,
            "Category_Lv3": breadcrumbs[2].get("name") if len(breadcrumbs) > 2 else None,
            "Category_Lv4": breadcrumbs[3].get("name") if len(breadcrumbs) > 3 else None,
            "Category_Lv5": breadcrumbs[4].get("name") if len(breadcrumbs) > 4 else None,
        }

        from ..crud import categories as cat_crud
        from ..services.category_service import create_or_get_category

        # Chuẩn hóa Category_Path và Level_Count
        category_data = cat_crud.ensure_path_fields({
            "Source": "Tiki",
            **category_dict
        })

        # Kiểm tra trùng (Source + Category_Path)
        existing = cat_crud.get_by_source_path(
            db,
            source=category_data["Source"],
            category_path=category_data["Category_Path"]
        )

        if existing:
            category_id = existing.Category_ID
            print(f"[Category] Reuse existing ID {category_id} for path: {category_data['Category_Path']}")
        else:
            new_category = create_or_get_category(db, source="Tiki", category_data=category_dict)
            category_id = new_category.Category_ID
            print(f"[Category] Created new category ID {category_id}: {category_data['Category_Path']}")

    else:
        category_id = None

    # ---------------------------
    # Lấy Rating, Review Count và Positive Percent từ API riêng
    # ---------------------------
    avg_rating, review_count, positive_percent = None, None, None
    try:
        review_resp = requests.get(
            f"https://tiki.vn/api/v2/reviews?product_id={product_id}&include=comments&limit=1",
            headers=_headers(),
            timeout=10
        )
        if review_resp.status_code == 200:
            review_json = review_resp.json()
            avg_rating = review_json.get("rating_average")
            review_count = review_json.get("reviews_count")

            # ✅ Tính Positive Percent nếu có dữ liệu sao
            stars = review_json.get("stars", {})
            if stars:
                # Cấu trúc mỗi sao: {"count": int, "percent": int}
                total = sum([v.get("count", 0) for v in stars.values()])
                if total > 0:
                    positive = stars.get("5", {}).get("count", 0) + stars.get("4", {}).get("count", 0)
                    positive_percent = round((positive / total) * 100, 2)
                    print(f"[DEBUG] Positive_Percent = {positive_percent}% ({positive}/{total})")
    except Exception :
        pass

    # ---------------------------
    # Lấy Origin và Brand Country trong attributes
    # ---------------------------
    origin, brand_country = None, None
    try:
        specs = product_data.get("specifications", [])
        for block in specs:
            for attr in block.get("attributes", []):
                if attr.get("code") == "origin":
                    origin = attr.get("value")
                elif attr.get("code") == "brand_country":
                    brand_country = attr.get("value")
    except Exception:
        pass
        # ---------------------------
    # Lấy và làm sạch mô tả sản phẩm
    # ---------------------------
    from bs4 import BeautifulSoup
    description_clean = None
    try:
        html_desc = product_data.get("description", "")
        if html_desc:
            soup = BeautifulSoup(html_desc, "html.parser")
            # Loại bỏ HTML, tách dòng giữa các đoạn
            description_clean = soup.get_text(separator="\n").strip()
            # Xóa dòng trống và ký tự thừa
            description_clean = "\n".join(
                [line.strip() for line in description_clean.splitlines() if line.strip()]
            )
    except Exception as e:
        print(f"[Warning] Không lấy được mô tả: {e}")

    # ---------------------------
    # Chuẩn bị dữ liệu lưu vào DB
    # ---------------------------
    product_record = {
        "External_ID": product_data.get("id"),
        "Product_Name": product_data.get("name"),
        "Brand": (product_data.get("brand") or {}).get("name"),
        "Category_ID": category_id,
        "Image_URL": product_data.get("thumbnail_url"),
        "Product_URL": f"https://tiki.vn/{product_data.get('url_path')}",
        "Price": product_data.get("price"),
        "Brand_country": brand_country,
        "Origin": origin,
        "Avg_Rating": avg_rating,
        "Review_Count": review_count,
        "Positive_Percent": positive_percent,
        "Source": "Tiki",
        "Description": description_clean,
    }

    product = product_crud.create_or_update_by_external_id(db, product_record)
    print("[DEBUG] Lưu sản phẩm:", product_record)
    if not product:
        return None

    # ---------------------------
    # Cập nhật sentiment (phân tích cảm xúc)
    # ---------------------------
    update_sentiment_from_tiki_reviews(db, product.External_ID)

    return {
        "Product_ID": product.Product_ID,
        "Product_Name": product.Product_Name,
        "Image_URL": product.Image_URL,
        "Price": product.Price,
        "Category_ID": product.Category_ID,
        "Avg_Rating": avg_rating,
        "Review_Count": review_count,
        "Positive_Percent": positive_percent,
        "Origin": origin,
        "Brand_country":  brand_country,
    }


# ============================================================
# =============== EXTENDED BULK & PIPELINE ===================
# ============================================================

from ..services import icheck_service, ocr_service


# ---------------------- Lấy danh sách 10 ID ----------------------
def get_tiki_ids(keyword: str, page: int = 1, limit: int = 10) -> List[int]:
    """
    Gọi API Tiki để lấy danh sách external_id sản phẩm theo từ khóa.
    Loại bỏ quảng cáo (advertisement hoặc Tiki Ads).
    """
    search_url = f"https://tiki.vn/api/v2/products?q={requests.utils.quote(keyword)}&page={page}"
    try:
        resp = requests.get(search_url, headers=_headers(), timeout=10)
        if resp.status_code != 200:
            print(f"[TIKI] Request failed: {resp.status_code}")
            return []

        data = resp.json()
        items = data.get("data", [])
        ids = []
        for item in items:
            if item.get("advertisement") or "Tiki Ads" in item.get("badges", []):
                continue
            pid = item.get("id")
            if pid:
                ids.append(pid)
            if len(ids) >= limit:
                break
        return ids

    except Exception as e:
        print(f"[TIKI] Error fetching IDs: {e}")
        return []



def search_and_crawl_tiki_products(db: Session, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    ✅ Pipeline tối ưu:
    - Tìm danh sách product_id từ Tiki.
    - Bỏ qua các sản phẩm đã tồn tại trong DB (theo External_ID).
    - Cào song song (multi-thread) để tăng tốc.
    - Trả về danh sách kết quả sản phẩm (có hoặc đã tồn tại).
    """

    if not keyword:
        print("[TIKI] ⚠️ Thiếu từ khóa tìm kiếm.")
        return []

    print(f"\n🔍 [TIKI] Bắt đầu tìm kiếm từ khóa: '{keyword}'")

    # ----------------------
    # B1: Lấy danh sách ID từ API Tiki
    # ----------------------
    ids = get_tiki_ids(keyword, page=1, limit=limit)
    if not ids:
        print(f"[TIKI] ❌ Không tìm thấy sản phẩm nào cho '{keyword}'")
        return []

    print(f"[TIKI] ✅ Lấy được {len(ids)} ID sản phẩm từ API.")

    results: List[Dict[str, Any]] = []

    # ----------------------
    # B2: Kiểm tra trùng trong DB (External_ID)
    # ----------------------
    existing_ids = set(product_crud.get_all_external_ids(db))
    new_ids = [pid for pid in ids if pid not in existing_ids]

    if not new_ids:
        print("[TIKI] 🔁 Tất cả sản phẩm đã tồn tại trong DB. Bỏ qua cào.")
    else:
        print(f"[TIKI] ⚙️ Có {len(new_ids)} sản phẩm mới cần cào.")

    # ----------------------
    # B3: Lấy dữ liệu sản phẩm đã có sẵn (để trả về ngay)
    # ----------------------
    for pid in existing_ids.intersection(ids):
        existing = product_crud.get_by_external_id(db, pid)
        if existing:
            results.append({
                "Product_ID": existing.Product_ID,
                "Product_Name": existing.Product_Name,
                "Image_URL": existing.Image_URL,
                "Price": existing.Price,
                "Category_ID": existing.Category_ID,
                "Avg_Rating": existing.Avg_Rating,
                "Review_Count": existing.Review_Count,
                "Positive_Percent": existing.Positive_Percent,
                "Origin": existing.Origin,
                "Brand_country": existing.Brand_country
            })

    # ----------------------
    # B4: Cào sản phẩm mới song song (tối đa 5 luồng)
    # ----------------------
    from ..database import SessionLocal

    def crawl_single(pid: int):
        local_db = SessionLocal()
        try:
            print(f"[TIKI] ⏳ Cào sản phẩm ID {pid}...")
            result = crawl_and_save_tiki_product(local_db, pid)
            local_db.commit()
            return result
        except Exception as e:
            print(f"[TIKI] ⚠️ Lỗi khi cào ID {pid}: {e}")
            local_db.rollback()
            return None
        finally:
            local_db.close()


    start_time = time.time()
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        for product in executor.map(crawl_single, new_ids):
            if product:
                results.append(product)

    duration = round(time.time() - start_time, 2)
    print(f"[TIKI] ✅ Hoàn tất cào {len(new_ids)} sản phẩm mới trong {duration}s.")

    # ----------------------
    # B5: Trả kết quả tổng hợp
    # ----------------------
    print(f"[TIKI] 🔎 Tổng cộng {len(results)} sản phẩm được trả về.")
    return results



# ---------------------- 3 pipeline đầu vào ----------------------
def crawl_by_barcode(db: Session, barcode: str) -> List[Dict[str, Any]]:
    """
    Pipeline cho route /products/barcode/{barcode}.
    1️⃣ Dùng iCheck để tra tên sản phẩm.
    2️⃣ Nếu có tên → tìm trên Tiki (hàm crawl_by_text sẽ tự lưu DB).
    3️⃣ Nếu iCheck hoặc Tiki đều không ra → trả thông báo hướng dẫn nhập tên.
    """
    if not barcode:
        return [{"message": "Thiếu mã vạch để tra cứu."}]

    # 1️⃣ Gọi iCheck
    product_name = icheck_service.lookup_product_name(barcode)

    if product_name:
        print(f"[iCheck] ✅ Tìm thấy tên sản phẩm: {product_name}")

        # 2️⃣ Gọi Tiki theo tên (crawl_by_text đã tự lưu DB)
        results = crawl_by_text(db, product_name)
        if results:
            return results

        # Tiki không có kết quả
        print(f"[Tiki] ⚠️ Không tìm thấy sản phẩm nào cho '{product_name}'.")
        return [{
            "message": f"Không tìm thấy sản phẩm tương ứng với mã vạch {barcode}. "
                       "Vui lòng nhập tên sản phẩm để tiếp tục tìm kiếm."
        }]

    # 3️⃣ iCheck không có dữ liệu
    print(f"[iCheck] ❌ Không tìm thấy dữ liệu cho barcode {barcode}.")
    return [{
        "message": f"Không tìm thấy sản phẩm cho mã vạch {barcode}. "
                   "Vui lòng nhập tên sản phẩm để tìm kiếm."
    }]



def crawl_by_image(db: Session, image_path: str) -> List[Dict[str, Any]]:
    """
    Pipeline cho route /products/scan/image.
    1️⃣ Dùng OCR để trích xuất text từ ảnh.
    2️⃣ Nếu có text → tìm sản phẩm trên Tiki.
    3️⃣ Nếu không có hoặc không tìm thấy → trả thông báo hướng dẫn người dùng nhập tên.
    """
    if not image_path:
        return [{"message": "Thiếu đường dẫn ảnh để quét."}]

    # 1️⃣ OCR đọc chữ từ ảnh
    text = ocr_service.extract_text_from_image(image_path)
    if not text:
        print("[OCR] ❌ Không nhận diện được chữ trong ảnh.")
        return [{"message": "Không nhận diện được chữ trong ảnh. Vui lòng thử lại hoặc nhập tên sản phẩm."}]

    print(f"[OCR] ✅ Nhận diện được từ ảnh: '{text}'")

    # 2️⃣ Tìm sản phẩm bằng chữ đã nhận diện
    results = crawl_by_text(db, text)
    if results:
        return results

    # 3️⃣ Không tìm thấy gì trên Tiki
    print(f"[Tiki] ⚠️ Không tìm thấy sản phẩm nào cho từ khóa '{text}'.")
    return [{
        "message": f"Không tìm thấy sản phẩm tương ứng với chữ nhận diện '{text}'. "
                   "Vui lòng nhập tên sản phẩm để tiếp tục tìm kiếm."
    }]



def crawl_by_text(db: Session, text: str) -> List[Dict[str, Any]]:
    """
    Pipeline cho route /search?q=...
    1. Dùng text làm từ khóa tìm kiếm Tiki.
    """
    if not text:
        return []
    print(f"[Search] Tìm sản phẩm với từ khóa: {text}")
    return search_and_crawl_tiki_products(db, keyword=text)

from __future__ import annotations
import time
import json
from typing import Any, Dict, List, Optional
import math, threading
import concurrent.futures
import asyncio
import aiohttp
import requests
from sqlalchemy.orm import Session

from ..crud import products as product_crud
from ..services.category_service import create_or_get_category
from ..services.sentiment_service import analyze_comment, label_sentiment
from ..services.http_async import get_json_with_session, bounded_gather


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
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Referer": referer or "https://tiki.vn/",
    }


# Shared aiohttp session for reduced handshake/DNS cost
_SHARED_SESSION: Optional[aiohttp.ClientSession] = None


async def get_shared_session() -> aiohttp.ClientSession:
    global _SHARED_SESSION
    if _SHARED_SESSION is None or _SHARED_SESSION.closed:
        timeout = aiohttp.ClientTimeout(total=20)
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50, ttl_dns_cache=300)
        _SHARED_SESSION = aiohttp.ClientSession(timeout=timeout, connector=connector)
    return _SHARED_SESSION


# =========================
# Async HTTP helper methods
# =========================

async def aget_product_detail(product_id: int, referer: Optional[str] = None, retry: int = 1, session: Optional[aiohttp.ClientSession] = None) -> Optional[Dict[str, Any]]:
    url = TIKI_DETAIL_API.format(product_id=int(product_id))
    own = False
    if session is None:
        own = True
        timeout = aiohttp.ClientTimeout(total=15)
        session = aiohttp.ClientSession(timeout=timeout)
    try:
        for attempt in range(retry + 1):
            try:
                async with session.get(url, headers=_headers(referer=referer)) as resp:
                    if resp.status == 200:
                        return await resp.json(content_type=None)
            except Exception:
                await asyncio.sleep(0.4 * (attempt + 1))
                continue
        return None
    finally:
        if own:
            await session.close()


async def _aget_review_page(session: aiohttp.ClientSession, product_id: int, page: int, limit: int) -> List[str]:
    params = {
        "limit": max(1, min(50, limit)),
        "include": "comments",
        "page": page,
        "product_id": int(product_id),
    }
    try:
        async with session.get(TIKI_REVIEWS_API, headers=_headers(), params=params) as resp:
            if resp.status != 200:
                return []
            data = await resp.json(content_type=None)
    except Exception:
        return []

    reviews_on_page = data.get("data") or []
    out: List[str] = []
    for r in reviews_on_page:
        title = (r.get("title") or "").strip()
        content = (r.get("content") or "").strip()
        text = (title + ", " + content).strip() if (title or content) else ""
        if text:
            out.append(text)
    return out


async def aget_product_reviews(product_id: int, limit: int = 20, retry: int = 2, max_pages: Optional[int] = None) -> List[str]:
    """Fetch review texts concurrently using aiohttp.

    - limit: items per page (max 50 by API)
    - max_pages: if set, only fetch up to this many pages for speed
    """
    timeout = aiohttp.ClientTimeout(total=20)
    connector = aiohttp.TCPConnector(limit=50)
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        # First page to determine total pages
        params = {
            "limit": min(50, max(1, limit)),
            "include": "comments",
            "page": 1,
            "product_id": int(product_id),
        }
        data: Dict[str, Any] = {}
        for attempt in range(retry + 1):
            try:
                async with session.get(TIKI_REVIEWS_API, headers=_headers(), params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        break
            except Exception:
                await asyncio.sleep(0.4 * (attempt + 1))
                continue

        if not data:
            return []

        review_count = data.get("paging", {}).get("total", 0)
        max_limit = params["limit"]
        total_pages = max(1, math.ceil(review_count / max_limit)) if review_count else 1
        if isinstance(max_pages, int) and max_pages > 0:
            total_pages = min(total_pages, max_pages)

        # Collect page 1 immediately
        all_reviews: List[str] = []
        page1_reviews = data.get("data") or []
        for r in page1_reviews:
            title = (r.get("title") or "").strip()
            content = (r.get("content") or "").strip()
            text = (title + ", " + content).strip() if (title or content) else ""
            if text:
                all_reviews.append(text)

        if total_pages <= 1:
            return all_reviews

        coros = [
            _aget_review_page(session, product_id, page=p, limit=max_limit)
            for p in range(2, total_pages + 1)
        ]
        other_pages = await bounded_gather(coros, limit=20)
        for texts in other_pages:
            if texts:
                all_reviews.extend(texts)

        return all_reviews


async def aget_reviews_summary(product_id: int, session: Optional[aiohttp.ClientSession] = None) -> Dict[str, Any]:
    """Get rating_average, reviews_count and compute positive_percent from stars."""
    own = False
    if session is None:
        own = True
        session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
    try:
        url = f"https://tiki.vn/api/v2/reviews?product_id={product_id}&include=comments&limit=1"
        try:
            async with session.get(url, headers=_headers()) as resp:
                if resp.status != 200:
                    return {"rating_average": None, "reviews_count": None, "positive_percent": None}
                review_json = await resp.json(content_type=None)
        except Exception:
            return {"rating_average": None, "reviews_count": None, "positive_percent": None}

        avg_rating = review_json.get("rating_average")
        review_count = review_json.get("reviews_count")

        positive_percent = None
        stars = review_json.get("stars", {}) or {}
        try:
            total = sum([v.get("count", 0) for v in stars.values()])
            if total > 0:
                positive = (stars.get("5", {}).get("count", 0) + stars.get("4", {}).get("count", 0))
                positive_percent = round((positive / total) * 100, 2)
        except Exception:
            positive_percent = None

        return {
            "rating_average": avg_rating,
            "reviews_count": review_count,
            "positive_percent": positive_percent,
        }
    finally:
        if own:
            await session.close()

def fetch_tiki_reviews(product_id: int, limit: int = 20, page: int = 1, retry: int = 1) -> Optional[Dict[str, Any]]:
    """Láº¥y dá»¯ liá»‡u review tá»« API chÃ­nh thá»©c cá»§a Tiki."""
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


async def aget_tiki_ids(keyword: str, page: int = 1, limit: int = 10) -> List[int]:
    """Async: fetch product IDs from Tiki search API, filtering out ads."""
    from urllib.parse import quote
    search_url = f"https://tiki.vn/api/v2/products?q={quote(keyword)}&page={page}"
    connector = aiohttp.TCPConnector(limit=20)
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        try:
            async with session.get(search_url, headers=_headers()) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json(content_type=None)
        except Exception:
            return []

    items = data.get("data", []) if isinstance(data, dict) else []
    ids: List[int] = []
    for item in items:
        try:
            if item.get("advertisement") or "Tiki Ads" in (item.get("badges") or []):
                continue
            pid = item.get("id")
            if pid:
                ids.append(int(pid))
            if len(ids) >= limit:
                break
        except Exception:
            continue
    return ids

# ============================================================
# =============== BASIC API CALLS =============================
# ============================================================

def get_product_detail(
    product_id: int,
    referer: Optional[str] = None,
    retry: int = 1
) -> Optional[Dict[str, Any]]:
    """Fetch product detail from Tiki API (async under the hood)."""
    try:
        return asyncio.run(aget_product_detail(product_id, referer=referer, retry=retry))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(aget_product_detail(product_id, referer=referer, retry=retry))
        finally:
            loop.close()


def get_product_reviews(
    product_id: int,
    limit: int = 20, # Giá»›i háº¡n sá»‘ lÆ°á»£ng review má»—i trang (máº·c Ä‘á»‹nh 20)
    retry: int = 2
) -> List[str]:
    """
    HÃ m dá»‹ch vá»¥ TUáº¦N Tá»° (Synchronous) láº¥y TOÃ€N Bá»˜ Ä‘Ã¡nh giÃ¡ cá»§a sáº£n pháº©m.

    Thá»±c hiá»‡n 3 bÆ°á»›c:
    1. Láº¥y dá»¯ liá»‡u Page 1 vÃ  review_count.
    2. TÃ­nh total_pages = ceil(review_count / page_limit).
    3. Láº·p tuáº§n tá»± tá»« Page 1 Ä‘áº¿n total_pages Ä‘á»ƒ thu tháº­p táº¥t cáº£ review.
    """
    all_reviews: List[str] = []
    # Giá»›i háº¡n sá»‘ lÆ°á»£ng review yÃªu cáº§u cho má»—i trang (max 50)
    max_limit = min(50, limit) 

    # 1. Gá»ŒI API Láº¦N Äáº¦U (PAGE 1) Äá»‚ Láº¤Y review_count
    params = {
        "limit": max_limit,
        "include": "comments",
        "page": 1,
        "product_id": int(product_id),
    }
    
    data: Dict[str, Any] = {}
    review_count: int = 0
    total_pages: int = 1
    
    # Thá»±c hiá»‡n request Ä‘áº§u tiÃªn (cÃ³ retry)
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
    
    # 2. TÃNH TOÃN Sá» TRANG
    if not data:
        return []

    # Giáº£ Ä‘á»‹nh: review_count náº±m trong trÆ°á»ng 'paging' -> 'total'
    review_count = data.get("paging", {}).get("total", 0) 
    
    if review_count > 0:
        # TÃNH TOÃN: review_count / max_limit vÃ  lÃ m trÃ²n lÃªn
        total_pages = math.ceil(review_count / max_limit)
        
    print(f"Tá»•ng sá»‘ Ä‘Ã¡nh giÃ¡: {review_count}. Tá»•ng sá»‘ trang cáº§n láº¥y: {total_pages}")
    
    # 3. Láº¶P TUáº¦N Tá»° QUA Táº¤T Cáº¢ CÃC TRANG
    for page in range(1, total_pages + 1):
        
        # Náº¿u lÃ  page 1, sá»­ dá»¥ng dá»¯ liá»‡u Ä‘Ã£ cÃ³ (tá»‘i Æ°u hÃ³a nhá»)
        if page == 1:
            current_page_data = data
        else:
            # Request cho cÃ¡c trang tiáº¿p theo
            params["page"] = page
            current_page_data = {}
            
            # Logic retry cho cÃ¡c trang tiáº¿p theo
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
        
        # 4. TRÃCH XUáº¤T Ná»˜I DUNG ÄÃNH GIÃ (Logic gá»‘c)
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
    """Analyze Tiki reviews â†’ compute sentiment score â†’ update DB."""
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
    # Láº¥y danh má»¥c (breadcrumbs)
    # ---------------------------
    breadcrumbs = product_data.get("breadcrumbs", []) or []

    # âœ… Loáº¡i bá» breadcrumb lÃ  sáº£n pháº©m (category_id == 0 hoáº·c url chá»©a product_id)
    breadcrumbs = [
        b for b in breadcrumbs
        if (isinstance(b.get("category_id"), int) and b.get("category_id") > 0)
        and str(product_id) not in (b.get("url") or "")
    ]

    category_id = None

    if breadcrumbs:
        # Map cÃ¡c cáº¥p danh má»¥c
        category_dict = {
            "Category_Lv1": breadcrumbs[0].get("name") if len(breadcrumbs) > 0 else None,
            "Category_Lv2": breadcrumbs[1].get("name") if len(breadcrumbs) > 1 else None,
            "Category_Lv3": breadcrumbs[2].get("name") if len(breadcrumbs) > 2 else None,
            "Category_Lv4": breadcrumbs[3].get("name") if len(breadcrumbs) > 3 else None,
            "Category_Lv5": breadcrumbs[4].get("name") if len(breadcrumbs) > 4 else None,
        }

        from ..crud import categories as cat_crud
        from ..services.category_service import create_or_get_category

        # Chuáº©n hÃ³a Category_Path vÃ  Level_Count
        category_data = cat_crud.ensure_path_fields({
            "Source": "Tiki",
            **category_dict
        })

        # Kiá»ƒm tra trÃ¹ng (Source + Category_Path)
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
    # Láº¥y Rating, Review Count vÃ  Positive Percent tá»« API riÃªng
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

            # âœ… TÃ­nh Positive Percent náº¿u cÃ³ dá»¯ liá»‡u sao
            stars = review_json.get("stars", {})
            if stars:
                # Cáº¥u trÃºc má»—i sao: {"count": int, "percent": int}
                total = sum([v.get("count", 0) for v in stars.values()])
                if total > 0:
                    positive = stars.get("5", {}).get("count", 0) + stars.get("4", {}).get("count", 0)
                    positive_percent = round((positive / total) * 100, 2)
                    print(f"[DEBUG] Positive_Percent = {positive_percent}% ({positive}/{total})")
    except Exception :
        pass

    # ---------------------------
    # Láº¥y Origin vÃ  Brand Country trong attributes
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
    # Láº¥y vÃ  lÃ m sáº¡ch mÃ´ táº£ sáº£n pháº©m
    # ---------------------------
    from bs4 import BeautifulSoup
    description_clean = None
    try:
        html_desc = product_data.get("description", "")
        if html_desc:
            soup = BeautifulSoup(html_desc, "html.parser")
            # Loáº¡i bá» HTML, tÃ¡ch dÃ²ng giá»¯a cÃ¡c Ä‘oáº¡n
            description_clean = soup.get_text(separator="\n").strip()
            # XÃ³a dÃ²ng trá»‘ng vÃ  kÃ½ tá»± thá»«a
            description_clean = "\n".join(
                [line.strip() for line in description_clean.splitlines() if line.strip()]
            )
    except Exception as e:
        print(f"[Warning] KhÃ´ng láº¥y Ä‘Æ°á»£c mÃ´ táº£: {e}")

    # ---------------------------
    # Chuáº©n bá»‹ dá»¯ liá»‡u lÆ°u vÃ o DB
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
    print("[DEBUG] LÆ°u sáº£n pháº©m:", product_record)
    if not product:
        return None

    # ---------------------------
    # Cáº­p nháº­t sentiment (phÃ¢n tÃ­ch cáº£m xÃºc)
    # ---------------------------
    update_sentiment_from_tiki_reviews(db, product.External_ID)

    return {
        "Product_ID": product.Product_ID,
        "Product_Name": product.Product_Name,
        "Brand": product.Brand,
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
from ..services import gemini_image_service


# ---------------------- Láº¥y danh sÃ¡ch 10 ID ----------------------
def get_tiki_ids(keyword: str, page: int = 1, limit: int = 10) -> List[int]:
    """
    Gá»i API Tiki Ä‘á»ƒ láº¥y danh sÃ¡ch external_id sáº£n pháº©m theo tá»« khÃ³a.
    Loáº¡i bá» quáº£ng cÃ¡o (advertisement hoáº·c Tiki Ads).
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
    âœ… Pipeline tá»‘i Æ°u:
    - TÃ¬m danh sÃ¡ch product_id tá»« Tiki.
    - Bá» qua cÃ¡c sáº£n pháº©m Ä‘Ã£ tá»“n táº¡i trong DB (theo External_ID).
    - CÃ o song song (multi-thread) Ä‘á»ƒ tÄƒng tá»‘c.
    - Tráº£ vá» danh sÃ¡ch káº¿t quáº£ sáº£n pháº©m (cÃ³ hoáº·c Ä‘Ã£ tá»“n táº¡i).
    """

    if not keyword:
        print("[TIKI] âš ï¸ Thiáº¿u tá»« khÃ³a tÃ¬m kiáº¿m.")
        return []

    print(f"\nðŸ” [TIKI] Báº¯t Ä‘áº§u tÃ¬m kiáº¿m tá»« khÃ³a: '{keyword}'")

    # ----------------------
    # B1: Láº¥y danh sÃ¡ch ID tá»« API Tiki
    # ----------------------
    ids = get_tiki_ids(keyword, page=1, limit=limit)
    if not ids:
        print(f"[TIKI] âŒ KhÃ´ng tÃ¬m tháº¥y sáº£n pháº©m nÃ o cho '{keyword}'")
        return []

    print(f"[TIKI] âœ… Láº¥y Ä‘Æ°á»£c {len(ids)} ID sáº£n pháº©m tá»« API.")

    results: List[Dict[str, Any]] = []

    # ----------------------
    # B2: Kiá»ƒm tra trÃ¹ng trong DB (External_ID)
    # ----------------------
    existing_ids = set(product_crud.get_all_external_ids(db))
    new_ids = [pid for pid in ids if pid not in existing_ids]

    if not new_ids:
        print("[TIKI] ðŸ” Táº¥t cáº£ sáº£n pháº©m Ä‘Ã£ tá»“n táº¡i trong DB. Bá» qua cÃ o.")
    else:
        print(f"[TIKI] âš™ï¸ CÃ³ {len(new_ids)} sáº£n pháº©m má»›i cáº§n cÃ o.")

    # ----------------------
    # B3: Láº¥y dá»¯ liá»‡u sáº£n pháº©m Ä‘Ã£ cÃ³ sáºµn (Ä‘á»ƒ tráº£ vá» ngay)
    # ----------------------
    for pid in existing_ids.intersection(ids):
        existing = product_crud.get_by_external_id(db, pid)
        if existing:
            results.append({
                "Product_ID": existing.Product_ID,
                "Product_Name": existing.Product_Name,
                "Brand": existing.Brand,
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
    # B4: CÃ o sáº£n pháº©m má»›i song song (tá»‘i Ä‘a 5 luá»“ng)
    # ----------------------
    from ..database import SessionLocal

    def crawl_single(pid: int):
        local_db = SessionLocal()
        try:
            print(f"[TIKI] â³ CÃ o sáº£n pháº©m ID {pid}...")
            result = crawl_and_save_tiki_product(local_db, pid)
            local_db.commit()
            return result
        except Exception as e:
            print(f"[TIKI] âš ï¸ Lá»—i khi cÃ o ID {pid}: {e}")
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
    print(f"[TIKI] âœ… HoÃ n táº¥t cÃ o {len(new_ids)} sáº£n pháº©m má»›i trong {duration}s.")

    # ----------------------
    # B5: Tráº£ káº¿t quáº£ tá»•ng há»£p
    # ----------------------
    print(f"[TIKI] ðŸ”Ž Tá»•ng cá»™ng {len(results)} sáº£n pháº©m Ä‘Æ°á»£c tráº£ vá».")
    return results



# ---------------------- 3 pipeline Ä‘áº§u vÃ o ----------------------
def crawl_by_barcode(db: Session, barcode: str) -> List[Dict[str, Any]]:
    """
    Pipeline cho route /products/barcode/{barcode}.
    1ï¸âƒ£ DÃ¹ng iCheck Ä‘á»ƒ tra tÃªn sáº£n pháº©m.
    2ï¸âƒ£ Náº¿u cÃ³ tÃªn â†’ tÃ¬m trÃªn Tiki (hÃ m crawl_by_text sáº½ tá»± lÆ°u DB).
    3ï¸âƒ£ Náº¿u iCheck hoáº·c Tiki Ä‘á»u khÃ´ng ra â†’ tráº£ thÃ´ng bÃ¡o hÆ°á»›ng dáº«n nháº­p tÃªn.
    """
    if not barcode:
        return [{"message": "Thiáº¿u mÃ£ váº¡ch Ä‘á»ƒ tra cá»©u."}]

    # 1ï¸âƒ£ Gá»i iCheck
    # Use safe wrapper to avoid nested event loop issues in async contexts
    product_name = icheck_service.lookup_product_name_safe(barcode)

    if product_name:
        print(f"[iCheck] âœ… TÃ¬m tháº¥y tÃªn sáº£n pháº©m: {product_name}")

        # 2ï¸âƒ£ Gá»i Tiki theo tÃªn (crawl_by_text Ä‘Ã£ tá»± lÆ°u DB)
        results = crawl_by_text(db, product_name)
        if results:
            return results

        # Tiki khÃ´ng cÃ³ káº¿t quáº£
        print(f"[Tiki] âš ï¸ KhÃ´ng tÃ¬m tháº¥y sáº£n pháº©m nÃ o cho '{product_name}'.")
        return [{
            "message": f"KhÃ´ng tÃ¬m tháº¥y sáº£n pháº©m tÆ°Æ¡ng á»©ng vá»›i mÃ£ váº¡ch {barcode}. "
                       "Vui lÃ²ng nháº­p tÃªn sáº£n pháº©m Ä‘á»ƒ tiáº¿p tá»¥c tÃ¬m kiáº¿m."
        }]

    # 3ï¸âƒ£ iCheck khÃ´ng cÃ³ dá»¯ liá»‡u
    print(f"[iCheck] âŒ KhÃ´ng tÃ¬m tháº¥y dá»¯ liá»‡u cho barcode {barcode}.")
    return [{
        "message": f"KhÃ´ng tÃ¬m tháº¥y sáº£n pháº©m cho mÃ£ váº¡ch {barcode}. "
                   "Vui lÃ²ng nháº­p tÃªn sáº£n pháº©m Ä‘á»ƒ tÃ¬m kiáº¿m."
    }]



def crawl_by_image(db: Session, image_path: str) -> List[Dict[str, Any]]:
    """
    Pipeline cho route /products/scan/image.
    1) Dùng OCR để trích xuất text từ ảnh.
    2) Kết hợp Gemini để nhận dạng tên sản phẩm rõ hơn.
    3) Thử tìm sản phẩm theo từng gợi ý (ưu tiên Gemini trước).
    """
    if not image_path:
        return [{"message": "Thiếu đường dẫn ảnh để quét."}]

    ocr_text = (ocr_service.extract_text_from_image(image_path) or "").strip()
    if ocr_text:
        print(f"[OCR] ✅ Nhận diện được text: '{ocr_text}'")
    else:
        print("[OCR] ⚠️ Không nhận diện được chữ trong ảnh.")

    gemini_name = gemini_image_service.identify_product_name_from_image(image_path)
    if gemini_name:
        gemini_name = gemini_name.strip()
        if gemini_name:
            print(f"[Gemini] ✅ Gợi ý tên sản phẩm: '{gemini_name}'")
        else:
            gemini_name = None

    candidates = []
    for keyword in [gemini_name, ocr_text]:
        keyword = (keyword or "").strip()
        if keyword and keyword.lower() not in [c.lower() for c in candidates]:
            candidates.append(keyword)

    if not candidates:
        return [{"message": "Không nhận diện được nội dung trong ảnh. Vui lòng chụp rõ hơn hoặc nhập tên sản phẩm."}]

    for keyword in candidates:
        print(f"[Search] Tìm sản phẩm với từ khóa: {keyword}")
        results = crawl_by_text(db, keyword)
        if results:
            return results

    print(f"[Tiki] ⚠️ Không tìm thấy sản phẩm nào cho các gợi ý: {candidates}")
    joined = "', '".join(candidates)
    return [{"message": f"Không tìm thấy sản phẩm tương ứng với '{joined}'. Vui lòng nhập tên sản phẩm để tiếp tục tìm kiếm."}]

def crawl_by_text(db: Session, text: str) -> List[Dict[str, Any]]:
    """
    Pipeline cho route /search?q=...
    1. DÃ¹ng text lÃ m tá»« khÃ³a tÃ¬m kiáº¿m Tiki.
    """
    if not text:
        return []
    print(f"[Search] TÃ¬m sáº£n pháº©m vá»›i tá»« khÃ³a: {text}")
    return search_and_crawl_tiki_products_fast(db, keyword=text)


# =============================
# New async-first search crawler
# =============================

async def asearch_and_crawl_tiki_products(db: Session, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
    if not keyword:
        return []

    ids = await aget_tiki_ids(keyword, page=1, limit=limit)
    if not ids:
        return []

    # Existing products in DB
    results: List[Dict[str, Any]] = []
    try:
        existing_ids = set(product_crud.get_all_external_ids(db))
    except Exception:
        existing_ids = set()

    for pid in existing_ids.intersection(ids):
        try:
            existing = product_crud.get_by_external_id(db, pid)
            if existing:
                results.append({
                    "Product_ID": existing.Product_ID,
                    "Product_Name": existing.Product_Name,
                    "Brand": existing.Brand,
                    "Image_URL": existing.Image_URL,
                    "Price": existing.Price,
                    "Category_ID": existing.Category_ID,
                    "Avg_Rating": existing.Avg_Rating,
                    "Review_Count": existing.Review_Count,
                    "Positive_Percent": existing.Positive_Percent,
                    "Origin": existing.Origin,
                    "Brand_country": existing.Brand_country,
                })
        except Exception:
            continue

    new_ids = [pid for pid in ids if pid not in existing_ids]
    if not new_ids:
        return results

    from ..database import SessionLocal
    connector = aiohttp.TCPConnector(limit=50)
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        sem = asyncio.Semaphore(32)

        async def process_new_id(pid: int) -> Optional[Dict[str, Any]]:
            async with sem:
                details_coro = aget_product_detail(pid, session=session)
                summary_coro = aget_reviews_summary(pid, session=session)
                reviews_sample_coro = aget_product_reviews(pid, limit=50, retry=1, max_pages=2)
                details, summary, reviews_sample = await asyncio.gather(details_coro, summary_coro, reviews_sample_coro)
                if not details:
                    return None

                # Breadcrumbs -> category chain
                breadcrumbs = (details.get("breadcrumbs") or [])
                breadcrumbs = [
                    b for b in breadcrumbs
                    if (isinstance(b.get("category_id"), int) and b.get("category_id") > 0)
                    and str(pid) not in (b.get("url") or "")
                ]

                category_dict = {
                    "Category_Lv1": breadcrumbs[0].get("name") if len(breadcrumbs) > 0 else None,
                    "Category_Lv2": breadcrumbs[1].get("name") if len(breadcrumbs) > 1 else None,
                    "Category_Lv3": breadcrumbs[2].get("name") if len(breadcrumbs) > 2 else None,
                    "Category_Lv4": breadcrumbs[3].get("name") if len(breadcrumbs) > 3 else None,
                    "Category_Lv5": breadcrumbs[4].get("name") if len(breadcrumbs) > 4 else None,
                }

                # Origin & Brand country from specifications
                origin, brand_country = None, None
                try:
                    specs = details.get("specifications", [])
                    for block in specs:
                        for attr in block.get("attributes", []):
                            if attr.get("code") == "origin":
                                origin = attr.get("value")
                            elif attr.get("code") == "brand_country":
                                brand_country = attr.get("value")
                except Exception:
                    pass

                # Clean description text
                description_clean = None
                try:
                    from bs4 import BeautifulSoup
                    html_desc = details.get("description", "")
                    if html_desc:
                        soup = BeautifulSoup(html_desc, "html.parser")
                        description_clean = soup.get_text(separator="\n").strip()
                        description_clean = "\n".join([line.strip() for line in description_clean.splitlines() if line.strip()])
                except Exception:
                    description_clean = None

                product_record = {
                    "External_ID": details.get("id"),
                    "Product_Name": details.get("name"),
                    "Brand": (details.get("brand") or {}).get("name"),
                    "Category_ID": None,  # fill after creating category
                    "Image_URL": details.get("thumbnail_url"),
                    "Product_URL": f"https://tiki.vn/{details.get('url_path')}",
                    "Price": details.get("price"),
                    "Brand_country": brand_country,
                    "Origin": origin,
                    "Avg_Rating": summary.get("rating_average"),
                    "Review_Count": summary.get("reviews_count"),
                    "Positive_Percent": summary.get("positive_percent"),
                    "Source": "Tiki",
                    "Description": description_clean,
                }

                def save_worker() -> Optional[Dict[str, Any]]:
                    local_db = SessionLocal()
                    try:
                        category_id = None
                        try:
                            if any(category_dict.values()):
                                cat = create_or_get_category(local_db, source="Tiki", category_data=category_dict)
                                category_id = cat.Category_ID
                        except Exception:
                            category_id = None

                        product_record["Category_ID"] = category_id
                        product = product_crud.create_or_update_by_external_id(local_db, product_record)
                        local_db.commit()

                        try:
                            if reviews_sample:
                                update_sentiment_with_comments(local_db, int(product.External_ID), reviews_sample)
                                local_db.commit()
                            else:
                                # fallback to full fetch path
                                update_sentiment_from_tiki_reviews(local_db, int(product.External_ID))
                                local_db.commit()
                        except Exception:
                            local_db.rollback()

                        return {
                            "Product_ID": product.Product_ID,
                            "Product_Name": product.Product_Name,
                            "Brand": product.Brand,
                            "Image_URL": product.Image_URL,
                            "Price": product.Price,
                            "Category_ID": product.Category_ID,
                            "Avg_Rating": product_record.get("Avg_Rating"),
                            "Review_Count": product_record.get("Review_Count"),
                            "Positive_Percent": product_record.get("Positive_Percent"),
                            "Origin": product_record.get("Origin"),
                            "Brand_country": product_record.get("Brand_country"),
                        }
                    except Exception as e:
                        local_db.rollback()
                        print(f"[TIKI] Error saving product {pid}: {e}")
                        return None
                    finally:
                        local_db.close()

                return await asyncio.to_thread(save_worker)

        tasks = [process_new_id(pid) for pid in new_ids]
        created = await asyncio.gather(*tasks)
        for item in created:
            if item:
                results.append(item)

    return results


def search_and_crawl_tiki_products_fast(db: Session, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Sync wrapper around the async search pipeline.

    When invoked from an async FastAPI endpoint (i.e. while an event loop is
    already running in this thread), creating/running another loop is
    forbidden. In that case we delegate the work to a temporary thread that owns
    its own event loop and SQLAlchemy session. Otherwise we run the coroutine
    directly.
    """

    async def _runner(session: Session) -> List[Dict[str, Any]]:
        return await asearch_and_crawl_tiki_products(session, keyword, limit=limit)

    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            from ..database import SessionLocal

            def _thread_job() -> List[Dict[str, Any]]:
                local_db = SessionLocal()
                try:
                    return asyncio.run(_runner(local_db))
                finally:
                    local_db.close()

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_thread_job)
                return future.result()
    except RuntimeError:
        # No running loop in this thread; fall through to direct execution.
        pass

    return asyncio.run(_runner(db))


# Override earlier definition with async-powered implementation
def update_sentiment_from_tiki_reviews(db: Session, product_id: int) -> Optional[float]:
    try:
        comments = asyncio.run(aget_product_reviews(product_id, limit=20))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            comments = loop.run_until_complete(aget_product_reviews(product_id, limit=20))
        finally:
            loop.close()

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


# Also override get_product_reviews to use async implementation
def get_product_reviews(
    product_id: int,
    limit: int = 20,
    retry: int = 2,
) -> List[str]:
    try:
        return asyncio.run(aget_product_reviews(product_id, limit=limit, retry=retry))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(aget_product_reviews(product_id, limit=limit, retry=retry))
        finally:
            loop.close()


def update_sentiment_with_comments(db: Session, product_id: int, comments: List[str]) -> Optional[float]:
    comments = [c for c in (comments or []) if c]
    if not comments:
        product_crud.update_sentiment(db, product_id, score=None, label=None)
        return None
    scores = [analyze_comment(c) for c in comments]
    if not scores:
        product_crud.update_sentiment(db, product_id, score=None, label=None)
        return None
    avg_score = sum(scores) / len(scores)
    label = label_sentiment(avg_score)
    product_crud.update_sentiment(db, product_id, score=avg_score, label=label)
    return avg_score


# Override get_tiki_ids to async wrapper to remove requests dependency
def get_tiki_ids(keyword: str, page: int = 1, limit: int = 10) -> List[int]:
    try:
        return asyncio.run(aget_tiki_ids(keyword, page=page, limit=limit))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(aget_tiki_ids(keyword, page=page, limit=limit))
        finally:
            loop.close()

from __future__ import annotations
from typing import Optional
import re
import requests
from bs4 import BeautifulSoup


def lookup_product_name(barcode: str) -> Optional[str]:
    """
    Tra cứu tên sản phẩm từ iCheck.vn bằng Requests + BeautifulSoup.
    Nếu phát hiện tên là 'KHÁM PHÁ THÊM' hoặc rác, return None ngay.
    """
    barcode = str(barcode or '').strip()
    if not re.fullmatch(r"\d{6,14}", barcode):
        return None

    url = f"https://icheck.vn/san-pham/{barcode}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }

    try:
        resp = requests.get(url, headers=headers, timeout=8.0)
        if resp.status_code != 200:
            print(f"[iCheck] ❌ Request failed ({resp.status_code}) for {barcode}")
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # Ưu tiên thẻ meta og:title
        og_tag = soup.find("meta", attrs={"property": "og:title"})
        if og_tag and og_tag.get("content"):
            og_title = og_tag["content"].strip()
            if og_title and og_title.upper() == "KHÁM PHÁ THÊM":
                print(f"[iCheck] ⚠️ Invalid title 'KHÁM PHÁ THÊM' → return None")
                return None
            if "icheck" in og_title.lower() or "sản phẩm" in og_title.lower():
                print(f"[iCheck] ⚠️ Generic title '{og_title}' → return None")
                return None
            print(f"[iCheck] ✅ Found via og:title → {og_title}")
            return og_title

        # Thử các selector phổ biến khác
        for selector in ["h1", "h2", "div.product-name"]:
            tag = soup.select_one(selector)
            if tag:
                name = tag.get_text(strip=True)
                if not name:
                    continue
                # Check invalid cases
                if name.upper() == "KHÁM PHÁ THÊM":
                    print(f"[iCheck] ⚠️ Invalid name 'KHÁM PHÁ THÊM' → return None")
                    return None
                if "icheck" in name.lower() or "sản phẩm" in name.lower():
                    print(f"[iCheck] ⚠️ Generic name '{name}' → return None")
                    return None
                print(f"[iCheck] ✅ Found via selector '{selector}' → {name}")
                return name

        # Nếu không có gì khớp
        print(f"[iCheck] ❌ No valid product name for {barcode}")
        return None

    except requests.RequestException as e:
        print(f"[iCheck] ❌ Connection error: {e}")
        return None

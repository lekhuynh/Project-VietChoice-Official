import os
import json
import re
from typing import Any, Dict, Optional
import requests
from app.config import settings

GEMINI_API_KEY = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"

def _clean_query(text: str) -> str:
    s = text.strip().lower()
    # Remove courtesy/filler phrases and generic words
    s = re.sub(r"\b(cho\s*(tôi|toi|mình|minh|em|anh|chị|chi|bạn|ban))\b", " ", s)
    s = re.sub(r"\b(tôi|toi|mình|minh|em|anh|chị|chi|bạn|ban|tui|tao|tớ|to)\b", " ", s)
    s = re.sub(r"\b(xem|tìm|tim|mua|giúp|giup|cần|can|muốn|muon|xài|xai)\b", " ", s)
    s = re.sub(r"\b(sản\s*phẩm|san\s*pham|sp)\b", " ", s)
    s = re.sub(r"\b(giá\s*rẻ)\b", " ", s)
    # Normalize common composed tokens
    s = s.replace("promax", "pro max").replace("pro-max", "pro max")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _normalize_product_name(name: str) -> str:
    s = name.strip().lower()
    s = s.replace("promax", "pro max").replace("pro-max", "pro max")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _parse_json_safely(text: str) -> Optional[Dict[str, Any]]:
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.startswith("json"):
            t = t[4:].strip()
    start = t.find("{")
    end = t.rfind("}")
    if start != -1 and end != -1 and end >= start:
        fragment = t[start : end + 1]
        try:
            return json.loads(fragment)
        except Exception:
            return None
    return None


def parse_search_intent(message: str) -> Dict[str, Any]:
    prompt = f"""
    Nhiệm vụ: phân tích một câu chat tiếng Việt để trích xuất truy vấn tìm sản phẩm. Trả về JSON hợp lệ DUY NHẤT, không bao gồm giải thích hay markdown.

    Yêu cầu:
    - Loại bỏ hư từ (ví dụ: "cho tôi xem", "tìm", "giúp", "mua", "giá rẻ").
    - Đặt tên sản phẩm ngắn gọn vào product_name (ví dụ: "dầu gội Thorakao", "iphone 15 pro max").
    - Nếu câu có thương hiệu, điền vào brand (ví dụ: "Thorakao", "Apple").
    - Nếu có gợi ý về giá ("dưới 200k", "khoảng 100 nghìn", "giá rẻ"), điền max_price là số (VND).
    - Nếu có đề cập Việt Nam/Việt, đặt is_vietnam_brand phù hợp.

    Cấu trúc JSON:
    {{
      "intent": "search",
      "product_name": "<string>",
      "brand": "<string | null>",
      "max_price": <number | null>,
      "origin": "<string | null>",
      "is_vietnam_brand": <true|false>
    }}

    Ví dụ:
    Input: "Cho tôi xem dầu gội Thorakao giá rẻ"
    Output: {{
      "intent": "search",
      "product_name": "dầu gội Thorakao",
      "brand": "Thorakao",
      "max_price": 100000,
      "origin": null,
      "is_vietnam_brand": true
    }}

    Câu người dùng: "{message}"
    """

    if not GEMINI_API_KEY:
        cleaned = _clean_query(message)
        return {"intent": "search", "product_name": _normalize_product_name(cleaned or message)}

    headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}
    data = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "response_mime_type": "application/json",
        },
    }

    try:
        res = requests.post(GEMINI_URL, headers=headers, json=data, timeout=15)
        if res.status_code != 200:
            cleaned = _clean_query(message)
            return {"intent": "search", "product_name": _normalize_product_name(cleaned or message)}

        body = res.json()
        candidates = body.get("candidates") or []
        text = ""
        if candidates:
            parts = (candidates[0].get("content") or {}).get("parts") or []
            text = "".join([(p.get("text") or "") for p in parts])
        if not text:
            cleaned = _clean_query(message)
            return {"intent": "search", "product_name": _normalize_product_name(cleaned or message)}

        parsed = _parse_json_safely(text) or {}
        if not isinstance(parsed, dict) or not parsed.get("product_name"):
            cleaned = _clean_query(message)
            return {"intent": "search", "product_name": _normalize_product_name(cleaned or message)}

        # Clean and normalize product name further to eliminate residual fillers
        pn = _normalize_product_name(_clean_query(str(parsed.get("product_name") or "").strip()))
        out: Dict[str, Any] = {
            "intent": "search",
            "product_name": pn or _normalize_product_name(_clean_query(message)),
            "brand": (parsed.get("brand") or None),
            "origin": (parsed.get("origin") or None),
            "is_vietnam_brand": bool(parsed.get("is_vietnam_brand")) if parsed.get("is_vietnam_brand") is not None else False,
            "max_price": None,
        }
        mp = parsed.get("max_price")
        if isinstance(mp, (int, float)):
            out["max_price"] = int(mp)
        elif isinstance(mp, str):
            s = mp.lower().strip()
            m = re.search(r"([0-9]+(?:[\.,][0-9]+)?)", s)
            if m:
                val = m.group(1).replace(".", "").replace(",", "")
                try:
                    n = float(val)
                    if "k" in s or "nghìn" in s or "ngan" in s or "ngàn" in s:
                        n *= 1000
                    if "tr" in s or "triệu" in s or "trieu" in s:
                        n *= 1_000_000
                    out["max_price"] = int(n)
                except Exception:
                    pass

        return out
    except Exception:
        cleaned = _clean_query(message)
        return {"intent": "search", "product_name": _normalize_product_name(cleaned or message)}

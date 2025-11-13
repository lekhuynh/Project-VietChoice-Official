from __future__ import annotations
import base64
import json
import os
from typing import Optional

import requests

from app.config import settings


GEMINI_API_KEY = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
# Reuse the same model family used by chat_intent_service
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"


def _parse_json_safely(text: str) -> Optional[dict]:
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


def _guess_mime_type(path: str) -> str:
    lower = (path or "").lower()
    if lower.endswith(".jpg") or lower.endswith(".jpeg"):
        return "image/jpeg"
    if lower.endswith(".webp"):
        return "image/webp"
    if lower.endswith(".gif"):
        return "image/gif"
    # default
    return "image/png"


def identify_product_name_from_image(image_path: str) -> Optional[str]:
    """
    Use Gemini to identify the product name from a product photo.
    Returns a normalized product name, or None if not identifiable.
    """
    if not image_path or not os.path.exists(image_path):
        return None
    if not GEMINI_API_KEY:
        return None

    try:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return None

    prompt = (
        "Bạn là trợ lý nhận dạng sản phẩm từ ảnh. Hãy nhìn vào ảnh bao bì/nhãn "
        "và trích xuất tên sản phẩm gọn nhất có thể (bao gồm thương hiệu nếu xuất hiện).\n"
        "Chỉ trả về JSON hợp lệ, không kèm giải thích hay markdown. Nếu không chắc chắn, để chuỗi rỗng.\n\n"
        "Cấu trúc JSON:\n{\n  \"product_name\": \"<string>\"\n}"
    )

    headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}
    data = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": _guess_mime_type(image_path),
                            "data": b64,
                        }
                    },
                    {"text": prompt},
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "response_mime_type": "application/json",
        },
    }

    try:
        res = requests.post(GEMINI_URL, headers=headers, json=data, timeout=20)
        if res.status_code != 200:
            return None
        body = res.json()
        candidates = body.get("candidates") or []
        text = ""
        if candidates:
            parts = (candidates[0].get("content") or {}).get("parts") or []
            text = "".join([(p.get("text") or "") for p in parts])
        if not text:
            return None
        parsed = _parse_json_safely(text) or {}
        name = str(parsed.get("product_name") or "").strip()
        return name or None
    except Exception:
        return None


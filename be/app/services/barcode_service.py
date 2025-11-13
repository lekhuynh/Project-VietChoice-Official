from typing import List
import re
import cv2
import numpy as np
from PIL import Image
from pyzbar.pyzbar import decode as zbar_decode

def _unique(seq):
    out = []
    seen = set()
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def _normalize_code(raw: str):
    """Lấy số, bỏ ký tự rác"""
    code = re.sub(r"\D+", "", raw)
    return code if 6 <= len(code) <= 32 else None

def _try_decode(pil_img):
    try:
        results = zbar_decode(pil_img)
        codes = []
        for r in results:
            raw = r.data.decode(errors="ignore")
            norm = _normalize_code(raw)
            if norm:
                codes.append(norm)
        return codes
    except:
        return []

def decode_barcodes(image_path: str) -> List[str]:
    """
    VIP Barcode Engine – Tối ưu cho ảnh mờ, lệch, nhỏ:
    - OpenCV preprocessing mạnh
    - Multi-scale
    - Multi-rotation
    - Adaptive threshold
    - CLAHE contrast enhancement
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            print("[Barcode] ❌ Cannot read image")
            return []

        # Convert → grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    except Exception as e:
        print("[Barcode] ❌ OpenCV error:", e)
        return []

    attempts = []

    # 1) Gốc
    attempts.append(gray)

    # 2) CLAHE boost
    clahe = cv2.createCLAHE(clipLimit=3.5, tileGridSize=(8, 8))
    attempts.append(clahe.apply(gray))

    # 3) Sharpen
    kernel = np.array([[0,-1,0], [-1,5,-1], [0,-1,0]])
    attempts.append(cv2.filter2D(gray, -1, kernel))

    # 4) Gaussian blur + sharpen combo
    blur = cv2.GaussianBlur(gray, (3,3), 0)
    sharp = cv2.addWeighted(gray, 1.6, blur, -0.6, 0)
    attempts.append(sharp)

    # 5) Adaptive threshold (mạnh nhất cho barcode mờ)
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 8
    )
    attempts.append(thresh)

    # 6) Canny + Morph close
    edges = cv2.Canny(gray, 80, 200)
    kernel_rect = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel_rect)
    attempts.append(closed)

    # 7) Multi-scale zoom
    for scale in [1.4, 1.8, 2.2]:
        scaled = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        attempts.append(scaled)

    # 8) Rotation combos
    rotations = [0, 90, 180, 270]
    for angle in rotations:
        rot = cv2.rotate(gray, {
            0: cv2.ROTATE_90_CLOCKWISE,
            90: cv2.ROTATE_180,
            180: cv2.ROTATE_90_COUNTERCLOCKWISE,
            270: None
        }.get(angle, None)) if angle != 270 else cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE)
        attempts.append(rot)

    detected = []

    for idx, a in enumerate(attempts):
        try:
            pil = Image.fromarray(a)
            codes = _try_decode(pil)

            if codes:
                for c in codes:
                    if c not in detected:
                        detected.append(c)
                # break ngay vì pyzbar đọc được rồi
                break

        except Exception as e:
            print("[Barcode] ⚠ Decode error:", e)

    print(f"[Barcode] 🔥 VIP Detected codes: {detected}")
    return _unique(detected)

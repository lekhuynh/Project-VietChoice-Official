from typing import Optional

def preprocess_image(image_path: str):
    """
    Tiền xử lý ảnh cơ bản cho OCR:
    - Chuyển grayscale
    - Làm mịn nhiễu
    """
    try:
        from PIL import Image, ImageFilter

        img = Image.open(image_path)
        img = img.convert("L")  # grayscale
        img = img.filter(ImageFilter.MedianFilter())
        return img
    except Exception as e:
        print(f"[OCR] ⚠️ Lỗi khi mở ảnh hoặc preprocess: {e}")
        return None


def extract_text_from_image(image_path: str) -> str:
    """
    Trích xuất chữ từ ảnh bằng pytesseract.
    - Nếu lỗi hoặc không có text → trả chuỗi rỗng.
    """
    try:
        import pytesseract
        from PIL import Image

        # ⚙️ Cấu hình Tesseract trên Windows (chỉ cần nếu chưa set env)
        import platform

        # Chỉ set đường dẫn trên Windows
        if platform.system() == "Windows":
            pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


        # 1️⃣ Tiền xử lý ảnh
        img = preprocess_image(image_path)
        if img is None:
            img = Image.open(image_path)

        # 2️⃣ OCR
        text = pytesseract.image_to_string(img, lang="vie+eng")

        # 3️⃣ Làm sạch kết quả
        clean_text = (text or "").strip()
        print(f"[OCR] ✅ Nhận diện được text: '{clean_text}'")
        import re
        result = clean_text.replace("\n", " ")
        result = re.sub(r"[^a-zA-ZÀ-ỹ0-9\s]", "", result)
        result = re.sub(r"\s+", " ", result).strip()
        return result
    except Exception as e:
        print(f"[OCR] ❌ Lỗi OCR: {e}")
        return ""



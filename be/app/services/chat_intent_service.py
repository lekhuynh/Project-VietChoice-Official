import json
import os
import google.generativeai as genai
from typing import Dict, Any
from app.config import settings

# 1. IN RA LOG XEM CÓ KEY CHƯA (Che bớt key để bảo mật)
raw_key = settings.API_KEY_GEMINI or os.getenv("API_KEY_GEMINI")
if raw_key:
    print(f"🔑 [DEBUG] API Key loaded: {raw_key[:5]}...{raw_key[-3:]}")
    genai.configure(api_key=raw_key)
else:
    print("❌ [DEBUG] API KEY IS MISSING/NONE! Code will skip Gemini.")

async def parse_search_intent(message: str) -> Dict[str, Any]:
    print(f"⚡ [DEBUG] Starting intent analysis for: '{message}'")

    # CHECK 1: Kiểm tra Key
    if not raw_key:
        print("⚠️ [DEBUG] No API Key -> FALLBACK MODE ACTIVATED")
        return {"is_searching": True, "product_name": message}

    model = genai.GenerativeModel(
        'gemini-2.5-flash',
        generation_config={"temperature": 0.1, "response_mime_type": "application/json"}
    )

    prompt = f"""
    Bạn là Trợ lý AI chuyên lọc ý định và trích xuất từ khóa cho sàn thương mại điện tử.
    User input: "{message}"

    NHIỆM VỤ:
    1. Xác định: User đang muốn tìm mua sản phẩm cụ thể (Search) hay chỉ đang trò chuyện (Chat)?
    2. Xử lý:
       - Nếu Search: Trích xuất TÊN SẢN PHẨM + THÔNG SỐ KỸ THUẬT (Product Name). Loại bỏ mọi từ thừa.
       - Nếu Chat: Trả lời lịch sự nhưng từ chối các câu hỏi không liên quan đến mua sắm.

    --- QUY TẮC 1: PHÂN LOẠI Ý ĐỊNH (INTENT) ---
    - is_searching = TRUE: Khi câu chứa tên một vật thể, hàng hóa cụ thể (iPhone, Áo thun, Nồi cơm...).
    - is_searching = FALSE: 
      + Câu chào hỏi xã giao ("Hi", "Chào shop", "Khỏe không").
      + Câu hỏi kiến thức ngoài lề ("Ronaldo sinh năm nào", "1+1 bằng mấy").
      + Ý định mua hàng nhưng KHÔNG CÓ tên sản phẩm ("Tôi muốn tìm kiếm", "Có bán gì không", "Tư vấn giúp").

    --- QUY TẮC 2: LÀM SẠCH TỪ KHÓA (CLEANING) ---
    - CHỈ GIỮ LẠI: Tên thương hiệu, Tên Model, Thông số (GB, RAM, Size, Màu), Loại sản phẩm.
    - CẮT BỎ NGAY:
      + Động từ: "mua", "bán", "tìm", "lấy", "xem", "cần".
      + Tính từ cảm xúc/đánh giá: "rẻ", "đẹp", "bền", "tốt", "xịn", "ngon", "chính hãng", "uy tín", "hot".
      + Yếu tố giá/địa điểm: "giá rẻ", "khuyến mãi", "hà nội", "tphcm", "trả góp".
      + Từ hư: "cái", "chiếc", "dòng", "những", "cho tôi".

    --- QUY TẮC 3: GIỚI HẠN PHẠM VI TRẢ LỜI (SCOPE) ---
    - Nếu user hỏi chuyện ngoài lề (bóng đá, thời tiết, tình yêu...), hãy trả lời: "Mình chỉ chuyên về sản phẩm thôi ạ, bạn cần tìm món gì không?".
    - Nếu user chào hỏi, hãy chào lại thân thiện và mời mua hàng.

    Output JSON Schema:
    {{
        "is_searching": boolean,
        "product_name": string | null,
        "reply": string | null
    }}
    """

    try:
        # CHECK 2: Bắt đầu gọi Google
        print("⏳ [DEBUG] Calling Gemini API...")
        response = await model.generate_content_async(prompt)
        
        # CHECK 3: In ra raw text mà Google trả về (để debug)
        # print(f"📩 [DEBUG] Gemini Raw Response: {response.text}")

        payload = json.loads(response.text)
        
        # Lấy dữ liệu và xử lý an toàn (tránh lỗi NoneType)
        is_searching = payload.get("is_searching", False)
        product_name = str(payload.get("product_name") or "").strip() # Ép về chuỗi và xóa khoảng trắng
        reply = payload.get("reply")
        print(f"🧠 [DEBUG] Parsed -> Search: {is_searching} | Product: '{product_name}' | Reply: '{reply}'")

        # --- LOGIC QUAN TRỌNG: CHẶN TỪ KHÓA RỖNG ---
        # Chỉ trả về search KHI VÀ CHỈ KHI có tên sản phẩm thực sự (> 1 ký tự)
        if is_searching and len(product_name) > 1:
            return {
                "is_searching": True, 
                "product_name": product_name
            }
        
        # Các trường hợp còn lại:
        # 1. AI bảo là Chat (is_searching = False)
        # 2. AI bảo là Search nhưng product_name rỗng (User nhập "tôi muốn tìm")
        # -> Đều chuyển về Chat hết.
        final_msg = reply if reply else "Bạn muốn tìm món gì cụ thể? Nhập tên giúp mình nha."
        
        return {
            "is_searching": False, 
            "message": final_msg
        }

    except Exception as e:
        # CHECK 4: Nếu lỗi Exception (Mất mạng, Google lỗi, Hết quota...)
        print(f"🔥 [DEBUG] EXCEPTION HAPPENED: {str(e)}")
        
        # Trả về tin nhắn báo lỗi nhẹ nhàng, không crash app
        return {
            "is_searching": False, 
            "message": "Hệ thống AI đang bận xíu, bạn thử lại sau nha."
        }
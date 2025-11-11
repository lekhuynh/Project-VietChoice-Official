
# ===============================================================
#  AUTO UPDATE PRODUCTS SERVICE
# ---------------------------------------------------------------
# 🎯 Mục tiêu:
# - Tự động cập nhật lại dữ liệu sản phẩm trong bảng Products
# - Lấy dữ liệu mới nhất từ API Tiki cho mỗi sản phẩm.
# - Nếu sản phẩm không còn tồn tại trên Tiki → đánh dấu Is_Active = False.
# - Cập nhật đồng thời:
#     • Price
#     • Avg_Rating  
#     • Review_Count
#     • Positive_Percent
# ---------------------------------------------------------------
# 🔁 Quy trình xử lý:
# 1️⃣ Lấy toàn bộ danh sách sản phẩm từ bảng Products.
# 2️⃣ Với mỗi sản phẩm:
#     - Gọi API https://tiki.vn/api/v2/products/{External_ID}
#     - Nếu không trả dữ liệu hoặc lỗi → gán Is_Active = False.
#     - Nếu có dữ liệu:
#           Cập nhật các trường chi tiết sản phẩm mới nhất.
#           Cập nhật điểm rating, review_count, positive_percent.
#     - Gọi get_product_reviews(product_id) để lấy comment mới.
#     - Gọi update_product_sentiment(db, product_id)
#           → cập nhật lại Sentiment_Score & Sentiment_Label.
# 3️⃣ Ghi log số sản phẩm được cập nhật, số sản phẩm bị vô hiệu hóa.
# 4️⃣ Cập nhật Updated_At = NOW() để đánh dấu lần cập nhật cuối.
# 5️⃣ Commit sau mỗi sản phẩm (hoặc batch commit nếu muốn tối ưu).
#
# ---------------------------------------------------------------
# ⚙️ Các hàm liên quan cần dùng:
# - get_product_detail(product_id)       → crawler_tiki.py
# - get_product_reviews(product_id)      → crawler_tiki.py
# - update_product_sentiment(db, id)     → sentiment_analysis.py
#
# ---------------------------------------------------------------
# 📦 Dữ liệu lưu lại trong DB:
# | Cột                | Nguồn dữ liệu          |
# |--------------------|------------------------|
# | Price              | API Tiki               |
# | Avg_Rating         | API Tiki               |
# | Review_Count       | API Tiki               |
# | Positive_Percent   | API Tiki               |
# | Sentiment_Score    | Sentiment Analysis     |
# | Sentiment_Label    | Sentiment Analysis     |
# | Updated_At         | Local UTC time         |
# | Is_Active          | False nếu bị xóa       |
#
# ---------------------------------------------------------------
# 🧠 Mở rộng gợi ý:
# - Thêm retry logic khi gọi API (thử lại 3 lần nếu lỗi).
# - Thêm scheduler chạy tự động mỗi 24h hoặc mỗi tuần.
# - Ghi log chi tiết sản phẩm nào bị xóa / cập nhật thành công.
# ---------------------------------------------------------------
# 📂 File liên quan:
# - app/services/auto_update_service.py      (file chính)
# - app/services/crawler_tiki.py             (gọi API Tiki)
# - app/services/sentiment_analysis.py       (phân tích cảm xúc)
# - app/routes/admin_routes.py               (endpoint thủ công)
# ---------------------------------------------------------------
# ✅ Endpoint gợi ý:
# POST /admin/force-update-products
#    → Thực hiện cập nhật toàn bộ sản phẩm trong DB.
# ---------------------------------------------------------------
# ===============================================================

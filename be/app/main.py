from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path

try:
    from .database import init_db  # type: ignore
    from .routes import auth as auth_router  # type: ignore
    from .core.security import AuthMiddleware  # type: ignore
except Exception:  # pragma: no cover
    # If executed from be/app (e.g., `uvicorn main:app`), ensure parent (be) is on sys.path
    parent_dir = Path(__file__).resolve().parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    from app.database import init_db  # type: ignore
    from app.routes import auth as auth_router  # type: ignore
    from app.core.security import AuthMiddleware  # type: ignore

from fastapi.middleware.cors import CORSMiddleware



app = FastAPI(title="VietChoice API")

origins = [
   "http://localhost:5173"
]   

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---------------------------------------
# HÀM TỰ ĐỘNG CHẠY NỀN
# ---------------------------------------
# from apscheduler.schedulers.background import BackgroundScheduler
# from app.database import SessionLocal
# from app.services.auto_update_service import auto_update_sentiment

# def scheduled_auto_update():
#     db = SessionLocal()
#     try:
#         result = auto_update_sentiment(db)
#         print(f"[AUTO SENTIMENT] {result}")
#     except Exception as e:
#         print(f"[AUTO SENTIMENT ERROR] {e}")
#     finally:
#         db.close()

# ---------------------------------------
# KHỞI TẠO SCHEDULER
# ---------------------------------------
# scheduler = BackgroundScheduler()
# scheduler.add_job(scheduled_auto_update, "interval", hours=24)  # chạy mỗi 24h
# scheduler.start()

@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/", tags=["Health"])
def read_root() -> JSONResponse:
    return JSONResponse({"message": "VietChoice API is running", "docs_url": "/docs"})


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)

# Register routers
app.include_router(auth_router.router)

# Thêm middleware xác thực
app.add_middleware(AuthMiddleware)

from app.routes import admin
app.include_router(admin.router)

from app.routes import users
app.include_router(users.router)

# Routes của phần sản phẩm
from app.routes import products
app.include_router(products.router)

# Routes của phần lịch sử tìm kiếm và lịch sử xem
from app.routes import search_history
app.include_router(search_history.router)

# Routes của phần thêm sản phẩm yêu thích
from app.routes import favorite
app.include_router(favorite.router)

#Routes của phần đánh giá sản phẩm của user
from app.routes import reviews as user_reviews
app.include_router(user_reviews.router)

# from app.routes import categories
# app.include_router(categories.router)
from app.routes.categories import router as category_router  # ✅ dùng nếu có router định nghĩa đúng
app.include_router(category_router)

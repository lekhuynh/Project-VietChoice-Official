from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

try:
    from .database import init_db  # type: ignore
    from .routes import auth as auth_router  # type: ignore
    from .core.security import AuthMiddleware  # type: ignore
    from .routes import admin, users, products, search_history, favorite, reviews as user_reviews  # type: ignore
    from .routes.categories import router as category_router  # type: ignore
except Exception:  # pragma: no cover
    parent_dir = Path(__file__).resolve().parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    from app.database import init_db  # type: ignore
    from app.routes import auth as auth_router  # type: ignore
    from app.core.security import AuthMiddleware  # type: ignore
    from app.routes import admin, users, products, search_history, favorite, reviews as user_reviews  # type: ignore
    from app.routes.categories import router as category_router  # type: ignore

# app = FastAPI(title="VietChoice API")

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
] 

from app.database import SessionLocal
# from app.routes import admin as admin_router
from app.routes import favorite
from app.routes import products
from app.routes import reviews as user_reviews
from app.routes import search_history
from app.routes import users
from app.routes.categories import router as category_router
from app.services.auto_update_service import auto_update_products
from app.services.system_flag_service import is_auto_update_enabled

app = FastAPI(title="VietChoice API")

# origins = ["http://localhost:5173"]

# CORS FIRST
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth AFTER
app.add_middleware(AuthMiddleware)

  
# ============================================================
# Scheduler
# ============================================================

scheduler: Optional[AsyncIOScheduler] = None


from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timezone

from app.database import SessionLocal
from app.services.auto_update_service import auto_update_products
from app.services.system_flag_service import is_auto_update_enabled


def start_scheduler() -> None:
    print("[Scheduler] Initializing...")
    scheduler = AsyncIOScheduler()

    @scheduler.scheduled_job(
        "interval",
        minutes=5,          # PROD: 10 phút 1 lần (hoặc hours=1 cho nhẹ)
        max_instances=1,     # đảm bảo không overlap
        coalesce=True,       # nếu lỡ trễ thì gộp 1 lần
    )
    def scheduled_update() -> None:
        print(f"[Scheduler] Job triggered at {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
        db = SessionLocal()
        try:
            if is_auto_update_enabled(db):
                print("[Scheduler] Auto update ENABLED -> running job")
                stats = auto_update_products(
                    db,
                    older_than_hours=8,
                    limit=None,   # hoặc 200/500 nếu muốn batch nhỏ dần
                    workers=8,
                )
                print(
                    f"[Scheduler] Done: total={stats['total']}, "
                    f"updated={stats['updated']}, "
                    f"deactivated={stats['deactivated']}, "
                    f"errors={stats['errors']}"
                )
            else:
                print("[Scheduler] Auto update DISABLED -> skip job")
        except Exception as exc:  # noqa: BLE001
            print(f"[Scheduler] Job failed: {exc}")
        finally:
            db.close()

    scheduler.start()
    print("[Scheduler] Started successfully!")



# ============================================================
# Startup
# ============================================================

@app.on_event("startup")
def on_startup() -> None:
    print("[App] Startup event triggered")
    init_db()
    print("[App] DB initialized")
    start_scheduler()


# ============================================================
# Basic routes
# ============================================================

@app.get("/", tags=["Health"])
def read_root() -> JSONResponse:
    return JSONResponse({"message": "VietChoice API is running", "docs_url": "/docs"})

@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


# Routers
app.include_router(auth_router.router)
app.add_middleware(AuthMiddleware)

from app.routes import admin
app.include_router(admin.router)

from app.routes import users
app.include_router(users.router)
app.include_router(products.router)
app.include_router(search_history.router)
app.include_router(favorite.router)
app.include_router(user_reviews.router)
app.include_router(category_router)
app.include_router(admin.router)  # ✅ Admin router đã được đăng ký

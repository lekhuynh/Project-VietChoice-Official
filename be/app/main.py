from __future__ import annotations

import asyncio
import sys
import threading
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ============================================================
# Dynamic import (for Docker / local Dev)
# ============================================================

try:
    from .database import init_db, SessionLocal
    from .core.security import AuthMiddleware
    from .routes import auth as auth_router
    from .routes import admin, users, products, search_history, favorite, reviews as user_reviews
    from .routes.categories import router as category_router
    from .tasks.auto_update_batch import enqueue_auto_update_chunked
    from .services.system_flag_service import is_auto_update_enabled
except Exception:
    parent_dir = Path(__file__).resolve().parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

    from app.database import init_db, SessionLocal
    from app.core.security import AuthMiddleware
    from app.routes import auth as auth_router
    from app.routes import admin, users, products, search_history, favorite, reviews as user_reviews
    from app.routes.categories import router as category_router
    from app.tasks.auto_update_batch import enqueue_auto_update_chunked
    from app.services.system_flag_service import is_auto_update_enabled


# ============================================================
# FastAPI App
# ============================================================

app = FastAPI(title="VietChoice API")


# ============================================================
# CORS — MUST BE FIRST
# ============================================================

ALLOW_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://project-viet-choice.vercel.app",
    "https://project-viet-choice-jzl1.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Auth middleware AFTER CORS
# ============================================================

app.add_middleware(AuthMiddleware)


# ============================================================
# Scheduler
# ============================================================

scheduler: Optional[AsyncIOScheduler] = None


def start_scheduler() -> None:
    print("[Scheduler] Initializing...")
    # Create a dedicated event loop for the scheduler thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    scheduler = AsyncIOScheduler(event_loop=loop)

    @scheduler.scheduled_job(
        "interval",
        minutes=5,
        max_instances=1,
        coalesce=True,
    )
    def scheduled_update() -> None:
        print(f"[Scheduler] Job triggered at {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
        db = SessionLocal()
        try:
            if is_auto_update_enabled(db):
                print("[Scheduler] Auto update ENABLED -> running job")
                job_id = enqueue_auto_update_chunked(
                    chunk_size=50,
                    older_than_hours=24,
                    workers=4,
                )
                print(f"[Scheduler] Enqueued auto-update job id={job_id}")
            else:
                print("[Scheduler] Auto update DISABLED -> skip job")
        except Exception as exc:
            print(f"[Scheduler] Job failed: {exc}")
        finally:
            db.close()

    scheduler.start()
    print("[Scheduler] Started successfully!")
    try:
        loop.run_forever()
    finally:
        loop.stop()


def start_scheduler_in_background() -> None:
    """Spin up the APScheduler on a separate daemon thread to avoid blocking the API event loop."""
    t = threading.Thread(target=start_scheduler, daemon=True)
    t.start()


# ============================================================
# Startup
# ============================================================

@app.on_event("startup")
def on_startup() -> None:
    print("[App] Startup event triggered")
    init_db()
    print("[App] DB initialized")
    start_scheduler_in_background()


# ============================================================
# Basic Routes
# ============================================================

@app.get("/", tags=["Health"])
def read_root() -> JSONResponse:
    return JSONResponse({"message": "VietChoice API is running", "docs_url": "/docs"})


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


# ============================================================
# Routers
# ============================================================

app.include_router(auth_router.router)
app.include_router(admin.router)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(search_history.router)
app.include_router(favorite.router)
app.include_router(user_reviews.router)
app.include_router(category_router)
# ============================================================

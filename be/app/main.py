from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path

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

app = FastAPI(title="VietChoice API")

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
] 

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
app.include_router(users.router)
app.include_router(products.router)
app.include_router(search_history.router)
app.include_router(favorite.router)
app.include_router(user_reviews.router)
app.include_router(category_router)
app.include_router(admin.router)  # ✅ Admin router đã được đăng ký
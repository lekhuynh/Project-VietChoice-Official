## VietChoice — Copilot Instructions for AI Agents

**Project Overview:** E-commerce product comparison & review platform. Backend: FastAPI + SQL Server. Frontend: Vite + React + TypeScript.

### Repo Structure

- **`be/`** — Python FastAPI backend. Runs on port 8000.
- **`frontend/`** — TypeScript React + Vite. Runs on port 5173 (dev).
- Entry points: `be/app/main.py` and `frontend/src/index.tsx`.

### How to Run (Dev)

```powershell
# Backend (from be/ folder):
cd be
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (from frontend/ folder):
cd frontend
npm install
npm run dev
```

Critical: run `uvicorn` from `be/` — the code has a sys.path fallback in `main.py` to handle imports correctly.

### Database & Config

- Settings loaded from `be/.env` via `app/config.py` using Pydantic `BaseSettings`.
- SQL Server connection:
  - Env keys: `db_driver`, `db_server`, `db_name`, `db_user`, `db_password`
  - URL built in `settings.SQLSERVER_URL` property (handles URL encoding, driver, TLS).
  - Session management: `SessionLocal()` from `database.py`, accessed via `get_db()` dependency.
  - Tables auto-created on startup via `init_db()` → imports all models from `app/models/__init__.py` and calls `Base.metadata.create_all()`.

### Architecture Patterns

**Request Flow:**
1. Client calls frontend API (e.g., `POST /products/search`).
2. Frontend hits backend at `http://localhost:8000` (configurable via `VITE_API_BASE_URL`).
3. Route handler in `app/routes/<domain>.py` (e.g., `products.py`) receives request.
4. Handler validates request schema (Pydantic), then calls service.
5. Service contains business logic; calls CRUD helpers; returns response.
6. Route returns JSON via `response_formatter.py` utility.

**Layers:**
- **Routes** (`be/app/routes/*.py`): FastAPI APIRouter. Each file exposes `router` object. Register in `main.py` via `app.include_router(router)`. Use dependencies for auth/validation.
- **Services** (`be/app/services/*.py`): Business logic. Called by routes. Examples: `product_service.py`, `user_service.py`, `review_service.py`. Prefers "create or update" patterns for idempotency.
- **CRUD** (`be/app/crud/*.py`): DB helpers. Query, insert, update, delete. Examples: `products.py` (get by external ID, upsert), `users.py`, `favorites.py`.
- **Models** (`be/app/models/*.py`): SQLAlchemy ORM. Auto-sync to DB. Example: `Users` has relationships to `Search_History`, `Favorites`, `User_Reviews`, `Product_Views`.
- **Schemas** (`be/app/schemas/*.py`): Pydantic request/response shapes. Convert DB models → API responses. Example: `UserCreate`, `ProductDetail`, `UserProfile`.

**Example: Add a new endpoint:**
```python
# 1. Create route: be/app/routes/my_feature.py
from fastapi import APIRouter
from ..services import my_service
router = APIRouter(prefix="/my_feature", tags=["Feature"])

@router.get("/list")
def list_features(db = Depends(get_db)):
    return my_service.get_all(db)

# 2. Register in be/app/main.py
from app.routes import my_feature
app.include_router(my_feature.router)
```

### Authentication & Authorization

- **JWT-based:** Tokens in `Authorization: Bearer <token>` header or `ACCESS_TOKEN_COOKIE_NAME` cookie.
- **Middleware:** `AuthMiddleware` (in `core/security.py`) extracts token and stashes `user_id` in `request.state`.
- **Dependencies:**
  - `get_current_user` — requires valid JWT, returns `Users` object. Raises 401 if missing/invalid.
  - `require_admin` — wraps `get_current_user`, checks `Role == "admin"`, raises 403 if not.
- **Passwords:** Hashed with `passlib`; verified in auth service.
- **Tokens:** Generated/validated in `app/auth/jwt_handler.py`. Payload includes `sub` (user_id) and `exp`.

Example protected route:
```python
@router.put("/admin/{user_id}/role", dependencies=[Depends(require_admin)])
def update_user_role(user_id: int, role: str, db: Session = Depends(get_db)):
    return user_service.change_user_role(db, user_id, role)
```

### Frontend (Vite + React + TypeScript)

- **API layer:** `src/api/*.ts` — each file groups related fetches. Example: `products.ts` has `fetchTopRatedProducts()`, `searchProducts()`, etc.
- **Shared types:** `src/types/index.ts` defines `Product`, `Review`, `Message`, `Conversation`. Data from API (snake_case) should be mapped to camelCase before UI rendering.
- **Components:** Organized by domain: `src/components/products/`, `src/components/auth/`, `src/components/scanner/`, `src/components/chat/`, `src/components/layout/`.
- **Pages:** `src/pages/*.tsx` — route-level components: `Home`, `Products`, `ProductDetail`, `Auth`, `Admin`.
- **Config:** `src/config.ts` defines `API_BASE_URL` (reads `VITE_API_BASE_URL` env var, defaults to `http://localhost:8000`).

**Scripts:**
- `npm run dev` — Vite dev server, hot reload.
- `npm run build` — TypeScript typecheck + Vite bundle.
- `npm run typecheck` — `tsc --noEmit`.
- `npm run lint` — ESLint; use `--fix` to auto-correct.
- `npm run validate` — runs typecheck + lint.
- `npm run format` — Prettier on src/ (TypeScript, CSS, Markdown).

### CORS & Cross-Origin

- Backend CORS allows `http://localhost:5173` only (frontend dev origin).
- Change in `app/main.py` if frontend runs elsewhere.

### Testing & Quick Checks

- `be/test_conn.py` — lightweight script to verify SQL Server connectivity.
- No integrated unit test suite; add via Pytest/Vitest as needed.

### Key Dependencies

**Backend (`be/requirements.txt`):**
- FastAPI, Uvicorn — web framework.
- SQLAlchemy — ORM.
- pyodbc — SQL Server driver.
- Pydantic, pydantic-settings — validation, config.
- passlib, python-jose — password hashing, JWT.
- requests, beautifulsoup4 — HTTP, web scraping.
- torch, numpy — ML/ML inference.

**Frontend (`frontend/package.json`):**
- React 18, React Router 6 — UI & routing.
- Vite — build tool.
- TypeScript 5.5 — type safety.
- Tailwind CSS 3.4 — styling.
- html5-qrcode — barcode/QR scanning.
- recharts — charts.
- ESLint, Prettier, Husky — dev tooling.

### Common Edits

1. **Fix DB model:** edit `be/app/models/<entity>.py`, ensure imported in `app/models/__init__.py`, run startup (auto-creates).
2. **Add API endpoint:** create route in `be/app/routes/<domain>.py`, register in `main.py`, define schema in `be/app/schemas/<domain>.py`.
3. **Update frontend UI:** edit React component in `src/components/`, update API call in `src/api/*.ts` if needed, check types in `src/types/index.ts`.
4. **Debug authentication:** check JWT decode in `app/auth/jwt_handler.py`, verify middleware in `app/core/security.py`, confirm token present in request.

### Integration Points

- **Sentiment Analysis & ML:** `sentiment_service.py`, `recommender_service.py` — may invoke external models or crawlers.
- **Web Crawling:** `crawler_tiki_service.py`, `icheck_service.py` — fetch product data from external sources.
- **OCR:** `ocr_service.py` — extract text from images (e.g., price labels).
- **Admin Functions:** `admin_service.py`, `admin.py` route — manage products, users, categories.
- **Caching:** `cache_service.py` — optimize repeated queries (implementation TBD).

---

If unclear on DB schema, auth flow, ML integration, or frontend component structure, ask!

VietChoice Backend (FastAPI)

This backend is scaffolded with a minimal authentication flow (register/login/logout with JWT). Other modules are placeholders for future implementation.

Quick start
- Create and configure `.env` in `be/` (already present).
- Install deps: `pip install -r .\be\requirements.txt`.
- Run dev server: `uvicorn app.main:app --reload` from `be/`.

Structure
- `app/main.py`: FastAPI entrypoint and router registration.
- `app/config.py`: Settings loaded from `.env`.
- `app/database.py`: SQLAlchemy engine/session (SQL Server via pyodbc).
- `app/auth/`: Password hashing and JWT helpers.
- `app/routers/auth.py`: Register/login/logout endpoints.
- Other folders/files are currently empty placeholders.


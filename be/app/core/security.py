from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import settings
from ..database import get_db, SessionLocal
from ..auth.jwt_handler import decode_access_token
from ..models.users import Users
from sqlalchemy.orm import Session


def _extract_token(request: Request) -> Optional[str]:
    """Get JWT from Authorization: Bearer ... or from configured cookie."""
    auth = request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    cookie_name = settings.ACCESS_TOKEN_COOKIE_NAME
    token = request.cookies.get(cookie_name)
    if token:
        return token
    return None


def _get_user_id_from_token(token: str) -> Optional[int]:
    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if sub is None:
            return None
        return int(sub)
    except Exception:
        return None


class AuthMiddleware(BaseHTTPMiddleware):
    """Lightweight middleware: parse JWT (if present) and stash user_id in request.state.

    - Does not enforce auth; use dependencies below for protection.
    - Avoids DB fetch at middleware level by default to keep overhead low.
    """

    async def dispatch(self, request: Request, call_next):

    # Bỏ qua preflight (OPTIONS)
        if request.method == "OPTIONS":
            return await call_next(request)

        token = _extract_token(request)
        if token:
            user_id = _get_user_id_from_token(token)
            if user_id:
                request.state.user_id = user_id

        return await call_next(request)



async def get_current_user(request: Request, db: Session = Depends(get_db)) -> Users:
    """Dependency to fetch the current user from JWT.

    - Reads user_id from request.state if middleware populated it.
    - Otherwise, extracts token again from header/cookie.
    - Raises 401 if missing/invalid.
    """
    user_id: Optional[int] = getattr(request.state, "user_id", None)
    if user_id is None:
        token = _extract_token(request)
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        user_id = _get_user_id_from_token(token)
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(Users).filter(Users.User_ID == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def require_admin(current_user: Users = Depends(get_current_user)) -> Users:
    """Dependency to ensure the current user has admin role."""
    if (current_user.Role or "").lower() != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: admin only")
    return current_user

async def get_optional_user(request: Request, db: Session = Depends(get_db)) -> Optional[Users]:
    """Không bắt buộc đăng nhập. Trả về user nếu token hợp lệ, ngược lại None."""
    try:
        user_id: Optional[int] = getattr(request.state, "user_id", None)
        if not user_id:
            token = _extract_token(request)
            if not token:
                return None
            user_id = _get_user_id_from_token(token)
            if not user_id:
                return None

        user = db.query(Users).filter(Users.User_ID == user_id).first()
        return user
    except Exception:
        return None

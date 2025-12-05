from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.security import get_optional_user

from ..auth.jwt_handler import create_access_token
from ..config import settings
from ..database import get_db
from ..crud import users as users_crud
from ..schemas.users import LoginRequest, TokenResponse, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    existing = users_crud.get_by_email(db, str(user_in.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = users_crud.create_user(
        db,
        email=str(user_in.email),
        name=user_in.name,
        password_plain=user_in.password,
    )

    return UserOut(id=user.User_ID, email=user.User_Email, name=user.User_Name)


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, response: Response, db: Session = Depends(get_db)) -> TokenResponse:
    user = users_crud.authenticate(db, email=str(credentials.email), password_plain=credentials.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token({"sub": str(user.User_ID)}, expires_delta)

    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=access_token,
        max_age=int(expires_delta.total_seconds()),
        httponly=True,
        samesite="none",
        secure=True,
    )


    return TokenResponse(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(response: Response, current_user=Depends(get_optional_user)) -> dict[str, str]:
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    response.delete_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        httponly=True,
        samesite="none",
        secure=True,
    )

    return {"detail": "Logged out"}
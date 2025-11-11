from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional, List

# ===== Base Schema =====   
class UserBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    email: EmailStr
    name: str


class UserCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: EmailStr = Field(..., alias="email")
    name: str = Field(..., min_length=1, max_length=100, alias="name")
    password: str = Field(..., min_length=6, max_length=100, alias="password")

# ===== Update (User Self-Update) =====
class UserUpdate(BaseModel):
    user_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None

class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: int

# schemas/users.py

class UserChangePassword(BaseModel):
    old_password: str = Field(..., min_length=6, max_length=100)
    new_password: str = Field(..., min_length=6, max_length=100)
    confirm_password: str = Field(..., min_length=6, max_length=100)


# ===== For Profile (View Info) =====
class UserProfile(BaseModel):
    user_name: str
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===== Admin: Update Role =====
class AdminUpdateRole(BaseModel):
    role: str = Field(..., pattern="^(user|manager|admin)$")


# ===== Admin: Full Detail =====
class AdminUserOut(UserOut):
    is_active: bool = True


# ===== Admin: List =====
class AdminUserList(BaseModel):
    users: List[AdminUserOut]

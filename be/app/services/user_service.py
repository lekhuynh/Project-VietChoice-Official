from typing import Any, Dict, Optional, Sequence
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..schemas.users import UserUpdate, UserChangePassword

from ..crud import users as users_crud
from ..models.users import Users
from ..auth.hashing import get_password_hash, verify_password


# ============================================================
# USER SELF-SERVICE
# ============================================================
def get_user_profile(db: Session, user_id: int) -> Optional[Users]:
    """Get a single user profile."""
    user = users_crud.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

def update_user_profile(db: Session, user_id: int, update_data: UserUpdate) -> Users:
    """Cập nhật tên, email (không đổi mật khẩu ở đây)."""
    user = users_crud.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if update_data.user_name:
        user.User_Name = update_data.user_name.strip()
    if update_data.email:
        user.User_Email = update_data.email.strip()

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def change_user_password(db: Session, user_id: int, pw_data: UserChangePassword) -> Users:
    """Đổi mật khẩu: yêu cầu nhập mật khẩu cũ, xác nhận mật khẩu mới."""
    user = users_crud.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Kiểm tra mật khẩu cũ
    if not verify_password(pw_data.old_password, user.User_Password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    # Kiểm tra xác nhận mật khẩu
    if pw_data.new_password != pw_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password confirmation does not match",
        )

    # Cập nhật mật khẩu mới
    user.User_Password = get_password_hash(pw_data.new_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# ============================================================
# ADMIN OPERATIONS
# ============================================================
def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> Sequence[Users]:
    """Admin: Get all users (paginated)."""
    return users_crud.get_all_users(db, skip=skip, limit=limit)


def change_user_role(db: Session, user_id: int, role: str) -> Users:
    """Admin: Update user role."""
    user = users_crud.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return users_crud.update_user_role(db, user, new_role=role)


def admin_update_user(db: Session, user_id: int, data: Dict[str, Any]) -> Users:
    """Admin: Update user info (name, email, role)."""
    user = users_crud.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updated = users_crud.admin_update_user(
        db,
        user,
        name=data.get("name"),
        email=data.get("email"),
        role=data.get("role")
    )
    return updated


def delete_user(db: Session, user_id: int) -> Dict[str, str]:
    """Admin: Delete a user."""
    user = users_crud.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    users_crud.delete_user(db, user)
    return {"message": f"User '{user.User_Email}' deleted successfully"}

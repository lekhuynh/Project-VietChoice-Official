from typing import Optional, Sequence
from sqlalchemy.orm import Session
from ..auth.hashing import get_password_hash, verify_password
from ..models.users import Users
from datetime import datetime

def get_by_id(db: Session, user_id: int) -> Optional[Users]:
    """Return user by primary key."""
    return db.query(Users).filter(Users.User_ID == user_id).first()


def get_by_email(db: Session, email: str) -> Optional[Users]:
    """Return user by email."""
    return db.query(Users).filter(Users.User_Email == email).first()


def list_users(db: Session, skip: int = 0, limit: int = 100) -> Sequence[Users]:
    """List users with pagination."""
    return db.query(Users).offset(skip).limit(limit).all()


def create_user(db: Session, *, email: str, name: str, password_plain: str, role: str = "user") -> Users:
    """Create a new user with hashed password."""
    user = Users(
        User_Name=name,
        User_Email=email,
        User_Password=get_password_hash(password_plain),
        Role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, *, email: str, password_plain: str) -> Optional[Users]:
    """Authenticate user credentials; return user or None."""
    user = get_by_email(db, email)
    if not user:
        return None
    if not verify_password(password_plain, user.User_Password):
        return None
    return user


# Convenience aliases to satisfy TODO naming without breaking callers
def get_user_by_email(db: Session, email: str) -> Optional[Users]:
    return get_by_email(db, email)


def get_user_by_id(db: Session, user_id: int) -> Optional[Users]:
    return get_by_id(db, user_id)


def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> Sequence[Users]:
    return list_users(db, skip=skip, limit=limit)


def update_user_role(db: Session, user: Users, *, new_role: str) -> Users:
    """Admin: update role for a user."""
    user.Role = new_role
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: Users) -> None:
    """Admin: delete a user."""
    db.delete(user)
    db.commit()


# ============================================================
# USER UPDATE (SELF)
# ============================================================
def update_user_profile(
    db: Session,
    user: Users,
    *,
    name: Optional[str] = None,
    email: Optional[str] = None,
    password_plain: Optional[str] = None,
) -> Users:
    """User self-update name/email/password."""
    if name:
        user.User_Name = name
    if email:
        user.User_Email = email
    if password_plain:
        user.User_Password = get_password_hash(password_plain)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ============================================================
# ADMIN ACTIONS
# ============================================================
def update_user_role(db: Session, user: Users, *, new_role: str) -> Users:
    """Admin: update role for a user."""
    user.Role = new_role
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def admin_update_user(
    db: Session,
    user: Users,
    *,
    name: Optional[str] = None,
    email: Optional[str] = None,
    role: Optional[str] = None
) -> Users:
    """Admin: update user info (name, email, role)."""
    if name:
        user.User_Name = name
    if email:
        user.User_Email = email
    if role:
        user.Role = role
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: Users) -> None:
    """Admin: delete a user."""
    db.delete(user)
    db.commit()


# ============================================================
# CONVENIENCE ALIASES
# ============================================================
def get_user_by_email(db: Session, email: str) -> Optional[Users]:
    return get_by_email(db, email)


def get_user_by_id(db: Session, user_id: int) -> Optional[Users]:
    return get_by_id(db, user_id)


def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> Sequence[Users]:
    return list_users(db, skip=skip, limit=limit)

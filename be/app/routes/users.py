from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.users import UserChangePassword, UserUpdate
from ..core.security import get_current_user, require_admin
from ..services import user_service

router = APIRouter(prefix="/users_profile", tags=["User Profile"])

# ---- User self ----
@router.get("/me")
def read_my_profile(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return user_service.get_user_profile(db, current_user.User_ID)


@router.put("/update")
def update_my_profile(update_data: UserUpdate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return user_service.update_user_profile(db, current_user.User_ID, update_data)

@router.put("/change-password")
def change_my_password(
    pw_data: UserChangePassword,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ✅ Đổi mật khẩu người dùng hiện tại.
    - Yêu cầu: old_password, new_password, confirm_password
    - Xác thực qua JWT (current_user)
    """
    updated_user = user_service.change_user_password(db, current_user.User_ID, pw_data)
    return {
        "message": "Password updated successfully",
        "user_id": updated_user.User_ID,
        "email": updated_user.User_Email,
    }

# ---- Admin only ----
@router.get("/admin/list", dependencies=[Depends(require_admin)])
def list_all_users(db: Session = Depends(get_db)):
    return user_service.get_all_users(db)


@router.put("/admin/{user_id}/role", dependencies=[Depends(require_admin)])
def update_user_role(user_id: int, role: str, db: Session = Depends(get_db)):
    return user_service.change_user_role(db, user_id, role)


@router.delete("/admin/{user_id}", dependencies=[Depends(require_admin)])
def remove_user(user_id: int, db: Session = Depends(get_db)):
    return user_service.delete_user(db, user_id)

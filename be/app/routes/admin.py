# Tổng hợp các thao tác quản trị hệ thống cho admin.

# Các endpoint:
# 1. GET /admin/dashboard
#    - Thống kê sản phẩm, user, đánh giá, danh mục...
#    - Requires: require_admin

# 2. GET /admin/logs
#    - Xem log hệ thống
#    - Requires: require_admin
# Có thể viết thêm các endpoint khác có trong dự án này

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from app.core.security import require_admin
from app.services.auto_update_service import auto_update_sentiment

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/auto-update-sentiment", dependencies=[Depends(require_admin)])
def run_auto_update(db: Session = Depends(get_db)):
    """
    ⚙️ Admin endpoint: Cập nhật lại sentiment cho sản phẩm cũ hơn 24h.
    """
    result = auto_update_sentiment(db)
    return result

from ..services import user_service
# ---- Ví Dụ ----
@router.get("/admin/list", dependencies=[Depends(require_admin)])
def list_all_users(db: Session = Depends(get_db)):
    return user_service.get_all_users(db)


@router.put("/admin/{user_id}/role", dependencies=[Depends(require_admin)])
def update_user_role(user_id: int, role: str, db: Session = Depends(get_db)):
    return user_service.change_user_role(db, user_id, role)


@router.delete("/admin/{user_id}", dependencies=[Depends(require_admin)])
def remove_user(user_id: int, db: Session = Depends(get_db)):
    return user_service.delete_user(db, user_id)

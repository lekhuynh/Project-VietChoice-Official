from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import require_admin as get_current_admin
from app.database import get_db
from app.services.auto_update_service import auto_update_products
from app.services.system_flag_service import (
    disable_auto_update,
    enable_auto_update,
    get_auto_update_status,
)

router = APIRouter(prefix="/admin", tags=["Admin - Auto Update"])


@router.post("/auto-update/enable")
def enable_auto(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    ok = enable_auto_update(db)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không bật được auto-update flag.",
        )
    return {"message": "Auto update ENABLED", "enabled": True}


@router.post("/auto-update/disable")
def disable_auto(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    ok = disable_auto_update(db)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không tắt được auto-update flag.",
        )
    return {"message": "Auto update DISABLED", "enabled": False}


@router.get("/auto-update/status")
def auto_update_status(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    status_info = get_auto_update_status(db)
    return status_info


@router.post("/auto-update/run-now")
def run_auto_update_now(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    """
    Cho phép admin tự tay chạy 1 batch auto-update (không phụ thuộc scheduler).
    """
    stats = auto_update_products(
        db,
        older_than_hours=0,  # cho test: update luôn
        limit=50,
        workers=4,
    )
    return {"message": "Auto update executed manually.", "stats": stats}

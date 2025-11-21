from __future__ import annotations

from sqlalchemy.orm import Session

from app.crud.system_flags import get_flag, is_flag_enabled, set_flag

AUTO_UPDATE_NAME = "AUTO_UPDATE_ENABLED"


def enable_auto_update(db: Session) -> bool:
    flag = set_flag(db, AUTO_UPDATE_NAME, True)
    return bool(flag.Flag_Value)


def disable_auto_update(db: Session) -> bool:
    flag = set_flag(db, AUTO_UPDATE_NAME, False)
    return bool(flag.Flag_Value)


def is_auto_update_enabled(db: Session) -> bool:
    return is_flag_enabled(db, AUTO_UPDATE_NAME)


def get_auto_update_status(db: Session) -> dict:
    flag = get_flag(db, AUTO_UPDATE_NAME)
    return {
        "flag_name": AUTO_UPDATE_NAME,
        "enabled": bool(flag and flag.Flag_Value),
        "updated_at": getattr(flag, "Updated_At", None),
    }

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models.system_flags import SystemFlags


def get_flag(db: Session, name: str) -> Optional[SystemFlags]:
    return (
        db.query(SystemFlags)
        .filter(SystemFlags.Flag_Name == name)
        .first()
    )


def set_flag(db: Session, name: str, value: bool) -> SystemFlags:
    flag = get_flag(db, name)
    if flag is None:
        flag = SystemFlags(Flag_Name=name, Flag_Value=value)
        db.add(flag)
    else:
        flag.Flag_Value = value
    db.commit()
    db.refresh(flag)
    return flag


def is_flag_enabled(db: Session, name: str) -> bool:
    flag = get_flag(db, name)
    return bool(flag and flag.Flag_Value)

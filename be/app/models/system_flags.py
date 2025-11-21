from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from app.database import Base


class SystemFlags(Base):
    __tablename__ = "System_Flags"

    Flag_ID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Flag_Name = Column(String(100), unique=True, nullable=False, index=True)
    Flag_Value = Column(Boolean, nullable=False, default=False)
    Updated_At = Column(
        DateTime,
        nullable=False,
        server_default=func.sysutcdatetime(),
        onupdate=func.sysutcdatetime(),
    )

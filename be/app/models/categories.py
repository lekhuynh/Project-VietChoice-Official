from sqlalchemy import (
    Column, Integer, Unicode, DateTime, BigInteger, UniqueConstraint, SmallInteger
)
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.sql import func

from ..database import Base


class Categories(Base):
    __tablename__ = "Categories"
    __table_args__ = (
        UniqueConstraint("Source", "Category_Path", name="UQ_Categories_Source_Path"),
    )

    Category_ID = Column(Integer, primary_key=True, index=True)
    Source = Column(Unicode(50), nullable=False)
    Category_Lv1 = Column(Unicode(150))
    Category_Lv2 = Column(Unicode(150))
    Category_Lv3 = Column(Unicode(150))
    Category_Lv4 = Column(Unicode(150))
    Category_Lv5 = Column(Unicode(150))
    Category_Path = Column(Unicode(600), nullable=False)
    Level_Count = Column(SmallInteger)
    Created_At = Column(DateTime, server_default=func.now())
    Updated_At = Column(DateTime, nullable=True)

    # Relationships
    products = relationship("Products", back_populates="category", cascade="all, delete")

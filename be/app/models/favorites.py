from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class Favorites(Base):
    __tablename__ = "Favorites"

    ID = Column(Integer, primary_key=True, index=True)
    User_ID = Column(Integer, ForeignKey("Users.User_ID"), nullable=False)
    Product_ID = Column(Integer, ForeignKey("Products.Product_ID"), nullable=False)
    Created_At = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("Users", back_populates="favorites")
    product = relationship("Products", back_populates="favorites")


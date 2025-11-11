from sqlalchemy import Column, Integer, String, DateTime, UnicodeText
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class Users(Base):
    __tablename__ = "Users"

    User_ID = Column(Integer, primary_key=True, index=True)
    User_Name = Column(UnicodeText)
    User_Email = Column(String(100), unique=True, nullable=False)
    User_Password = Column(String(100), nullable=False)
    Role = Column(String(50), default="user")
    Created_At = Column(DateTime, default=datetime.utcnow)

    # Relationships
    search_history = relationship("Search_History", back_populates="user", cascade="all, delete")
    favorites = relationship("Favorites", back_populates="user", cascade="all, delete")
    user_reviews = relationship("User_Reviews", back_populates="user", cascade="all, delete")
    product_views = relationship("Product_Views", back_populates="user", cascade="all, delete")

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text, UnicodeText
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class User_Reviews(Base):
    __tablename__ = "User_Reviews"

    Review_ID = Column(Integer, primary_key=True, index=True)
    User_ID = Column(Integer, ForeignKey("Users.User_ID"), nullable=False)
    Product_ID = Column(Integer, ForeignKey("Products.Product_ID"), nullable=False)
    Rating = Column(Integer, nullable=False)
    Comment = Column(UnicodeText)
    Created_At = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("Users", back_populates="user_reviews")
    product = relationship("Products", back_populates="user_reviews")


from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text, UnicodeText, func
from sqlalchemy.orm import relationship

from ..database import Base


class User_Reviews(Base):
    __tablename__ = "User_Reviews"

    Review_ID = Column(Integer, primary_key=True, index=True)
    User_ID = Column(Integer, ForeignKey("Users.User_ID"), nullable=False)
    Product_ID = Column(Integer, ForeignKey("Products.Product_ID"), nullable=False)
    Rating = Column(Integer, nullable=False)
    Comment = Column(UnicodeText)
    Created_At = Column(DateTime, server_default=func.sysutcdatetime())

    # Relationships
    user = relationship("Users", back_populates="user_reviews")
    product = relationship("Products", back_populates="user_reviews")


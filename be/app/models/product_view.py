from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class Product_Views(Base):
    __tablename__ = "Product_Views"

    View_ID = Column(Integer, primary_key=True, index=True)
    User_ID = Column(Integer, ForeignKey("Users.User_ID", ondelete="CASCADE"), nullable=False)
    Product_ID = Column(Integer, ForeignKey("Products.Product_ID", ondelete="CASCADE"), nullable=False)
    Viewed_At = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("User_ID", "Product_ID", name="UQ_ProductViews_User_Product"),
    )

    user = relationship("Users", back_populates="product_views")
    product = relationship("Products")

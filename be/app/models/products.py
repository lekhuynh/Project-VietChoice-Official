from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Unicode, UnicodeText,
    BigInteger, DECIMAL, Text, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class Products(Base):
    __tablename__ = "Products"
    __table_args__ = (
        UniqueConstraint("External_ID", name="UQ_Products_ExternalID"),
    )

    Product_ID = Column(Integer, primary_key=True, index=True)
    Source = Column(String(50), default="Tiki")
    External_ID = Column(BigInteger, nullable=True)
    Barcode = Column(String(100))
    Product_Name = Column(Unicode(500), nullable=False)
    Brand = Column(Unicode(255))
    Category_ID = Column(Integer, ForeignKey("Categories.Category_ID", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    Image_URL = Column(String(1000))
    Product_URL = Column(String(1000))
    Price = Column(DECIMAL(18, 2))
    Avg_Rating = Column(Float)
    Review_Count = Column(Integer)
    Positive_Percent = Column(Float)
    Sentiment_Score = Column(Float)
    Sentiment_Label = Column(Unicode(50))
    Brand_country = Column(Unicode(50))
    Origin = Column(Unicode(255))
    Is_Authentic = Column(Boolean, default=True)
    Is_Active = Column(Boolean, default=True)

    Created_At = Column(
        DateTime(timezone=False),
        server_default=func.sysutcdatetime()
    )

    Updated_At = Column(
        DateTime(timezone=False),
        server_default=func.sysutcdatetime(),
        onupdate=func.sysutcdatetime()
    )
    Description = Column(UnicodeText)
    Image_Full_URL = Column(String(1000), nullable=True)

    # Relationships
    category = relationship("Categories", back_populates="products")
    history_links = relationship(
        "Search_History_Products",
        back_populates="product",
        cascade="all, delete",
    )
    favorites = relationship("Favorites", back_populates="product", cascade="all, delete")
    user_reviews = relationship("User_Reviews", back_populates="product", cascade="all, delete")

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from ..database import Base


class Search_History_Products(Base):
    __tablename__ = "Search_History_Products"

    ID = Column(Integer, primary_key=True, index=True)
    History_ID = Column(
        Integer,
        ForeignKey("Search_History.History_ID", ondelete="CASCADE"),
        nullable=False,
    )
    Product_ID = Column(
        Integer,
        ForeignKey("Products.Product_ID"),
        nullable=False,
    )

    # Relationships
    history = relationship("Search_History", back_populates="history_products")
    product = relationship("Products", back_populates="history_links")


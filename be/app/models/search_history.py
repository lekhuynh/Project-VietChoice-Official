from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UnicodeText, func
from sqlalchemy.orm import relationship

from ..database import Base


class Search_History(Base):
    __tablename__ = "Search_History"

    History_ID = Column(Integer, primary_key=True, index=True)
    User_ID = Column(Integer, ForeignKey("Users.User_ID", ondelete="CASCADE"))
    Query = Column(UnicodeText)
    Result_Count = Column(Integer, default=0)
    Created_At = Column(
        DateTime(timezone=True),
        server_default=func.sysutcdatetime()
    )

    # Relationships
    user = relationship("Users", back_populates="search_history")
    history_products = relationship(
        "Search_History_Products",
        back_populates="history",
        cascade="all, delete",
    )

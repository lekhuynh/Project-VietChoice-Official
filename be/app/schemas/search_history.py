from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SearchHistoryBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    user_id: int
    query: str
    result_count: Optional[int] = 0


class SearchHistoryCreate(SearchHistoryBase):
    pass


class SearchHistoryOut(SearchHistoryBase):
    id: int
    created_at: Optional[datetime] = None

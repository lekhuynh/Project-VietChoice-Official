from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class FavoriteBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    user_id: int
    product_id: int


class FavoriteCreate(FavoriteBase):
    pass


class FavoriteOut(FavoriteBase):
    id: int
    created_at: Optional[datetime] = None


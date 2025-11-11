from pydantic import BaseModel, ConfigDict


class SearchHistoryProductBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    history_id: int
    product_id: int


class SearchHistoryProductCreate(SearchHistoryProductBase):
    pass


class SearchHistoryProductOut(SearchHistoryProductBase):
    id: int


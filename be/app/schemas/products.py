from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ProductBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    source: Optional[str] = "Tiki"
    external_id: Optional[int] = None
    barcode: Optional[str] = None
    product_name: str = Field(..., min_length=1, max_length=500)
    brand: Optional[str] = None
    category_id: int
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    price: Optional[Decimal] = None
    avg_rating: Optional[float] = None
    review_count: Optional[int] = None
    positive_percent: Optional[float] = None
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    brand_country: Optional[str] = None
    origin: Optional[str] = None
    is_authentic: Optional[bool] = None
    is_active: Optional[bool] = True
    description: Optional[str] = None

class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    barcode: Optional[str] = None
    product_name: Optional[str] = None
    brand: Optional[str] = None
    category_id: Optional[int] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    price: Optional[Decimal] = None
    avg_rating: Optional[float] = None
    review_count: Optional[int] = None
    positive_percent: Optional[float] = None
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    brand_country: Optional[str] = None
    origin: Optional[str] = None
    is_authentic: Optional[bool] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None   

class ProductOut(ProductBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

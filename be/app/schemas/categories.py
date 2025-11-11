from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

# ===============================
# Schema cơ bản cho danh mục
# ===============================
class CategoryBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    Source: str = Field(..., min_length=1, max_length=50)
    Category_Path: str = Field(..., min_length=1, max_length=600)
    Level_Count: Optional[int] = None
    Category_Lv1: Optional[str] = None
    Category_Lv2: Optional[str] = None
    Category_Lv3: Optional[str] = None
    Category_Lv4: Optional[str] = None
    Category_Lv5: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    Category_Lv1: Optional[str] = None
    Category_Lv2: Optional[str] = None
    Category_Lv3: Optional[str] = None
    Category_Lv4: Optional[str] = None
    Category_Lv5: Optional[str] = None
    Category_Path: Optional[str] = None
    Level_Count: Optional[int] = None


class CategoryOut(CategoryBase):
    Category_ID: int
    Created_At: Optional[datetime] = None
    Updated_At: Optional[datetime] = None


# ===============================
# Schema cho danh mục dạng phẳng (FE hiển thị)
# ===============================
class CategoryFlat(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Category_ID: int
    name: str
    path: str
    level: int

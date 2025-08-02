from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional
from datetime import datetime

class Vendor(BaseModel):
    name: str = Field(..., example="Amazon")
    link: HttpUrl = Field(..., example="https://amazon.in/product")

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    brand: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    image: HttpUrl
    vendors: List[Vendor] = Field(..., min_items=1)
    description: str = Field(..., min_length=10, max_length=1000)
    category: str = Field(..., min_length=1, max_length=100)
    inStock: bool = Field(default=True)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    brand: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[float] = Field(None, gt=0)
    image: Optional[HttpUrl] = None
    vendors: Optional[List[Vendor]] = Field(None, min_items=1)
    description: Optional[str] = Field(None, min_length=10, max_length=1000)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    inStock: Optional[bool] = None

class Product(ProductBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
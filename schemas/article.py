from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AuthorModel(BaseModel):
    id: str
    name: str
    username: str

class ArticleCreate(BaseModel):
    heading: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1)
    youtube_link: Optional[str] = None
    videoUrl: Optional[str] = None  
    
    class Config:
        extra = "ignore"  

class ArticleOut(BaseModel):
    id: str
    heading: str
    body: str
    date: datetime
    author: AuthorModel  
    youtube_link: Optional[str] = None
    
    class Config:
        from_attributes = True
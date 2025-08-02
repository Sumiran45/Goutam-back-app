from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ActivityBase(BaseModel):
    type: str
    title: str
    description: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}
    icon: str = "bell"

class ActivityCreate(ActivityBase):
    pass

class ActivityResponse(ActivityBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True
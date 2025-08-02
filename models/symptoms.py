from datetime import datetime, date
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class SymptomDocument(BaseModel):
    """MongoDB document model for symptoms"""
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str = Field(..., description="User ID (string for MongoDB)")
    date: date = Field(..., description="Date of symptom entry")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Mood tracking
    mood: Optional[str] = Field(None, description="User's mood: irritated, sad, happy, anxious, calm")
    
    # Physical symptoms
    cramps: Optional[str] = Field(None, description="Cramp intensity: none, mild, moderate, strong")
    headache: bool = Field(False, description="Whether user has headache")
    nausea: bool = Field(False, description="Whether user has nausea")
    fatigue: bool = Field(False, description="Whether user has fatigue")
    
    # Flow tracking
    flow_level: Optional[str] = Field(None, description="Flow level: none, light, medium, heavy")
    
    # Lifestyle factors
    sleep_quality: Optional[str] = Field(None, description="Sleep quality: poor, fair, good, excellent")
    food_cravings: Optional[str] = Field(None, description="Food cravings description")
    
    # Additional notes
    notes: Optional[str] = Field(None, description="Additional notes")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "user_id": "user123",
                "date": "2024-01-15",
                "mood": "happy",
                "cramps": "mild",
                "headache": False,
                "nausea": False,
                "fatigue": True,
                "flow_level": "light",
                "sleep_quality": "good",
                "food_cravings": "chocolate",
                "notes": "Feeling good overall"
            }
        }

# Collection name for MongoDB
SYMPTOM_COLLECTION = "symptoms"
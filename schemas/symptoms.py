from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date, datetime
from enum import Enum

# Enums for validation
class MoodEnum(str, Enum):
    HAPPY = "happy"
    SAD = "sad"
    IRRITATED = "irritated"
    ANXIOUS = "anxious"
    CALM = "calm"
    EXCITED = "excited"
    DEPRESSED = "depressed"

class CrampsEnum(str, Enum):
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    STRONG = "strong"

class FlowEnum(str, Enum):
    NONE = "none"
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"

class SleepQualityEnum(str, Enum):
    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"

# Input schemas
class SymptomInput(BaseModel):
    mood: Optional[MoodEnum] = None
    cramps: Optional[CrampsEnum] = None
    headache: Optional[bool] = False
    nausea: Optional[bool] = False
    fatigue: Optional[bool] = False
    flow_level: Optional[FlowEnum] = None
    sleep_quality: Optional[SleepQualityEnum] = None
    food_cravings: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)

    class Config:
        use_enum_values = True

class SymptomCreate(SymptomInput):
    user_id: int
    date: Optional[date] = None  # Defaults to today if not provided

# Response schemas
class SymptomResponse(BaseModel):
    id: int
    user_id: int
    date: date
    created_at: datetime
    mood: Optional[str] = None
    cramps: Optional[str] = None
    headache: bool
    nausea: bool
    fatigue: bool
    flow_level: Optional[str] = None
    sleep_quality: Optional[str] = None
    food_cravings: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class SymptomSummary(BaseModel):
    date: date
    mood: Optional[str] = None
    cramps: Optional[str] = None
    has_headache: bool
    has_nausea: bool
    has_fatigue: bool
    flow_level: Optional[str] = None
    sleep_quality: Optional[str] = None

# Prediction and suggestion schemas
class PredictedSymptom(BaseModel):
    symptom: str
    probability: float = Field(..., ge=0.0, le=1.0)
    confidence: str  # low, medium, high

class Suggestion(BaseModel):
    category: str  # remedy, lifestyle, medical
    title: str
    description: str
    priority: str  # low, medium, high

class PredictionResponse(BaseModel):
    date: date
    predicted_symptoms: List[PredictedSymptom]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    based_on_days: int

class SuggestionResponse(BaseModel):
    suggestions: List[Suggestion]
    based_on_symptoms: List[str]
    date: date

class SymptomAnalytics(BaseModel):
    total_entries: int
    date_range: Dict[str, date]
    most_common_mood: Optional[str] = None
    average_cramp_intensity: Optional[str] = None
    symptom_frequency: Dict[str, int]
    patterns: List[str]
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime, date
from enum import Enum


class MoodType(str, Enum):
    HAPPY = "happy"
    SAD = "sad"
    ANXIOUS = "anxious"
    IRRITABLE = "irritable"
    CALM = "calm"
    ENERGETIC = "energetic"
    TIRED = "tired"
    EMOTIONAL = "emotional"


class PhysicalSymptom(str, Enum):
    CRAMPS = "cramps"
    BLOATING = "bloating"
    HEADACHE = "headache"
    BREAST_TENDERNESS = "breast_tenderness"
    BACK_PAIN = "back_pain"
    NAUSEA = "nausea"
    ACNE = "acne"
    FOOD_CRAVINGS = "food_cravings"


class FlowIntensity(str, Enum):
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"
    SPOTTING = "spotting"


class CycleEntry(BaseModel):
    date: date
    is_period_day: bool = False
    flow_intensity: Optional[FlowIntensity] = None
    moods: List[MoodType] = []
    physical_symptoms: List[PhysicalSymptom] = []
    notes: Optional[str] = None
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    exercise_minutes: Optional[int] = Field(None, ge=0)
    water_intake: Optional[float] = Field(None, ge=0)  # in liters

    @validator('flow_intensity')
    def validate_flow_intensity(cls, v, values):
        if values.get('is_period_day') and not v:
            raise ValueError("Flow intensity required for period days")
        if not values.get('is_period_day') and v:
            raise ValueError("Flow intensity only allowed for period days")
        return v


class CycleEntryCreate(CycleEntry):
    pass


class CycleEntryOut(CycleEntry):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


class CycleStats(BaseModel):
    average_cycle_length: Optional[float] = None
    average_period_length: Optional[float] = None
    last_period_start: Optional[date] = None
    next_predicted_period: Optional[date] = None
    next_predicted_ovulation: Optional[date] = None
    current_cycle_day: Optional[int] = None
    current_phase: Optional[str] = None
    total_cycles_tracked: int = 0


class HormoneLevel(BaseModel):
    estrogen_level: str  # "low", "medium", "high"
    progesterone_level: str  # "low", "medium", "high"
    testosterone_level: str  # "low", "medium", "high"


class CyclePrediction(BaseModel):
    date: date
    cycle_day: int
    phase: str
    predicted_mood: List[str]
    predicted_symptoms: List[str]
    hormone_levels: HormoneLevel
    fertility_status: str  # "low", "medium", "high"


class CycleAnalysis(BaseModel):
    stats: CycleStats
    predictions: List[CyclePrediction]
    mood_patterns: Dict[str, List[str]]
    symptom_patterns: Dict[str, List[str]]

from pydantic import BaseModel, Field, EmailStr, validator
from datetime import datetime, time
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid


class DayOfWeek(str, Enum):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"


class AppointmentStatus(str, Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"
    pending = "pending"


# Update in schemas.py
class ContactInfo(BaseModel):
    address: str
    city: str
    state: str
    pincode: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    lat: Optional[float] = None  # Add latitude
    lng: Optional[float] = None  # Add longitude

    @validator('pincode')
    def validate_pincode(cls, v):
        if len(v) != 6 or not v.isdigit():
            raise ValueError('Pincode must be 6 digits')
        return v


class Availability(BaseModel):
    day: DayOfWeek
    start_time: time
    end_time: time
    is_available: bool = True

    @validator('end_time')
    def validate_times(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v


class Award(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    year: int
    description: Optional[str] = None

    @validator('year')
    def validate_year(cls, v):
        current_year = datetime.now().year
        if v > current_year or v < 1950:
            raise ValueError(f'Year must be between 1950 and {current_year}')
        return v


class Service(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)


class Rating(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_name: str
    rating: float = Field(ge=1, le=5)
    review: Optional[str] = None
    date: datetime = Field(default_factory=datetime.utcnow)
    verified: bool = False


class DoctorStats(BaseModel):
    """Statistics for doctor dashboard"""
    total_patients: int = 0
    appointments_today: int = 0
    appointments_this_week: int = 0
    avg_rating: float = 0.0
    total_reviews: int = 0


class DoctorBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    specialization: str
    qualification: str
    experience_years: int = Field(..., ge=0, le=60)
    hospital_affiliation: str
    about: str = Field(..., min_length=50, max_length=1000)
    consultation_fee: float = Field(..., ge=0)
    contact_info: ContactInfo
    availability: List[Availability]
    services: List[Service]
    awards: List[Award] = []
    languages: List[str] = Field(..., min_items=1)


class DoctorCreate(DoctorBase):
    pass


class DoctorOut(DoctorBase):
    id: str
    rating: float = Field(ge=0, le=5)
    total_ratings: int = Field(ge=0)
    verified: bool = False
    profile_image: Optional[str] = None
    distance_km: Optional[float] = None  # For location-based searches
    created_at: datetime
    updated_at: datetime
    stats: Optional[DoctorStats] = None


class DoctorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    specialization: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: Optional[int] = Field(None, ge=0, le=60)
    hospital_affiliation: Optional[str] = None
    about: Optional[str] = Field(None, min_length=50, max_length=1000)
    consultation_fee: Optional[float] = Field(None, ge=0)
    contact_info: Optional[ContactInfo] = None
    availability: Optional[List[Availability]] = None
    services: Optional[List[Service]] = None
    awards: Optional[List[Award]] = None
    languages: Optional[List[str]] = None
    profile_image: Optional[str] = None


class DoctorSearchParams(BaseModel):
    specialization: Optional[str] = None
    city: Optional[str] = None
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    max_fee: Optional[float] = Field(None, ge=0)
    experience_years: Optional[int] = Field(None, ge=0)
    languages: Optional[List[str]] = None
    available_today: Optional[bool] = None
    verified_only: Optional[bool] = None

class Location(BaseModel):
    address: str
    city: str
    state: str
    pincode: str
    lat: float
    lng: float

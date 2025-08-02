from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class DoctorListItem(BaseModel):
    """Doctor item for list view (matches your UI)"""
    id: str
    name: str
    specialization: str
    experience_years: int
    rating: float
    total_ratings: int
    consultation_fee: int
    distance_km: float
    address: str
    availability: str  # Simplified for UI: "Tue-Sat 11AM-4PM"
    languages: List[str]
    verified: bool
    place_id: str

class DoctorDetail(BaseModel):
    """Detailed doctor info for profile view"""
    id: str
    name: str
    specialization: str
    qualification: str
    experience_years: int
    rating: float
    total_ratings: int
    consultation_fee: int
    about: str
    address: str
    phone: Optional[str]
    website: Optional[str]
    languages: List[str]
    services: List[str]
    awards: List[Dict[str, Any]]
    availability_details: Dict[str, Any]
    reviews: List[Dict[str, Any]]
    verified: bool
    hospital_affiliation: str

class ApiResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool
    data: Any
    message: Optional[str] = None
    count: Optional[int] = None

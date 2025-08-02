from pydantic import BaseModel, Field, EmailStr, validator
from datetime import datetime
from typing import Optional
from enum import Enum
import uuid


class AppointmentType(str, Enum):
    consultation = "consultation"
    follow_up = "follow_up"
    emergency = "emergency"
    online = "online"

class AppointmentStatus(str, Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"
    pending = "pending"

class AppointmentBase(BaseModel):
    patient_name: str = Field(..., min_length=2, max_length=100)
    patient_email: EmailStr
    patient_phone: str = Field(..., pattern=r'^\+?[1-9]\d{1,14}$')
    appointment_date: datetime
    appointment_type: AppointmentType = AppointmentType.consultation
    notes: Optional[str] = Field(None, max_length=500)

    @validator('appointment_date')
    def validate_appointment_date(cls, v):
        if v <= datetime.utcnow():
            raise ValueError('Appointment date must be in the future')
        return v


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentOut(AppointmentBase):
    id: str
    doctor_id: str
    status: AppointmentStatus = AppointmentStatus.scheduled
    created_at: datetime
    updated_at: datetime


class AppointmentUpdate(BaseModel):
    appointment_date: Optional[datetime] = None
    appointment_type: Optional[AppointmentType] = None
    notes: Optional[str] = Field(None, max_length=500)
    status: Optional[AppointmentStatus] = None

from pydantic import BaseModel, EmailStr
from typing import Optional, List

class UserCreate(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str
    confirm_password: str

    # Ensure either email or phone is provided
    def validate_contact(self):
        if not self.email and not self.phone:
            raise ValueError("Either email or phone must be provided.")

class UserOut(BaseModel):
    id: str
    username: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_verified: bool
    phone_verified: bool
    is_active: bool

class UserUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None

class UserLogin(BaseModel):
    email_or_username: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email_or_username: str

class ResetPasswordRequest(BaseModel):
    email_or_username: str
    code: str
    new_password: str
    confirm_password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

class OTPVerifyRequest(BaseModel):
        phone: str
        otp: str

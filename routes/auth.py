from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel, validator, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
from bson.objectid import ObjectId
import random

from schemas.user import UserLogin, ResetPasswordRequest, ForgotPasswordRequest, ChangePasswordRequest
from models.user import user_collection, user_helper, otp_collection
from utils.auth import hash_password, verify_password, create_access_token, get_current_user
from utils.sms import send_verification_sms
from utils.email import (
    send_verification_email,
    send_reset_password_email,
    send_verification_success_email
)
from utils.activity_logger import ActivityLogger, safe_log_activity

router = APIRouter()

class OnboardingData(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    age: Optional[str] = None
    weight: Optional[str] = None
    height: Optional[str] = None
    lastPeriodDate: Optional[str] = None
    cycleLength: Optional[str] = "28"
    periodLength: Optional[str] = "5"
    symptoms: Optional[List[str]] = []
    goals: Optional[List[str]] = []

class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    password: str
    confirm_password: str
    onboarding_data: Optional[OnboardingData] = None

    def validate_contact(self):
        if not self.email and not self.phone:
            raise HTTPException(status_code=400, detail="Either email or phone number is required")

    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise HTTPException(status_code=400, detail="Invalid email format")
        return v

    @validator('phone')
    def validate_phone(cls, v):
        if v and len(v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) < 10:
            raise HTTPException(status_code=400, detail="Invalid phone number")
        return v

# Enhanced user helper function
def user_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "username": user.get("username"),
        "email": user.get("email"),
        "phone": user.get("phone"),
        "is_admin": user.get("is_admin", False),
        "is_verified": user.get("is_verified", False),
        "phone_verified": user.get("phone_verified", False),
        "is_active": user.get("is_active", True),
        "onboarding_completed": user.get("onboarding_completed", False),
        "profile": user.get("profile", {}),
        "createdAt": user.get("createdAt"),
        "updatedAt": user.get("updatedAt"),
        "name": user.get("name"),
        "image": user.get("image"),
        "articles": [str(aid) for aid in user.get("articles", [])],
        "products": user.get("products", [])
    }

# Registration endpoint with onboarding
@router.post("/register")
async def register(user: UserCreate):
    user.validate_contact()

    # Check duplicate by email or phone or username
    query_conditions = []
    if user.email:
        query_conditions.append({"email": user.email})
    if user.phone:
        query_conditions.append({"phone": user.phone})
    query_conditions.append({"username": user.username})

    existing_user = await user_collection.find_one({"$or": query_conditions})
    if existing_user:
        raise HTTPException(status_code=409, detail="User with given username/email/phone already exists.")

    if user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")

    hashed_pw = hash_password(user.password)

    # Prepare onboarding data
    onboarding_data = {}
    if user.onboarding_data:
        onboarding_data = {
            "firstName": user.onboarding_data.firstName,
            "lastName": user.onboarding_data.lastName,
            "age": int(user.onboarding_data.age) if user.onboarding_data.age and user.onboarding_data.age.isdigit() else None,
            "weight": float(user.onboarding_data.weight) if user.onboarding_data.weight and user.onboarding_data.weight.replace('.', '').isdigit() else None,
            "height": float(user.onboarding_data.height) if user.onboarding_data.height and user.onboarding_data.height.replace('.', '').isdigit() else None,
            "lastPeriodDate": user.onboarding_data.lastPeriodDate,
            "cycleLength": int(user.onboarding_data.cycleLength) if user.onboarding_data.cycleLength and user.onboarding_data.cycleLength.isdigit() else 28,
            "periodLength": int(user.onboarding_data.periodLength) if user.onboarding_data.periodLength and user.onboarding_data.periodLength.isdigit() else 5,
            "symptoms": user.onboarding_data.symptoms or [],
            "goals": user.onboarding_data.goals or [],
            "completedAt": datetime.utcnow()
        }

    new_user = {
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "password": hashed_pw,
        "is_admin": False,
        "is_verified": False,
        "phone_verified": False,
        "is_active": True,
        "onboarding_completed": bool(user.onboarding_data),
        "profile": onboarding_data,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }

    result = await user_collection.insert_one(new_user)
    created_user = await user_collection.find_one({"_id": result.inserted_id})

    # Log user registration activity
    await safe_log_activity(
        ActivityLogger.log_user_registration,
        str(created_user["_id"]),
        user.username,
        user.email,
        user.phone
    )

    verification_code = str(random.randint(100000, 999999))

    if user.email:
        await otp_collection.delete_many({"email": user.email, "purpose": "verify"})
        await otp_collection.insert_one({
            "email": user.email,
            "code": verification_code,
            "purpose": "verify",
            "createdAt": datetime.utcnow()
        })
        await send_verification_email(user.email, verification_code)
    elif user.phone:
        await otp_collection.delete_many({"phone": user.phone, "purpose": "verify"})
        await otp_collection.insert_one({
            "phone": user.phone,
            "code": verification_code,
            "purpose": "verify",
            "createdAt": datetime.utcnow()
        })
        await send_verification_sms(user.phone, verification_code)

    return {
        "message": "User registered successfully. Please verify your contact method with the OTP sent.",
        "user": user_helper(created_user),
        "success": True
    }

# Email verification endpoint
@router.post("/verify-email")
async def verify_email(email: EmailStr = Body(...), code: str = Body(...)):
    record = await otp_collection.find_one({"email": email, "code": code, "purpose": "verify"})
    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")

    if datetime.utcnow() - record["createdAt"] > timedelta(minutes=10):
        raise HTTPException(status_code=400, detail="Verification code expired.")

    # Get user details for activity logging
    user = await user_collection.find_one({"email": email})
    
    await user_collection.update_one(
        {"email": email},
        {"$set": {"is_verified": True, "updatedAt": datetime.utcnow()}}
    )
    await otp_collection.delete_many({"email": email, "purpose": "verify"})

    # Log verification activity
    if user:
        await safe_log_activity(
            ActivityLogger.log_user_verification,
            str(user["_id"]),
            user.get("username", "Unknown"),
            "email"
        )

    await send_verification_success_email(email)

    return {"message": "Email verified successfully."}

# Phone verification endpoint
@router.post("/verify-phone")
async def verify_phone(phone: str = Body(...), code: str = Body(...)):
    record = await otp_collection.find_one({"phone": phone, "code": code, "purpose": "verify"})
    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")

    if datetime.utcnow() - record["createdAt"] > timedelta(minutes=10):
        raise HTTPException(status_code=400, detail="Verification code expired.")

    # Get user details for activity logging
    user = await user_collection.find_one({"phone": phone})

    await user_collection.update_one(
        {"phone": phone},
        {"$set": {"phone_verified": True, "updatedAt": datetime.utcnow()}}
    )
    await otp_collection.delete_many({"phone": phone, "purpose": "verify"})

    # Log verification activity
    if user:
        await safe_log_activity(
            ActivityLogger.log_user_verification,
            str(user["_id"]),
            user.get("username", "Unknown"),
            "phone"
        )

    return {"message": "Phone number verified successfully."}

# Login endpoint
@router.post("/login")
async def login(form: UserLogin):
    query_conditions = [
        {"email": form.email_or_username},
        {"username": form.email_or_username},
        {"phone": form.email_or_username}
    ]
    user = await user_collection.find_one({"$or": query_conditions})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(form.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Require verification of either email or phone (at least one verified)
    if not (user.get("is_verified", False) or user.get("phone_verified", False)):
        raise HTTPException(status_code=403, detail="Account not verified")

    token_data = {
        "id": str(user["_id"]),
        "email": user.get("email"),
        "phone": user.get("phone"),
        "username": user["username"],
        "is_admin": user.get("is_admin", False)
    }
    token = create_access_token(token_data)

    return {
        "access_token": token, 
        "token_type": "bearer",
        "user": user_helper(user)
    }

# Forgot password endpoint
@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    email_or_username = request.email_or_username
    query = {
        "$or": [
            {"email": email_or_username},
            {"username": email_or_username}
        ]
    }
    user = await user_collection.find_one(query)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Ensure user has an email for password reset
    if not user.get("email"):
        raise HTTPException(status_code=400, detail="No email associated with this account")

    reset_code = str(random.randint(100000, 999999))
    await otp_collection.delete_many({"email": user["email"], "purpose": "reset"})
    await otp_collection.insert_one({
        "email": user["email"],
        "code": reset_code,
        "createdAt": datetime.utcnow(),
        "purpose": "reset"
    })
    await send_reset_password_email(user["email"], reset_code)

    return {"message": "Password reset code sent to your email."}

# Reset password endpoint
@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")

    otp_record = await otp_collection.find_one({
        "email": request.email_or_username,
        "code": request.code,
        "purpose": "reset"
    })

    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset code.")

    code_expiry_time = otp_record["createdAt"] + timedelta(minutes=10)
    if datetime.utcnow() > code_expiry_time:
        raise HTTPException(status_code=400, detail="Reset code has expired.")

    hashed_pw = hash_password(request.new_password)
    result = await user_collection.update_one(
        {"$or": [{"email": request.email_or_username}, {"username": request.email_or_username}]},
        {"$set": {"password": hashed_pw, "updatedAt": datetime.utcnow()}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found.")

    await otp_collection.delete_many({"email": request.email_or_username, "purpose": "reset"})

    return {"message": "Password reset successful."}

# Change password endpoint
@router.post("/change-password")
async def change_password(request: ChangePasswordRequest, user=Depends(get_current_user)):
    if not verify_password(request.current_password, user["password"]):
        raise HTTPException(status_code=401, detail="Current password is incorrect.")

    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match.")

    hashed_new_password = hash_password(request.new_password)

    result = await user_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"password": hashed_new_password, "updatedAt": datetime.utcnow()}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found or password update failed.")

    return {"message": "Password changed successfully."}

# Update onboarding data endpoint
@router.put("/users/{user_id}/onboarding")
async def update_onboarding(user_id: str, onboarding_data: OnboardingData):
    try:
        user_object_id = ObjectId(user_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    profile_data = {
        "firstName": onboarding_data.firstName,
        "lastName": onboarding_data.lastName,
        "age": int(onboarding_data.age) if onboarding_data.age and onboarding_data.age.isdigit() else None,
        "weight": float(onboarding_data.weight) if onboarding_data.weight and onboarding_data.weight.replace('.', '').isdigit() else None,
        "height": float(onboarding_data.height) if onboarding_data.height and onboarding_data.height.replace('.', '').isdigit() else None,
        "lastPeriodDate": onboarding_data.lastPeriodDate,
        "cycleLength": int(onboarding_data.cycleLength) if onboarding_data.cycleLength and onboarding_data.cycleLength.isdigit() else 28,
        "periodLength": int(onboarding_data.periodLength) if onboarding_data.periodLength and onboarding_data.periodLength.isdigit() else 5,
        "symptoms": onboarding_data.symptoms or [],
        "goals": onboarding_data.goals or [],
        "completedAt": datetime.utcnow()
    }

    result = await user_collection.update_one(
        {"_id": user_object_id},
        {
            "$set": {
                "profile": profile_data,
                "onboarding_completed": True,
                "updatedAt": datetime.utcnow()
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = await user_collection.find_one({"_id": user_object_id})
    return {
        "message": "Onboarding data updated successfully",
        "user": user_helper(updated_user)
    }

# Get current user profile endpoint
@router.get("/profile")
async def get_profile(user=Depends(get_current_user)):
    return {
        "user": user_helper(user)
    }

# Update user profile endpoint
@router.put("/profile")
async def update_profile(user=Depends(get_current_user), profile_data: OnboardingData = Body(...)):
    profile_update = {
        "firstName": profile_data.firstName,
        "lastName": profile_data.lastName,
        "age": int(profile_data.age) if profile_data.age and profile_data.age.isdigit() else None,
        "weight": float(profile_data.weight) if profile_data.weight and profile_data.weight.replace('.', '').isdigit() else None,
        "height": float(profile_data.height) if profile_data.height and profile_data.height.replace('.', '').isdigit() else None,
        "lastPeriodDate": profile_data.lastPeriodDate,
        "cycleLength": int(profile_data.cycleLength) if profile_data.cycleLength and profile_data.cycleLength.isdigit() else 28,
        "periodLength": int(profile_data.periodLength) if profile_data.periodLength and profile_data.periodLength.isdigit() else 5,
        "symptoms": profile_data.symptoms or [],
        "goals": profile_data.goals or [],
        "completedAt": datetime.utcnow()
    }

    result = await user_collection.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "profile": profile_update,
                "onboarding_completed": True,
                "updatedAt": datetime.utcnow()
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = await user_collection.find_one({"_id": user["_id"]})
    return {
        "message": "Profile updated successfully",
        "user": user_helper(updated_user)
    }
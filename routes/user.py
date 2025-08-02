from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from models.user import user_collection, user_helper
from utils.auth import get_current_user
from schemas.user import UserOut, UserUpdate
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
import base64
from typing import List

router = APIRouter()

@router.get("/profile", response_model=UserOut)
async def get_profile(user=Depends(get_current_user)):
    return user_helper(user)

@router.put("/profile")
async def update_profile(
    name: str = Form(None),
    image: UploadFile = File(None),
    user=Depends(get_current_user)
):
    updates = {}
    if name:
        updates["name"] = name
    if image:
        content = await image.read()
        encoded_image = base64.b64encode(content).decode("utf-8")
        updates["image"] = encoded_image

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update.")
    updates["updatedAt"] = datetime.utcnow()
    await user_collection.update_one({"_id": user["_id"]}, {"$set": updates})
    updated_user = await user_collection.find_one({"_id": user["_id"]})
    return user_helper(updated_user)

@router.post("/profile/image")
async def update_profile_image(
    image: UploadFile = File(...),
    user=Depends(get_current_user)
):
    content = await image.read()
    encoded_image = base64.b64encode(content).decode("utf-8")
    await user_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"image": encoded_image, "updatedAt": datetime.utcnow()}}
    )
    return {"message": "Image updated successfully"}


@router.delete("/users/{user_id}")
async def soft_delete_user(user_id: str):
    try:
        user_obj_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    result = await user_collection.update_one({"_id": user_obj_id}, {"$set": {"is_active": False}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User deactivated"}
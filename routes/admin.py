from fastapi import APIRouter, Depends, HTTPException, Header
from utils.auth import decode_access_token
from models.user import user_collection, user_helper
from utils.auth import get_current_user
from schemas.user import UserOut, UserUpdate
from bson import ObjectId
from typing import List

router = APIRouter(prefix="/admin", tags=["Admin"])

def get_admin(token: str = Header(...)):
    payload = decode_access_token(token)
    if not payload or not payload.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admins only")
    return payload

@router.get("/admin/users", response_model=List[UserOut])
async def get_all_users(user=Depends(get_current_user)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    users = await user_collection.find().to_list(None)
    return [user_helper(u) for u in users]

@router.put("/admin/users/{user_id}")
async def update_user(user_id: str, update: UserUpdate, admin=Depends(get_current_user)):
    if not admin.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    await user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": update.dict(exclude_unset=True)})
    updated_user = await user_collection.find_one({"_id": ObjectId(user_id)})
    return user_helper(updated_user)

@router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, admin=Depends(get_current_user)):
    if not admin.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    await user_collection.delete_one({"_id": ObjectId(user_id)})
    return {"message": "User deleted successfully"}

# Fetching data with pagination
@router.get("/admin/users", response_model=List[UserOut])
async def get_all_users(skip: int = 0, limit: int = 10, user=Depends(get_current_user)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    users = user_collection.find().skip(skip).limit(limit)
    return [user_helper(u) async for u in users]

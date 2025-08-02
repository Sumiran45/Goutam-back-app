from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from schemas.activity import ActivityCreate, ActivityResponse
from models.activity import ActivityModel
from utils.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[ActivityResponse])
async def get_activities(
    limit: int = Query(50, ge=1, le=100),
    days_back: int = Query(7, ge=1, le=365)
):
    """Get activities with optional filtering"""
    try:
        activities = await ActivityModel.get_activities(limit=limit, days_back=days_back)
        return activities
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching activities: {str(e)}")

@router.get("/recent", response_model=List[ActivityResponse])
async def get_recent_activities(
    limit: int = Query(10, ge=1, le=50)
):
    """Get recent activities"""
    try:
        activities = await ActivityModel.get_recent_activities(limit=limit)
        return activities
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recent activities: {str(e)}")

@router.get("/stats")
async def get_activity_stats():
    """Get activity statistics"""
    try:
        stats = await ActivityModel.get_activity_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching activity stats: {str(e)}")

@router.delete("/cleanup")
async def cleanup_old_activities(current_user=Depends(get_current_user)):
    """Cleanup activities older than 45 days (Admin only)"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        deleted_count = await ActivityModel.cleanup_old_activities()
        return {
            "message": f"Successfully cleaned up {deleted_count} old activities",
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during cleanup: {str(e)}")
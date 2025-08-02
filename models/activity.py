from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from bson import ObjectId
from database import db

activity_collection = db["activity"]

def activity_helper(activity) -> dict:
    """Helper function to transform activity document"""
    return {
        "id": str(activity["_id"]),
        "type": activity["type"],
        "title": activity["title"],
        "description": activity["description"],
        "user_id": activity.get("user_id"),
        "user_name": activity.get("user_name"),
        "entity_id": activity.get("entity_id"),
        "entity_name": activity.get("entity_name"),
        "metadata": activity.get("metadata", {}),
        "icon": activity.get("icon", "bell"),
        "created_at": activity["created_at"]
    }

class ActivityModel:
    @staticmethod
    async def create_activity(activity_data: dict) -> dict:
        """Create a new activity"""
        activity_data["created_at"] = datetime.utcnow()
        result = await activity_collection.insert_one(activity_data)
        created_activity = await activity_collection.find_one({"_id": result.inserted_id})
        return activity_helper(created_activity)
    
    @staticmethod
    async def get_activities(limit: int = 50, days_back: int = 7) -> List[dict]:
        """Get activities with optional filtering"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        cursor = activity_collection.find(
            {"created_at": {"$gte": cutoff_date}}
        ).sort("created_at", -1).limit(limit)
        
        activities = []
        async for activity in cursor:
            activities.append(activity_helper(activity))
        
        return activities
    
    @staticmethod
    async def get_recent_activities(limit: int = 10) -> List[dict]:
        """Get recent activities"""
        cursor = activity_collection.find().sort("created_at", -1).limit(limit)
        
        activities = []
        async for activity in cursor:
            activities.append(activity_helper(activity))
        
        return activities
    
    @staticmethod
    async def get_activity_stats() -> Dict[str, int]:
        """Get activity statistics"""
        pipeline = [
            {"$group": {"_id": "$type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        stats = {}
        async for stat in activity_collection.aggregate(pipeline):
            stats[stat["_id"]] = stat["count"]
        
        return stats
    
    @staticmethod
    async def cleanup_old_activities():
        """Remove activities older than 45 days"""
        cutoff_date = datetime.utcnow() - timedelta(days=45)
        result = await activity_collection.delete_many(
            {"created_at": {"$lt": cutoff_date}}
        )
        return result.deleted_count
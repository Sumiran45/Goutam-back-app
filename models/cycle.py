from database import db
from bson import ObjectId
from datetime import datetime

cycle_collection = db["cycle_entries"]

def cycle_entry_helper(entry) -> dict:
    return {
        "id": str(entry["_id"]),
        "user_id": str(entry["user_id"]),
        "date": entry["date"],
        "is_period_day": entry["is_period_day"],
        "flow_intensity": entry.get("flow_intensity"),
        "moods": entry.get("moods", []),
        "physical_symptoms": entry.get("physical_symptoms", []),
        "notes": entry.get("notes"),
        "sleep_hours": entry.get("sleep_hours"),
        "exercise_minutes": entry.get("exercise_minutes"),
        "water_intake": entry.get("water_intake"),
        "created_at": entry["created_at"],
        "updated_at": entry["updated_at"]
    }

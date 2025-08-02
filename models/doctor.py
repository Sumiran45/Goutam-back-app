# from database import db
# from datetime import datetime
# from typing import List, Dict, Any, Optional
# from bson import ObjectId
# import asyncio
#
# doctor_collection = db["doctors"]
# appointment_collection = db["appointments"]
# rating_collection = db["ratings"]
#
# def doctor_helper(doc) -> dict:
#     """Convert MongoDB document to dict"""
#     result = {
#         "id": str(doc["_id"]),
#         "name": doc.get("name"),
#         "specialization": doc.get("specialization"),
#         "qualification": doc.get("qualification"),
#         "experience_years": doc.get("experience_years"),
#         "hospital_affiliation": doc.get("hospital_affiliation"),
#         "about": doc.get("about"),
#         "consultation_fee": doc.get("consultation_fee"),
#         "contact_info": doc.get("contact_info"),
#         "availability": doc.get("availability"),
#         "services": doc.get("services"),
#         "awards": doc.get("awards", []),
#         "languages": doc.get("languages"),
#         "rating": doc.get("rating", 0),
#         "total_ratings": doc.get("total_ratings", 0),
#         "verified": doc.get("verified", False),
#         "profile_image": doc.get("profile_image"),
#         "created_at": doc.get("created_at"),
#         "updated_at": doc.get("updated_at")
#     }
#
#     # Handle distance field from geoNear
#     if "distance" in doc:
#         result["distance_km"] = round(doc["distance"] / 1000, 2)
#     elif "dist" in doc and "calculated" in doc["dist"]:
#         result["distance_km"] = round(doc["dist"]["calculated"] / 1000, 2)
#
#     return result
#
# async def get_doctor_stats(doctor_id: str) -> Dict[str, Any]:
#     """Get statistics for a doctor"""
#     today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
#     week_start = today - timedelta(days=today.weekday())
#
#     # Count appointments
#     total_appointments = await appointment_collection.count_documents({"doctor_id": doctor_id})
#     appointments_today = await appointment_collection.count_documents({
#         "doctor_id": doctor_id,
#         "appointment_date": {"$gte": today, "$lt": today + timedelta(days=1)}
#     })
#     appointments_this_week = await appointment_collection.count_documents({
#         "doctor_id": doctor_id,
#         "appointment_date": {"$gte": week_start}
#     })
#
#     # Get rating stats
#     rating_stats = await rating_collection.aggregate([
#         {"$match": {"doctor_id": doctor_id}},
#         {"$group": {
#             "_id": None,
#             "avg_rating": {"$avg": "$rating"},
#             "total_reviews": {"$sum": 1}
#         }}
#     ]).to_list(1)
#
#     stats = rating_stats[0] if rating_stats else {"avg_rating": 0, "total_reviews": 0}
#
#     return {
#         "total_patients": total_appointments,
#         "appointments_today": appointments_today,
#         "appointments_this_week": appointments_this_week,
#         "avg_rating": round(stats["avg_rating"], 1) if stats["avg_rating"] else 0.0,
#         "total_reviews": stats["total_reviews"]
#     }
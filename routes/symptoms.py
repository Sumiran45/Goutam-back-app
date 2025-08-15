from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta, date
from bson import ObjectId

from database import db
from models.symptoms import SymptomDocument, SYMPTOM_COLLECTION
from schemas.symptoms import (
    SymptomInput, SymptomResponse, 
    PredictionResponse, SuggestionResponse, SymptomAnalytics
)
from utils.symptom_predictor import SymptomPredictor
from utils.auth import get_current_user  # Assuming you have auth utils

router = APIRouter(prefix="/symptoms", tags=["symptoms"])
predictor = SymptomPredictor()

# MongoDB collection
symptoms_collection = db[SYMPTOM_COLLECTION]

@router.post("/today", response_model=SymptomResponse)
async def save_today_symptoms(
    symptom_data: SymptomInput,
    current_user: dict = Depends(get_current_user)
):
    """Save today's symptoms for the authenticated user"""
    
    # Check if symptoms already exist for today
    today = datetime.utcnow().date()
    existing_symptom = await symptoms_collection.find_one({
        "user_id": str(current_user["_id"]),
        "date": datetime.combine(today, datetime.min.time())
    })
    
    if existing_symptom:
        # Update existing entry
        update_data = symptom_data.dict(exclude_unset=True)
        update_data["created_at"] = datetime.utcnow()
        
        await symptoms_collection.update_one(
            {"_id": existing_symptom["_id"]},
            {"$set": update_data}
        )
        
        # Fetch updated document
        updated_symptom = await symptoms_collection.find_one({"_id": existing_symptom["_id"]})
        return SymptomResponse(**updated_symptom, id=str(updated_symptom["_id"]))
    
    # Create new symptom entry with datetime instead of date
    symptom_data_dict = symptom_data.dict()
    symptom_doc = SymptomDocument(
        user_id=str(current_user["_id"]),
        date=datetime.combine(today, datetime.min.time()),  # Convert date to datetime at start of day
        **symptom_data_dict
    )
    
    # Insert into MongoDB
    symptom_dict = symptom_doc.dict(by_alias=True)
    symptom_dict['date'] = datetime.combine(symptom_doc.date, datetime.min.time())  # Ensure datetime is used
    result = await symptoms_collection.insert_one(symptom_dict)
    
    # Fetch the created document
    created_symptom = await symptoms_collection.find_one({"_id": result.inserted_id})
    
    return SymptomResponse(**created_symptom, id=str(created_symptom["_id"]))

@router.get("/tomorrow", response_model=PredictionResponse)
async def predict_tomorrow_symptoms(
    current_user: dict = Depends(get_current_user)
):
    """Predict tomorrow's symptoms based on user's historical data"""
    
    # Get user's symptom history (last 30 days)
    thirty_days_ago = datetime.combine(date.today() - timedelta(days=30), datetime.min.time())
    
    cursor = symptoms_collection.find({
        "user_id": str(current_user["_id"]),
        "date": {"$gte": thirty_days_ago}
    }).sort("date", -1)
    
    user_symptoms = await cursor.to_list(length=None)
    
    if not user_symptoms:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No symptom history found. Please log symptoms for a few days first."
        )
    
    # Convert to response models
    symptom_responses = [
        SymptomResponse(**symptom, id=str(symptom["_id"])) 
        for symptom in user_symptoms
    ]
    
    # Generate predictions for tomorrow
    tomorrow = date.today() + timedelta(days=1)
    prediction = predictor.predict_tomorrow_symptoms(symptom_responses, tomorrow)
    
    return prediction

@router.get("/suggestions", response_model=SuggestionResponse)
async def get_suggestions(
    include_predictions: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """Get health suggestions based on current and predicted symptoms"""
    
    # Get today's symptoms
    today = datetime.utcnow().date()
    today_symptoms = await symptoms_collection.find_one({
        "user_id": str(current_user["_id"]),
        "date": datetime.combine(today, datetime.min.time())
    })
    
    predicted_symptoms = []
    
    if include_predictions:
        # Get recent symptom history for predictions
        thirty_days_ago = datetime.combine(today - timedelta(days=30), datetime.min.time())
        
        cursor = symptoms_collection.find({
            "user_id": str(current_user["_id"]),
            "date": {"$gte": thirty_days_ago}
        }).sort("date", -1)
        
        user_symptoms = await cursor.to_list(length=None)
        
        if user_symptoms:
            symptom_responses = [
                SymptomResponse(**symptom, id=str(symptom["_id"]))
                for symptom in user_symptoms
            ]
            tomorrow = today + timedelta(days=1)
            prediction = predictor.predict_tomorrow_symptoms(symptom_responses, tomorrow)
            predicted_symptoms = prediction.predicted_symptoms
    
    # Generate suggestions
    current_symptom_response = (
        SymptomResponse(**today_symptoms, id=str(today_symptoms["_id"]))
        if today_symptoms else None
    )
    suggestions = predictor.generate_suggestions(current_symptom_response, predicted_symptoms)
    
    return suggestions

@router.get("/history", response_model=List[SymptomResponse])
async def get_symptom_history(
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """Get user's symptom history for the specified number of days"""
    
    if days > 365:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot retrieve more than 365 days of history"
        )
    
    # Convert start_date to datetime at start of day for MongoDB query
    start_date = datetime.combine(date.today() - timedelta(days=days), datetime.min.time())
    
    cursor = symptoms_collection.find({
        "user_id": str(current_user["_id"]),
        "date": {"$gte": start_date}
    }).sort("date", -1)
    
    symptoms = await cursor.to_list(length=None)
    
    return [
        SymptomResponse(**symptom, id=str(symptom["_id"]))
        for symptom in symptoms
    ]

@router.get("/analytics", response_model=SymptomAnalytics)
async def get_symptom_analytics(
    days: int = 90,
    current_user: dict = Depends(get_current_user)
):
    """Get analytics and patterns from user's symptom data"""
    
    start_date = datetime.combine(date.today() - timedelta(days=days), datetime.min.time())
    
    cursor = symptoms_collection.find({
        "user_id": str(current_user["_id"]),
        "date": {"$gte": start_date}
    })
    
    symptoms = await cursor.to_list(length=None)
    
    if not symptoms:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No symptom data found for analytics"
        )
    
    # Calculate analytics
    total_entries = len(symptoms)
    dates = [s["date"] for s in symptoms]
    date_range = {"start": min(dates), "end": max(dates)}
    
    # Most common mood
    moods = [s["mood"] for s in symptoms if s.get("mood")]
    most_common_mood = max(set(moods), key=moods.count) if moods else None
    
    # Average cramp intensity
    cramps = [s["cramps"] for s in symptoms if s.get("cramps") and s["cramps"] != "none"]
    cramp_intensities = {"mild": 1, "moderate": 2, "strong": 3}
    if cramps:
        avg_intensity = sum(cramp_intensities.get(c, 0) for c in cramps) / len(cramps)
        intensity_map = {1: "mild", 2: "moderate", 3: "strong"}
        average_cramp_intensity = intensity_map.get(round(avg_intensity), "mild")
    else:
        average_cramp_intensity = None
    
    # Symptom frequency
    symptom_frequency = {
        "headache": sum(1 for s in symptoms if s.get("headache", False)),
        "nausea": sum(1 for s in symptoms if s.get("nausea", False)),
        "fatigue": sum(1 for s in symptoms if s.get("fatigue", False)),
        "cramps": sum(1 for s in symptoms if s.get("cramps") and s["cramps"] != "none")
    }
    
    # Simple patterns
    patterns = []
    if symptom_frequency["headache"] > total_entries * 0.3:
        patterns.append("Frequent headaches detected")
    if symptom_frequency["cramps"] > total_entries * 0.4:
        patterns.append("Regular cramping pattern")
    if symptom_frequency["fatigue"] > total_entries * 0.5:
        patterns.append("High fatigue frequency")
    
    return SymptomAnalytics(
        total_entries=total_entries,
        date_range=date_range,
        most_common_mood=most_common_mood,
        average_cramp_intensity=average_cramp_intensity,
        symptom_frequency=symptom_frequency,
        patterns=patterns
    )

@router.delete("/{symptom_id}")
async def delete_symptom(
    symptom_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a specific symptom entry"""
    
    # Validate ObjectId
    if not ObjectId.is_valid(symptom_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid symptom ID format"
        )
    
    # Find and delete the symptom
    result = await symptoms_collection.delete_one({
        "_id": ObjectId(symptom_id),
        "user_id": current_user["id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Symptom entry not found"
        )
    
    return {"message": "Symptom entry deleted successfully"}

@router.get("/today", response_model=Optional[SymptomResponse])
async def get_today_symptoms(
    current_user: dict = Depends(get_current_user)
):
    """Get today's symptoms for the authenticated user"""
    
    today = datetime.utcnow().date()
    symptom = await symptoms_collection.find_one({
        "user_id": str(current_user["_id"]),
        "date": datetime.combine(today, datetime.min.time())
    })
    
    if not symptom:
        return None
    
    return SymptomResponse(**symptom, id=str(symptom["_id"]))

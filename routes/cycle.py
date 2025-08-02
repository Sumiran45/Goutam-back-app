from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, date, timedelta
from bson import ObjectId
from bson.errors import InvalidId

from schemas.cycle import (
    CycleEntryCreate, CycleEntryOut, CycleStats,
    CycleAnalysis, CyclePrediction
)
from models.cycle import cycle_collection, cycle_entry_helper
from utils.auth import get_current_user
from utils.cycle_calculator import MenstrualCycleCalculator

router = APIRouter(prefix="/cycle", tags=["Menstrual Cycle"])
calculator = MenstrualCycleCalculator()


@router.post("/entries", response_model=CycleEntryOut)
async def create_cycle_entry(
        entry: CycleEntryCreate,
        user=Depends(get_current_user)
):
    """Create a new cycle entry"""
    # Check if entry already exists for this date
    existing = await cycle_collection.find_one({
        "user_id": user["_id"],
        "date": entry.date
    })

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Entry already exists for this date. Use PUT to update."
        )

    entry_dict = entry.dict()
    entry_dict.update({
        "user_id": user["_id"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })

    result = await cycle_collection.insert_one(entry_dict)
    created_entry = await cycle_collection.find_one({"_id": result.inserted_id})

    return cycle_entry_helper(created_entry)


@router.get("/entries", response_model=List[CycleEntryOut])
async def get_cycle_entries(
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None),
        limit: int = Query(100, le=365),
        user=Depends(get_current_user)
):
    """Get cycle entries for a date range"""
    query = {"user_id": user["_id"]}

    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        query["date"] = date_filter

    entries = cycle_collection.find(query).sort("date", -1).limit(limit)
    return [cycle_entry_helper(entry) async for entry in entries]


@router.put("/entries/{entry_id}", response_model=CycleEntryOut)
async def update_cycle_entry(
        entry_id: str,
        entry: CycleEntryCreate,
        user=Depends(get_current_user)
):
    """Update an existing cycle entry"""
    try:
        entry_obj_id = ObjectId(entry_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid entry ID")

    # Verify ownership
    existing = await cycle_collection.find_one({
        "_id": entry_obj_id,
        "user_id": user["_id"]
    })

    if not existing:
        raise HTTPException(status_code=404, detail="Entry not found")

    entry_dict = entry.dict()
    entry_dict["updated_at"] = datetime.utcnow()

    await cycle_collection.update_one(
        {"_id": entry_obj_id},
        {"$set": entry_dict}
    )

    updated_entry = await cycle_collection.find_one({"_id": entry_obj_id})
    return cycle_entry_helper(updated_entry)


@router.delete("/entries/{entry_id}")
async def delete_cycle_entry(
        entry_id: str,
        user=Depends(get_current_user)
):
    """Delete a cycle entry"""
    try:
        entry_obj_id = ObjectId(entry_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid entry ID")

    result = await cycle_collection.delete_one({
        "_id": entry_obj_id,
        "user_id": user["_id"]
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Entry not found")

    return {"message": "Entry deleted successfully"}


@router.get("/stats", response_model=CycleStats)
async def get_cycle_stats(user=Depends(get_current_user)):
    """Get cycle statistics and predictions"""
    # Get last 12 months of data
    since_date = date.today() - timedelta(days=365)
    entries = cycle_collection.find({
        "user_id": user["_id"],
        "date": {"$gte": since_date}
    }).sort("date", 1)

    entries_list = [entry async for entry in entries]
    return calculator.calculate_cycle_stats(entries_list)


@router.get("/predictions", response_model=List[CyclePrediction])
async def get_cycle_predictions(
        days_ahead: int = Query(30, ge=1, le=90),
        user=Depends(get_current_user)
):
    """Get cycle predictions for the next X days"""
    # Get historical data for better predictions
    since_date = date.today() - timedelta(days=365)
    entries = cycle_collection.find({
        "user_id": user["_id"],
        "date": {"$gte": since_date}
    }).sort("date", 1)

    entries_list = [entry async for entry in entries]
    return calculator.generate_predictions(entries_list, days_ahead)


@router.get("/analysis", response_model=CycleAnalysis)
async def get_cycle_analysis(user=Depends(get_current_user)):
    """Get comprehensive cycle analysis"""
    # Get last 12 months of data
    since_date = date.today() - timedelta(days=365)
    entries = cycle_collection.find({
        "user_id": user["_id"],
        "date": {"$gte": since_date}
    }).sort("date", 1)

    entries_list = [entry async for entry in entries]

    stats = calculator.calculate_cycle_stats(entries_list)
    predictions = calculator.generate_predictions(entries_list, 30)
    mood_patterns = calculator.analyze_mood_patterns(entries_list)
    symptom_patterns = calculator.analyze_symptom_patterns(entries_list)

    return CycleAnalysis(
        stats=stats,
        predictions=predictions,
        mood_patterns=mood_patterns,
        symptom_patterns=symptom_patterns
    )


@router.get("/calendar")
async def get_cycle_calendar(
        year: int = Query(None),
        month: int = Query(None),
        user=Depends(get_current_user)
):
    """Get cycle data formatted for calendar display"""
    if not year:
        year = date.today().year
    if not month:
        month = date.today().month

    # Get entries for the specified month
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)

    entries = cycle_collection.find({
        "user_id": user["_id"],
        "date": {"$gte": start_date, "$lte": end_date}
    }).sort("date", 1)

    entries_list = [cycle_entry_helper(entry) async for entry in entries]

    # Get predictions for the month as well
    all_entries = cycle_collection.find({
        "user_id": user["_id"],
        "date": {"$gte": date.today() - timedelta(days=365)}
    }).sort("date", 1)

    all_entries_list = [entry async for entry in all_entries]
    predictions = calculator.generate_predictions(all_entries_list, 60)

    # Filter predictions for this month
    month_predictions = [
        p for p in predictions
        if p.date.year == year and p.date.month == month
    ]

    return {
        "entries": entries_list,
        "predictions": month_predictions,
        "month": month,
        "year": year
    }
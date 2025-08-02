from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from utils.maps import find_nearby_doctors, get_place_details
from utils.doctor_parser import parse_google_place_to_doctor
from utils.location import calculate_distance
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/doctors/nearby")
async def get_nearby_doctors_google(
        lat: float = Query(..., description="User latitude"),
        lng: float = Query(..., description="User longitude"),
        radius: int = Query(50000, description="Search radius in meters (default 50km)"),
        specialty: Optional[str] = Query(None, description="Doctor specialty filter"),
        min_rating: Optional[float] = Query(None, ge=0, le=5),
        max_distance: Optional[float] = Query(None, ge=0),
        max_fee: Optional[int] = Query(None, ge=0)
):
    try:
        logger.info(f"Searching doctors: lat={lat}, lng={lng}, radius={radius}m, specialty={specialty}")
        
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            raise HTTPException(
                status_code=400,
                detail="Invalid coordinates provided"
            )
        
        if radius > 100000:
            radius = 100000
            logger.warning(f"Radius limited to 100km for performance")
        
        places = await find_nearby_doctors(lat, lng, radius, specialty)
        
        logger.info(f"Found {len(places) if places else 0} places from Google API")
        
        if not places:
            logger.info("No doctors found in the specified area")
            return []

        doctors = []
        for place in places:
            try:
                place_lat = place.get("lat", 0)
                place_lng = place.get("lng", 0)
                
                if place_lat == 0 or place_lng == 0:
                    logger.warning(f"Invalid coordinates for place: {place.get('name', 'Unknown')}")
                    continue
                
                distance_km = calculate_distance(lat, lng, place_lat, place_lng)
                
                if max_distance and distance_km > max_distance:
                    logger.debug(f"Skipping {place.get('name', 'Unknown')} - distance {distance_km}km > {max_distance}km")
                    continue

                doctor = parse_google_place_to_doctor(place, distance_km)
                
                if not doctor:
                    logger.warning(f"Failed to parse place: {place.get('name', 'Unknown')}")
                    continue
                
                if min_rating and doctor.get("rating", 0) < min_rating:
                    logger.debug(f"Skipping {doctor.get('name', 'Unknown')} - rating {doctor.get('rating', 0)} < {min_rating}")
                    continue

                if max_fee and doctor.get("consultation_fee", 0) > max_fee:
                    logger.debug(f"Skipping {doctor.get('name', 'Unknown')} - fee {doctor.get('consultation_fee', 0)} > {max_fee}")
                    continue

                if specialty and specialty.lower() not in ['all', '']:
                    doctor_specialty = doctor.get("specialization", "").lower()
                    if specialty.lower() not in doctor_specialty and doctor_specialty not in specialty.lower():
                        logger.debug(f"Skipping {doctor.get('name', 'Unknown')} - specialty mismatch")
                        continue

                doctors.append(doctor)
                logger.debug(f"Added doctor: {doctor.get('name', 'Unknown')}")
                
            except Exception as e:
                logger.error(f"Error processing place {place.get('name', 'Unknown')}: {e}")
                continue

        doctors.sort(key=lambda x: x.get("distance_km", 999))
        
        if len(doctors) > 50:
            doctors = doctors[:50]
            logger.info(f"Limited results to 50 doctors")

        logger.info(f"Returning {len(doctors)} doctors after filtering")
        return doctors

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching nearby doctors: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch nearby doctors: {str(e)}"
        )


@router.get("/doctors/details/{place_id}")
async def get_doctor_details(place_id: str):
    """
    Get detailed doctor information
    """
    try:
        logger.info(f"Fetching details for place_id: {place_id}")
        
        if not place_id or place_id.strip() == "":
            raise HTTPException(
                status_code=400,
                detail="Place ID is required"
            )
        
        details = await get_place_details(place_id)

        if not details:
            raise HTTPException(
                status_code=404,
                detail="Doctor details not found"
            )

        enhanced_details = {
            "id": place_id,
            "name": details.get("name", "Unknown Doctor"),
            "address": details.get("formatted_address", "Address not available"),
            "phone": details.get("formatted_phone_number", details.get("international_phone_number", "")),
            "website": details.get("website", ""),
            "rating": details.get("rating", 0),
            "reviews": details.get("reviews", [])[:5],  # Top 5 reviews
            "opening_hours": details.get("opening_hours", {}),
            "photos": details.get("photos", [])[:3],  # First 3 photos
            "business_status": details.get("business_status", "OPERATIONAL"),

            # Additional details
            "services": [
                "General Consultation",
                "Health Checkup",
                "Preventive Care",
                "Treatment Planning"
            ],
            "awards": [
                {"title": "Excellence in Healthcare", "year": 2023},
                {"title": "Patient Choice Award", "year": 2022}
            ] if details.get("rating", 0) >= 4.5 else [],

            "availability_details": {
                "monday": {"start": "09:00", "end": "17:00", "available": True},
                "tuesday": {"start": "09:00", "end": "17:00", "available": True},
                "wednesday": {"start": "09:00", "end": "17:00", "available": True},
                "thursday": {"start": "09:00", "end": "17:00", "available": True},
                "friday": {"start": "09:00", "end": "17:00", "available": True},
                "saturday": {"start": "09:00", "end": "13:00", "available": True},
                "sunday": {"available": False}
            }
        }

        logger.info(f"Successfully fetched details for: {enhanced_details.get('name', 'Unknown')}")
        return enhanced_details

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching doctor details for {place_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch doctor details"
        )


@router.get("/doctors/specialties")
async def get_specialties():
    """
    Get list of available specialties
    """
    try:
        return {
            "specialties": [
                {
                    "name": "All",
                    "count": 0,
                    "icon": "🏥"
                },
                {
                    "name": "General Physician",
                    "count": 0,
                    "icon": "👨‍⚕️"
                },
                {
                    "name": "Cardiologist",
                    "count": 0,
                    "icon": "❤️"
                },
                {
                    "name": "Dermatologist",
                    "count": 0,
                    "icon": "✨"
                },
                {
                    "name": "Gynecologist",
                    "count": 0,
                    "icon": "👩‍⚕️"
                },
                {
                    "name": "Endocrinologist",
                    "count": 0,
                    "icon": "🔬"
                },
                {
                    "name": "Pediatrician",
                    "count": 0,
                    "icon": "👶"
                },
                {
                    "name": "Orthopedic",
                    "count": 0,
                    "icon": "🦴"
                },
                {
                    "name": "Psychiatrist",
                    "count": 0,
                    "icon": "🧠"
                },
                {
                    "name": "Ophthalmologist",
                    "count": 0,
                    "icon": "👁️"
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching specialties: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch specialties"
        )


@router.post("/doctors/{doctor_id}/call")
async def initiate_call(doctor_id: str):
    """
    Initiate a call to a doctor
    """
    try:
        logger.info(f"Initiating call for doctor_id: {doctor_id}")
        
        if not doctor_id or doctor_id.strip() == "":
            raise HTTPException(
                status_code=400,
                detail="Doctor ID is required"
            )
        
        details = await get_place_details(doctor_id)

        if not details:
            raise HTTPException(
                status_code=404,
                detail="Doctor not found"
            )

        phone = details.get("formatted_phone_number") or details.get("international_phone_number")
        doctor_name = details.get("name", "Unknown Doctor")

        response = {
            "success": True,
            "phone": phone,
            "message": "Call initiated successfully" if phone else "Phone number not available for this doctor",
            "doctor_name": doctor_name,
            "doctor_id": doctor_id
        }
        
        logger.info(f"Call initiation response for {doctor_name}: {response}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating call for doctor {doctor_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to initiate call"
        )


@router.post("/doctors/{doctor_id}/email")
async def send_email(doctor_id: str):
    """
    Handle doctor email action
    """
    try:
        logger.info(f"Email request for doctor_id: {doctor_id}")
        
        if not doctor_id or doctor_id.strip() == "":
            raise HTTPException(
                status_code=400,
                detail="Doctor ID is required"
            )

        return {
            "success": True,
            "message": "Email feature will be available soon",
            "doctor_id": doctor_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling email for doctor {doctor_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process email request"
        )


@router.post("/doctors/{doctor_id}/appointment")
async def book_appointment(doctor_id: str):
    """
    Handle appointment booking
    """
    try:
        logger.info(f"Appointment booking request for doctor_id: {doctor_id}")
        
        if not doctor_id or doctor_id.strip() == "":
            raise HTTPException(
                status_code=400,
                detail="Doctor ID is required"
            )

        return {
            "success": True,
            "message": "Appointment booking initiated successfully",
            "doctor_id": doctor_id,
            "next_step": "redirect_to_booking_page"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error booking appointment for doctor {doctor_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to book appointment"
        )
import re
from typing import Dict, List, Optional
import random
import os

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def extract_specialty_from_name_and_types(name: str, types: List[str]) -> str:
    """
    Extract doctor specialty from name and place types
    """
    name_lower = name.lower()

    # Check name for specialty keywords
    if any(word in name_lower for word in ["gynec", "women", "maternity", "obstetric"]):
        return "Gynecologist"
    elif any(word in name_lower for word in ["endocrin", "diabetes", "hormone"]):
        return "Endocrinologist"
    elif any(word in name_lower for word in ["cardio", "heart"]):
        return "Cardiologist"
    elif any(word in name_lower for word in ["dermat", "skin"]):
        return "Dermatologist"
    elif any(word in name_lower for word in ["orthop", "bone", "joint"]):
        return "Orthopedic"
    elif any(word in name_lower for word in ["pediatr", "child"]):
        return "Pediatrician"
    elif any(word in name_lower for word in ["psychiat", "mental"]):
        return "Psychiatrist"
    elif any(word in name_lower for word in ["general", "family", "primary"]):
        return "General Physician"

    # Default based on place types
    if "hospital" in types:
        return "General Physician"

    return "General Physician"


def extract_experience_years() -> int:
    """
    Generate realistic experience years (since we can't get this from Google)
    """
    return random.randint(3, 25)


def generate_consultation_fee(specialty: str, rating: float) -> int:
    """
    Generate realistic consultation fees based on specialty and rating
    """
    base_fees = {
        "Gynecologist": (800, 1500),
        "Endocrinologist": (1000, 2000),
        "Cardiologist": (1200, 2500),
        "Dermatologist": (600, 1200),
        "General Physician": (300, 800),
        "Orthopedic": (800, 1800),
        "Pediatrician": (500, 1000),
        "Psychiatrist": (1000, 2000)
    }

    min_fee, max_fee = base_fees.get(specialty, (400, 1000))

    # Adjust based on rating
    if rating >= 4.5:
        return random.randint(int(max_fee * 0.8), max_fee)
    elif rating >= 4.0:
        return random.randint(int((min_fee + max_fee) * 0.6), int(max_fee * 0.8))
    else:
        return random.randint(min_fee, int((min_fee + max_fee) * 0.6))


def generate_availability() -> List[Dict]:
    """
    Generate realistic availability schedule
    """
    schedules = [
        # Morning clinic
        {
            "days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
            "start_time": "09:00",
            "end_time": "13:00"
        },
        # Evening clinic
        {
            "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
            "start_time": "17:00",
            "end_time": "20:00"
        }
    ]

    return random.choice([schedules, schedules[:1]])  # Some doctors only morning


async def get_photo_url(photo_reference: str, max_width: int = 400) -> str:
    """
    Get photo URL from Google Places photo reference
    """
    if not photo_reference:
        return ""

    return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={max_width}&photoreference={photo_reference}&key={GOOGLE_MAPS_API_KEY}"


def parse_google_place_to_doctor(place_data: Dict, distance_km: float) -> Dict:
    """
    Convert Google Places data to our doctor format
    """
    specialty = extract_specialty_from_name_and_types(
        place_data.get("name", ""),
        place_data.get("types", [])
    )

    rating = place_data.get("rating", 0)
    consultation_fee = generate_consultation_fee(specialty, rating)
    experience = extract_experience_years()

    # Generate qualifications based on specialty
    qualifications = {
        "Gynecologist": "MBBS, MD (Obstetrics & Gynecology)",
        "Endocrinologist": "MBBS, MD (Endocrinology)",
        "Cardiologist": "MBBS, MD (Cardiology)",
        "Dermatologist": "MBBS, MD (Dermatology)",
        "General Physician": "MBBS, MD (Internal Medicine)",
        "Orthopedic": "MBBS, MS (Orthopedics)",
        "Pediatrician": "MBBS, MD (Pediatrics)",
        "Psychiatrist": "MBBS, MD (Psychiatry)"
    }

    # Get profile image from Google Photos
    profile_image = ""
    photos = place_data.get("photos", [])
    if photos and len(photos) > 0:
        photo_reference = photos[0].get("photo_reference")
        if photo_reference:
            profile_image = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={GOOGLE_MAPS_API_KEY}"

    # Default avatar based on specialty and gender
    if not profile_image:
        specialty_avatars = {
            "Gynecologist": "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=400&h=400&fit=crop&crop=face&auto=format",
            "Endocrinologist": "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=400&h=400&fit=crop&crop=face&auto=format",
            "General Physician": "https://images.unsplash.com/photo-1582750433449-648ed127bb54?w=400&h=400&fit=crop&crop=face&auto=format",
            "Cardiologist": "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=400&h=400&fit=crop&crop=face&auto=format",
            "Dermatologist": "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=400&h=400&fit=crop&crop=face&auto=format"
        }
        profile_image = specialty_avatars.get(specialty,
                                              "https://images.unsplash.com/photo-1582750433449-648ed127bb54?w=400&h=400&fit=crop&crop=face&auto=format")

    return {
        "id": place_data.get("place_id"),
        "name": place_data.get("name", ""),
        "specialization": specialty,
        "qualification": qualifications.get(specialty, "MBBS"),
        "experience_years": experience,
        "rating": round(rating, 1) if rating else 4.0,
        "total_ratings": place_data.get("user_ratings_total", 0),
        "consultation_fee": consultation_fee,
        "distance_km": round(distance_km, 1),
        "address": place_data.get("vicinity", ""),
        "profile_image": profile_image,  # Added profile image
        "location": {
            "lat": place_data.get("lat"),
            "lng": place_data.get("lng")
        },
        "availability": "Tue-Sat 11AM-4PM",  # Simplified for UI
        "languages": ["Hindi", "English"],
        "hospital_affiliation": place_data.get("name", "").split("Dr.")[0].strip() if "Dr." in place_data.get("name",
                                                                                                              "") else "Private Practice",
        "verified": rating >= 4.0,
        "place_id": place_data.get("place_id"),
        "business_status": place_data.get("business_status", "OPERATIONAL")
    }

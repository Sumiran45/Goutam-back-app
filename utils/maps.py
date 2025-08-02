import httpx
from fastapi import HTTPException
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
PLACES_API_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
DETAILS_API_URL = "https://maps.googleapis.com/maps/api/place/details/json"

# Specialty mapping for better search results
SPECIALTY_KEYWORDS = {
    "gynecologist": ["gynecologist", "women's health", "obstetrics", "maternity"],
    "endocrinologist": ["endocrinologist", "diabetes", "hormone", "thyroid"],
    "general physician": ["general practitioner", "family medicine", "primary care"],
    "dermatologist": ["dermatologist", "skin specialist"],
    "cardiologist": ["cardiologist", "heart specialist"],
    "psychiatrist": ["psychiatrist", "mental health"],
    "orthopedic": ["orthopedic", "bone specialist", "joint"],
    "pediatrician": ["pediatrician", "child specialist"]
}


async def find_nearby_doctors(
        lat: float,
        lng: float,
        radius: int = 5000,
        specialty: Optional[str] = None
) -> List[Dict]:
    """
    Find nearby doctors using Google Places API with enhanced search
    """
    try:
        # Base search for doctors/hospitals
        keywords = ["doctor", "hospital", "clinic", "medical center"]

        # Add specialty-specific keywords if provided
        if specialty and specialty.lower() in SPECIALTY_KEYWORDS:
            keywords.extend(SPECIALTY_KEYWORDS[specialty.lower()])

        all_places = []

        # Search with multiple keywords to get comprehensive results
        for keyword in keywords[:3]:  # Limit to avoid too many API calls
            params = {
                "location": f"{lat},{lng}",
                "radius": radius,
                "keyword": keyword,
                "type": "doctor",
                "key": GOOGLE_MAPS_API_KEY
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(PLACES_API_URL, params=params)
                response.raise_for_status()
                data = response.json()

            if data["status"] == "OK":
                for place in data.get("results", []):
                    # Avoid duplicates based on place_id
                    if not any(p["place_id"] == place.get("place_id") for p in all_places):
                        place_data = {
                            "name": place.get("name", ""),
                            "place_id": place.get("place_id"),
                            "lat": place["geometry"]["location"]["lat"],
                            "lng": place["geometry"]["location"]["lng"],
                            "vicinity": place.get("vicinity", ""),
                            "rating": place.get("rating", 0),
                            "user_ratings_total": place.get("user_ratings_total", 0),
                            "types": place.get("types", []),
                            "business_status": place.get("business_status", "OPERATIONAL"),
                            "price_level": place.get("price_level"),
                            "photos": place.get("photos", [])
                        }
                        all_places.append(place_data)

        return all_places[:20]  # Limit results

    except Exception as e:
        logger.error(f"Error in Google Maps API call: {e}")
        raise HTTPException(
            status_code=502,
            detail="Failed to fetch data from Google Maps API"
        )


async def get_place_details(place_id: str) -> Dict:
    """
    Get detailed information about a specific place
    """
    try:
        params = {
            "place_id": place_id,
            "fields": "name,formatted_address,formatted_phone_number,international_phone_number,website,opening_hours,rating,reviews,photos,price_level,types,business_status",
            "key": GOOGLE_MAPS_API_KEY
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(DETAILS_API_URL, params=params)
            response.raise_for_status()
            data = response.json()

        if data["status"] != "OK":
            logger.error(f"Google Places Details error: {data.get('error_message')}")
            return {}

        return data.get("result", {})

    except Exception as e:
        logger.error(f"Error fetching place details: {e}")
        return {}


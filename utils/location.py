# import math
# import os
# import httpx
# from typing import Tuple, Optional
# from dotenv import load_dotenv
#
# load_dotenv()
# GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
#
#
# async def get_coordinates_from_address(address: str) -> Tuple[Optional[float], Optional[float]]:
#     """
#     Use Google Maps Geocoding API to get coordinates (lat, lng) from a physical address.
#     """
#     async with httpx.AsyncClient() as client:
#         response = await client.get(
#             "https://maps.googleapis.com/maps/api/geocode/json",
#             params={"address": address, "key": GOOGLE_API_KEY}
#         )
#         data = response.json()
#         if data["status"] == "OK":
#             loc = data["results"][0]["geometry"]["location"]
#             return loc["lat"], loc["lng"]
#         return None, None
#
#
# def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
#     """
#     Calculate the great-circle distance between two points on the earth (in kilometers).
#     """
#     lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
#     dlat = lat2 - lat1
#     dlon = lon2 - lon1
#
#     a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
#     c = 2 * math.asin(math.sqrt(a))
#
#     earth_radius_km = 6371
#     return c * earth_radius_km
#
#
# def get_nearby_doctors_query(lat: float, lng: float, radius_km: float = 50) -> dict:
#     """
#     Generate a MongoDB geospatial query for doctors within a given radius (in km).
#     Requires a 2dsphere index on contact_info.location.
#     """
#     return {
#         "contact_info.location": {
#             "$near": {
#                 "$geometry": {
#                     "type": "Point",
#                     "coordinates": [lng, lat]
#                 },
#                 "$maxDistance": radius_km * 1000  # meters
#             }
#         }
#     }

# utils/location.py
import math


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula
    Returns distance in kilometers
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])

    # Haversine formula
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    # Radius of earth in kilometers
    r = 6371

    return c * r

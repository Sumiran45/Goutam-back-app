from database import db

user_collection = db["users"]
otp_collection = db["email_verification_codes"]

def user_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "username": user.get("username"),
        "email": user.get("email"),
        "phone": user.get("phone"),
        "is_admin": user.get("is_admin", False),
        "is_verified": user.get("is_verified", False),
        "phone_verified": user.get("phone_verified", False),
        "is_active": user.get("is_active", True),
        "createdAt": user.get("createdAt"),
        "updatedAt": user.get("updatedAt"),
        "name": user.get("name"),
        "image": user.get("image"),
        "articles": [str(aid) for aid in user.get("articles", [])],
        "products": user.get("products", [])
    }

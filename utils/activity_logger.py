from models.activity import ActivityModel
from typing import Optional, Dict, Any
import asyncio

class ActivityLogger:
    """Service to log activities throughout the application"""
    
    @staticmethod
    async def log_user_registration(user_id: str, username: str, email: str = None, phone: str = None):
        """Log user registration activity"""
        contact_info = email or phone or "N/A"
        registration_method = "email" if email else "phone number"
        activity_data = {
            "type": "user_registration",
            "title": "New User Registration",
            "description": f"'{username}' registered in the portal successfully using {registration_method}",
            "user_id": user_id,
            "user_name": username,
            "metadata": {
                "email": email,
                "phone": phone,
                "registration_method": "email" if email else "phone"
            },
            "icon": "user-plus"
        }
        return await ActivityModel.create_activity(activity_data)
    
    @staticmethod
    async def log_user_login(user_id: str, username: str):
        """Log user login activity"""
        activity_data = {
            "type": "user_login",
            "title": "User Login",
            "description": f"'{username}' logged in to the portal successfully",
            "user_id": user_id,
            "user_name": username,
            "metadata": {
                "login_time": True
            },
            "icon": "sign-in-alt"
        }
        return await ActivityModel.create_activity(activity_data)
    
    @staticmethod
    async def log_user_verification(user_id: str, username: str, verification_type: str):
        """Log user verification activity"""
        activity_data = {
            "type": "user_verification",
            "title": "Account Verification",
            "description": f"'{username}' successfully verified their {verification_type}",
            "user_id": user_id,
            "user_name": username,
            "metadata": {
                "verification_type": verification_type
            },
            "icon": "check-circle"
        }
        return await ActivityModel.create_activity(activity_data)
    
    @staticmethod
    async def log_product_creation(user_id: str, user_name: str, product_id: str, product_name: str):
        """Log product creation activity"""
        activity_data = {
            "type": "product_creation",
            "title": "Product Created",
            "description": f"successfully created a new product '{product_name}'",
            "user_id": user_id,
            "user_name": user_name,
            "entity_id": product_id,
            "entity_name": product_name,
            "metadata": {
                "action": "create"
            },
            "icon": "plus-circle"
        }
        return await ActivityModel.create_activity(activity_data)
    
    @staticmethod
    async def log_product_deletion(user_id: str, user_name: str, product_id: str, product_name: str):
        """Log product deletion activity"""
        activity_data = {
            "type": "product_deletion",
            "title": "Product Deleted",
            "description": f"successfully deleted product '{product_name}'",
            "user_id": user_id,
            "user_name": user_name,
            "entity_id": product_id,
            "entity_name": product_name,
            "metadata": {
                "action": "delete"
            },
            "icon": "trash-alt"
        }
        return await ActivityModel.create_activity(activity_data)
    
    @staticmethod
    async def log_article_creation(user_id: str, user_name: str, article_id: str, article_title: str):
        """Log article creation activity"""
        activity_data = {
            "type": "article_creation",
            "title": "Article Published",
            "description": f"successfully published a new article '{article_title}'",
            "user_id": user_id,
            "user_name": user_name,
            "entity_id": article_id,
            "entity_name": article_title,
            "metadata": {
                "action": "create"
            },
            "icon": "file-alt"
        }
        return await ActivityModel.create_activity(activity_data)
    
    @staticmethod
    async def log_article_deletion(user_id: str, user_name: str, article_id: str, article_title: str):
        """Log article deletion activity"""
        activity_data = {
            "type": "article_deletion",
            "title": "Article Removed",
            "description": f"successfully removed article '{article_title}'",
            "user_id": user_id,
            "user_name": user_name,
            "entity_id": article_id,
            "entity_name": article_title,
            "metadata": {
                "action": "delete"
            },
            "icon": "trash-alt"
        }
        return await ActivityModel.create_activity(activity_data)
    
    @staticmethod
    async def log_profile_update(user_id: str, user_name: str):
        """Log profile update activity"""
        activity_data = {
            "type": "profile_update",
            "title": "Profile Updated",
            "description": f"successfully updated their profile information",
            "user_id": user_id,
            "user_name": user_name,
            "metadata": {
                "action": "update"
            },
            "icon": "user-edit"
        }
        return await ActivityModel.create_activity(activity_data)
    
    @staticmethod
    async def log_password_change(user_id: str, user_name: str):
        """Log password change activity"""
        activity_data = {
            "type": "password_change",
            "title": "Password Updated",
            "description": f"successfully changed their account password",
            "user_id": user_id,
            "user_name": user_name,
            "metadata": {
                "action": "security_update"
            },
            "icon": "key"
        }
        return await ActivityModel.create_activity(activity_data)

# Helper function to safely log activities without breaking main flow
async def safe_log_activity(log_function, *args, **kwargs):
    """Safely log activity without affecting main application flow"""
    try:
        await log_function(*args, **kwargs)
    except Exception as e:
        print(f"Error logging activity: {e}")
        # Continue execution without failing the main operation
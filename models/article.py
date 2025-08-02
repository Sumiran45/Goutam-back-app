from database import db
from datetime import datetime
from models.user import user_helper

article_collection = db["articles"]

def article_helper(article) -> dict:
    """Helper function to convert MongoDB document to response format"""
    if not article:
        return None
    
    try:
        return {
            "id": str(article["_id"]),
            "heading": article.get("heading", ""),
            "body": article.get("body", ""),
            "date": article.get("date"),
            "author": article.get("author", {"id": "", "name": "Unknown", "username": "Unknown"}),
            "youtube_link": article.get("youtube_link")
        }
    except Exception as e:
        print(f"Error in article_helper: {str(e)}")
        print(f"Article data: {article}")
        return None
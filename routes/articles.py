from fastapi import APIRouter, HTTPException, Depends
from schemas.article import ArticleCreate, ArticleOut
from models.article import article_collection, article_helper
from models.user import user_collection
from datetime import datetime
from bson import ObjectId
from utils.auth import get_current_user
from utils.activity_logger import ActivityLogger, safe_log_activity
from typing import Optional, List
import re  # Added missing import

router = APIRouter()

@router.post("/CreateArticles", response_model=ArticleOut)
async def create_article(article: ArticleCreate, user=Depends(get_current_user)):
    try:
        if not article.heading or not article.heading.strip():
            raise HTTPException(status_code=400, detail="Title is required")
        
        if not article.body or not article.body.strip():
            raise HTTPException(status_code=400, detail="Content is required")

        youtube_url = None
        # Check both youtube_link and videoUrl fields
        youtube_link = article.youtube_link or article.videoUrl
        if youtube_link:
            youtube_pattern = r'^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+'
            if re.match(youtube_pattern, youtube_link.strip()):
                youtube_url = youtube_link.strip()
            else:
                raise HTTPException(status_code=400, detail="Invalid YouTube URL format")

        new_article = {
            "heading": article.heading.strip(),
            "body": article.body.strip(),
            "date": datetime.utcnow(),
            "author": {
                "id": str(user["_id"]),
                "name": user.get("name", "Unknown"),
                "username": user.get("username", "Unknown")
            },
            "youtube_link": youtube_url,
            "deleted": False
        }
        
        print(f"Creating article: {new_article}")
        
        result = await article_collection.insert_one(new_article)
        print(f"Created article with ID: {result.inserted_id}")
        
        created_article = await article_collection.find_one({"_id": result.inserted_id})
        
        if not created_article:
            raise HTTPException(status_code=500, detail="Failed to retrieve created article")

        # Update user's articles list
        await user_collection.update_one(
            {"_id": user["_id"]},
            {"$push": {"articles": result.inserted_id}}
        )

        # Log article creation activity
        await safe_log_activity(
            ActivityLogger.log_article_creation,
            user_id=str(user["_id"]),
            user_name=user.get("name", user.get("username", "Unknown")),
            article_id=str(result.inserted_id),
            article_title=article.heading.strip()
        )

        return article_helper(created_article)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error creating article: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create article")


@router.get("/articles", response_model=List[ArticleOut])
async def get_articles():
    try:
        cursor = article_collection.find({"deleted": {"$ne": True}}).sort("date", -1)
        articles = await cursor.to_list(length=None)
        return [article_helper(article) for article in articles]
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch articles")

        
@router.get("/articles/{article_id}", response_model=ArticleOut)
async def get_article_by_id(article_id: str):
    try:
        if not ObjectId.is_valid(article_id):
            raise HTTPException(status_code=400, detail="Invalid article ID")
        
        article = await article_collection.find_one({"_id": ObjectId(article_id), "deleted": {"$ne": True}})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        return article_helper(article)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching article: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch article")


@router.put("/articles/{article_id}", response_model=ArticleOut)
async def update_article(article_id: str, updated_data: ArticleCreate, user=Depends(get_current_user)):
    try:
        if not ObjectId.is_valid(article_id):
            raise HTTPException(status_code=400, detail="Invalid article ID")
        
        article = await article_collection.find_one({"_id": ObjectId(article_id)})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Check if article is deleted
        if article.get("deleted", False):
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Authorization check
        article_author_id = article.get("author", {}).get("id")
        if article_author_id != str(user["_id"]) and not user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Not authorized to update this article")

        # Validate input
        if not updated_data.heading or not updated_data.heading.strip():
            raise HTTPException(status_code=400, detail="Title is required")
        
        if not updated_data.body or not updated_data.body.strip():
            raise HTTPException(status_code=400, detail="Content is required")

        youtube_url = None
        youtube_link = updated_data.youtube_link or updated_data.videoUrl
        if youtube_link:
            youtube_pattern = r'^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+'
            if re.match(youtube_pattern, youtube_link.strip()):
                youtube_url = youtube_link.strip()
            else:
                raise HTTPException(status_code=400, detail="Invalid YouTube URL format")

        update_fields = {
            "heading": updated_data.heading.strip(),
            "body": updated_data.body.strip(),
            "youtube_link": youtube_url,
            "date": datetime.utcnow()  # Update the modification date
        }
        
        await article_collection.update_one(
            {"_id": ObjectId(article_id)}, 
            {"$set": update_fields}
        )
        
        updated_article = await article_collection.find_one({"_id": ObjectId(article_id)})

        # Log article update activity
        await safe_log_activity(
            ActivityLogger.log_article_update,
            user_id=str(user["_id"]),
            user_name=user.get("name", user.get("username", "Unknown")),
            article_id=str(article_id),
            article_title=updated_data.heading.strip()
        )

        return article_helper(updated_article)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating article: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update article")


@router.delete("/articles/{article_id}")
async def delete_article(article_id: str, user=Depends(get_current_user)):
    try:
        if not ObjectId.is_valid(article_id):
            raise HTTPException(status_code=400, detail="Invalid article ID")
        
        article = await article_collection.find_one({"_id": ObjectId(article_id)})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Check if article is already deleted
        if article.get("deleted", False):
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Authorization check
        article_author_id = article.get("author", {}).get("id")
        if article_author_id != str(user["_id"]) and not user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Not authorized to delete this article")

        # Store article title for logging before deletion
        article_title = article.get("heading", "Unknown Article")

        # Soft delete
        await article_collection.update_one(
            {"_id": ObjectId(article_id)}, 
            {"$set": {"deleted": True, "deleted_at": datetime.utcnow()}}
        )
        
        # Remove from user's articles list
        await user_collection.update_one(
            {"_id": user["_id"]},
            {"$pull": {"articles": ObjectId(article_id)}}
        )

        # Log article deletion activity
        await safe_log_activity(
            ActivityLogger.log_article_deletion,
            user_id=str(user["_id"]),
            user_name=user.get("name", user.get("username", "Unknown")),
            article_id=str(article_id),
            article_title=article_title
        )
        
        return {"message": "Article deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting article: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete article")
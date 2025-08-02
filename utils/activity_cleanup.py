import asyncio
from datetime import datetime, timedelta
from models.activity import ActivityModel
import logging

logger = logging.getLogger(__name__)

class ActivityCleanupTask:
    """Background task to automatically cleanup old activities"""
    
    def __init__(self):
        self.is_running = False
    
    async def cleanup_old_activities(self):
        """Cleanup activities older than 45 days"""
        try:
            deleted_count = await ActivityModel.cleanup_old_activities()
            logger.info(f"Cleaned up {deleted_count} old activities")
            return deleted_count
        except Exception as e:
            logger.error(f"Error during activity cleanup: {e}")
            return 0
    
    async def run_periodic_cleanup(self):
        """Run cleanup every 24 hours"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting periodic activity cleanup task")
        
        try:
            while self.is_running:
                await self.cleanup_old_activities()
                # Wait for 24 hours before next cleanup
                await asyncio.sleep(24 * 60 * 60)
        except Exception as e:
            logger.error(f"Error in periodic cleanup task: {e}")
        finally:
            self.is_running = False
    
    def start(self):
        """Start the background cleanup task"""
        if not self.is_running:
            asyncio.create_task(self.run_periodic_cleanup())
    
    def stop(self):
        """Stop the background cleanup task"""
        self.is_running = False

# Global instance
activity_cleanup_task = ActivityCleanupTask()

# Function to initialize the cleanup task
async def initialize_activity_cleanup():
    """Initialize the activity cleanup task"""
    activity_cleanup_task.start()
    logger.info("Activity cleanup task initialized")
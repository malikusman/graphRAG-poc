"""
Database connection and configuration
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from typing import Optional

from .config import settings

# Global database client
_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    global _database
    if _database is None:
        await connect_to_mongo()
    return _database


async def connect_to_mongo():
    """Create database connection"""
    global _client, _database
    
    try:
        _client = AsyncIOMotorClient(settings.MONGODB_URL)
        _database = _client[settings.MONGODB_DATABASE]
        
        # Test the connection
        await _client.admin.command('ping')
        print("✅ Connected to MongoDB successfully")
        
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Close database connection"""
    global _client
    if _client:
        _client.close()
        print("🔌 Disconnected from MongoDB")


def get_sync_database():
    """Get synchronous database instance for Celery tasks"""
    client = MongoClient(settings.MONGODB_URL)
    return client[settings.MONGODB_DATABASE]

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from core.config import settings
from core.models import User, Session, Artifact, Question, Answer, Score, Report, Embedding, Resume, JobDescription

# Global database client
client: AsyncIOMotorClient = None
database = None


async def connect_to_mongo():
    """Create database connection"""
    global client, database
    client = AsyncIOMotorClient(settings.mongo_uri)
    database = client.get_default_database()
    
    # Initialize Beanie with document models
    await init_beanie(
        database=database,
        document_models=[
            User,
            Session, 
            Artifact,
            Question,
            Answer,
            Score,
            Report,
            Embedding,
            Resume,
            JobDescription
        ]
    )


async def close_mongo_connection():
    """Close database connection"""
    global client
    if client:
        client.close()


async def get_database():
    """Get database instance"""
    return database


# For backward compatibility with existing code
def get_db():
    """Dependency to get database session - kept for compatibility"""
    return database
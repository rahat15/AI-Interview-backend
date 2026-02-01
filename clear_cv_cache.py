"""
Clear CV cache to force re-analysis with improved CV extraction
Run this after upgrading CV analysis to extract candidate names
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def clear_cv_cache():
    """Clear all CV analysis cache"""
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_uri)
    db = client["interview_db"]
    
    # Clear CV analysis cache
    result = await db.cv_cache.delete_many({})
    print(f"✅ Cleared {result.deleted_count} CV cache entries")
    
    # Also clear session cache to force fresh analysis
    result = await db.session_cache.delete_many({})
    print(f"✅ Cleared {result.deleted_count} session cache entries")
    
    client.close()
    print("\n🎯 Cache cleared! Next interview will use improved CV analysis with candidate names.")
    print("📋 You should see:")
    print("   - Full Gemini CV analysis response (with candidate name, email, skills)")
    print("   - Personalized greeting using actual name")
    print("   - Questions referencing specific experience")

if __name__ == "__main__":
    asyncio.run(clear_cv_cache())

#!/usr/bin/env python3
"""
MongoDB initialization script
Run this to set up indexes and initial data
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from core.models import User, Session, Artifact, Question, Answer, Score, Report, Embedding
from core.config import settings


async def create_indexes():
    """Create MongoDB indexes for better performance"""
    print("📊 Creating MongoDB indexes...")
    
    client = AsyncIOMotorClient(settings.mongo_uri)
    db = client.get_default_database()
    
    # Initialize Beanie
    await init_beanie(
        database=db,
        document_models=[User, Session, Artifact, Question, Answer, Score, Report, Embedding]
    )
    
    # Create additional indexes
    await db.users.create_index("email", unique=True)
    await db.sessions.create_index([("user_id", 1), ("created_at", -1)])
    await db.questions.create_index([("session_id", 1), ("order_index", 1)])
    await db.answers.create_index([("session_id", 1), ("question_id", 1)])
    await db.scores.create_index("answer_id")
    await db.reports.create_index("session_id", unique=True)
    await db.embeddings.create_index([("artifact_id", 1), ("chunk_idx", 1)])
    
    # Create text indexes for search
    await db.embeddings.create_index([("content", "text")])
    await db.artifacts.create_index([("text", "text")])
    
    print("✅ Indexes created successfully")
    
    client.close()


async def seed_demo_data():
    """Seed some demo data"""
    print("🌱 Seeding demo data...")
    
    # Create a demo user
    demo_user = User(
        email="demo@example.com",
        hashed_password="$2b$12$demo_hashed_password",  # This should be properly hashed
        full_name="Demo User",
        is_active=True,
        is_superuser=False
    )
    
    try:
        await demo_user.insert()
        print("✅ Demo user created")
    except Exception as e:
        print(f"ℹ️  Demo user might already exist: {e}")


async def main():
    """Main initialization function"""
    print("🚀 Initializing MongoDB for Interview Coach API...")
    
    try:
        await create_indexes()
        await seed_demo_data()
        print("🎉 MongoDB initialization completed!")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
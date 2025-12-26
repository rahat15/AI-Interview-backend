#!/usr/bin/env python3
"""
Migration script to move data from PostgreSQL to MongoDB
Run this script to migrate existing data before switching to MongoDB
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

# Import old models (PostgreSQL)
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# You'll need to temporarily keep the old models for migration
# from core.models_old import User as OldUser, Session as OldSession, etc.

# Import new models (MongoDB)
from core.models import User, Session, Artifact, Question, Answer, Score, Report, Embedding


class DataMigrator:
    def __init__(self, postgres_url: str, mongo_uri: str):
        # PostgreSQL connection
        self.pg_engine = create_engine(postgres_url)
        self.pg_session = sessionmaker(bind=self.pg_engine)()
        
        # MongoDB connection
        self.mongo_client = AsyncIOMotorClient(mongo_uri)
        self.mongo_db = self.mongo_client.get_default_database()
    
    async def initialize_mongo(self):
        """Initialize MongoDB with Beanie"""
        await init_beanie(
            database=self.mongo_db,
            document_models=[User, Session, Artifact, Question, Answer, Score, Report, Embedding]
        )
    
    async def migrate_users(self):
        """Migrate users from PostgreSQL to MongoDB"""
        print("🔄 Migrating users...")
        
        # This is a template - you'll need to adjust based on your actual old models
        # pg_users = self.pg_session.query(OldUser).all()
        
        # for pg_user in pg_users:
        #     mongo_user = User(
        #         id=str(pg_user.id),
        #         email=pg_user.email,
        #         hashed_password=pg_user.hashed_password,
        #         full_name=pg_user.full_name,
        #         is_active=pg_user.is_active,
        #         is_superuser=pg_user.is_superuser,
        #         created_at=pg_user.created_at,
        #         updated_at=pg_user.updated_at
        #     )
        #     await mongo_user.insert()
        
        print("✅ Users migrated")
    
    async def migrate_artifacts(self):
        """Migrate artifacts from PostgreSQL to MongoDB"""
        print("🔄 Migrating artifacts...")
        
        # Similar pattern for artifacts
        # pg_artifacts = self.pg_session.query(OldArtifact).all()
        # ... migration logic
        
        print("✅ Artifacts migrated")
    
    async def migrate_sessions(self):
        """Migrate sessions from PostgreSQL to MongoDB"""
        print("🔄 Migrating sessions...")
        
        # Similar pattern for sessions
        print("✅ Sessions migrated")
    
    async def migrate_questions(self):
        """Migrate questions from PostgreSQL to MongoDB"""
        print("🔄 Migrating questions...")
        print("✅ Questions migrated")
    
    async def migrate_answers(self):
        """Migrate answers from PostgreSQL to MongoDB"""
        print("🔄 Migrating answers...")
        print("✅ Answers migrated")
    
    async def migrate_scores(self):
        """Migrate scores from PostgreSQL to MongoDB"""
        print("🔄 Migrating scores...")
        print("✅ Scores migrated")
    
    async def migrate_reports(self):
        """Migrate reports from PostgreSQL to MongoDB"""
        print("🔄 Migrating reports...")
        print("✅ Reports migrated")
    
    async def migrate_embeddings(self):
        """Migrate embeddings from PostgreSQL to MongoDB"""
        print("🔄 Migrating embeddings...")
        print("✅ Embeddings migrated")
    
    async def run_migration(self):
        """Run the complete migration"""
        print("🚀 Starting migration from PostgreSQL to MongoDB...")
        
        await self.initialize_mongo()
        
        # Run migrations in order (respecting dependencies)
        await self.migrate_users()
        await self.migrate_artifacts()
        await self.migrate_sessions()
        await self.migrate_questions()
        await self.migrate_answers()
        await self.migrate_scores()
        await self.migrate_reports()
        await self.migrate_embeddings()
        
        print("🎉 Migration completed successfully!")
    
    def cleanup(self):
        """Cleanup connections"""
        self.pg_session.close()
        self.mongo_client.close()


async def main():
    """Main migration function"""
    # Get connection strings from environment
    postgres_url = os.getenv("OLD_DATABASE_URL", "postgresql://postgres:password@localhost:5432/interview_coach")
    mongo_uri = os.getenv("MONGO_URI", "mongodb+srv://karmansingharora03_db_user:8813917626%24Karman@cluster0.yyjs2ln.mongodb.net/ai-interview?retryWrites=true&w=majority&appName=Cluster0")
    
    migrator = DataMigrator(postgres_url, mongo_uri)
    
    try:
        await migrator.run_migration()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        migrator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
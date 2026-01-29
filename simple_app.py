#!/usr/bin/env python3
"""
Simple FastAPI app to test MongoDB connection
"""

import asyncio
import os
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

# Simple app without complex dependencies
app = FastAPI(
    title="Interview Coach API",
    version="1.0.0",
    root_path="/api",
    docs_url="/docs",
    openapi_url="/openapi.json",
)



# MongoDB connection
client = None
database = None

@app.on_event("startup")
async def startup_event():
    global client, database
    mongo_uri = os.getenv("MONGO_URI", "mongodb+srv://karmansingharora03_db_user:8813917626%24Karman@cluster0.yyjs2ln.mongodb.net/ai-interview?retryWrites=true&w=majority&appName=Cluster0")
    client = AsyncIOMotorClient(mongo_uri)
    database = client.get_default_database()
    print("✅ Connected to MongoDB")

@app.on_event("shutdown")
async def shutdown_event():
    global client
    if client:
        client.close()
    print("✅ Disconnected from MongoDB")

@app.get("/")
async def root():
    return {"message": "Interview Coach API is running!", "status": "ok"}

@app.get("/healthz")
async def health():
    return {"status": "healthy", "database": "connected" if database else "disconnected"}

@app.get("/test-mongo")
async def test_mongo():
    try:
        # Test MongoDB connection
        collections = await database.list_collection_names()
        return {
            "status": "success",
            "database_name": database.name,
            "collections": collections
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
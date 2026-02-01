#!/bin/bash

# AI Interview Coach API Startup Script
echo "🚀 Starting AI Interview Coach API..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing requirements..."
pip install -r requirements.txt

# Check if MongoDB is accessible
echo "🔍 Checking MongoDB connection..."
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
mongo_uri = os.getenv('MONGO_URI')
if mongo_uri:
    print('✅ MongoDB URI found in .env')
else:
    print('❌ MongoDB URI not found in .env')
    exit(1)
"

# Start Redis (if not running)
echo "🔴 Checking Redis..."
if ! pgrep -x "redis-server" > /dev/null; then
    echo "Starting Redis server..."
    redis-server --daemonize yes --port 6379
else
    echo "✅ Redis is already running"
fi

# Initialize MongoDB (optional)
echo "🗄️ Initializing MongoDB..."
python3 -m scripts.init_mongo

# Start the FastAPI application
echo "🌟 Starting FastAPI application..."
echo "📍 API will be available at: http://localhost:8000"
echo "📖 Swagger docs at: http://localhost:8000/docs"
echo "🔍 Health check at: http://localhost:8000/healthz"
echo ""

# Run with uvicorn
uvicorn apps.api.app:app --host 0.0.0.0 --port 8000 --reload
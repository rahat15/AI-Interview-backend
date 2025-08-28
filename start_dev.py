#!/usr/bin/env python3
"""
Development startup script for Interview Coach API.
This script helps you get started with the development environment.
"""

import os
import sys
import subprocess
import time

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error code: {e.returncode}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False

def check_docker():
    """Check if Docker is running"""
    print("🔍 Checking Docker status...")
    
    try:
        result = subprocess.run("docker --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker is available: {result.stdout.strip()}")
            
            # Check if Docker daemon is running
            result = subprocess.run("docker info", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Docker daemon is running")
                return True
            else:
                print("❌ Docker daemon is not running")
                print("Please start Docker Desktop or the Docker service")
                return False
        else:
            print("❌ Docker is not available")
            return False
    except Exception as e:
        print(f"❌ Error checking Docker: {e}")
        return False

def check_environment():
    """Check environment setup"""
    print("\n🔍 Checking environment setup...")
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        if os.path.exists("env.example"):
            print("⚠️  .env file not found, but env.example exists")
            print("Please copy env.example to .env and configure your environment variables")
            return False
        else:
            print("❌ Neither .env nor env.example found")
            return False
    
    print("✅ .env file found")
    
    # Check required environment variables
    required_vars = ["SECRET_KEY", "DATABASE_URL", "REDIS_URL"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file")
        return False
    
    print("✅ Required environment variables are set")
    return True

def main():
    """Main startup function"""
    print("🚀 Interview Coach API - Development Startup")
    print("=" * 50)
    
    # Check Docker
    if not check_docker():
        print("\n❌ Docker is required but not available.")
        print("Please install Docker Desktop or Docker Engine and try again.")
        return 1
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment is not properly configured.")
        print("Please fix the issues above and try again.")
        return 1
    
    print("\n✅ Environment is ready!")
    
    # Ask user what they want to do
    print("\nWhat would you like to do?")
    print("1. Start the full development stack (recommended)")
    print("2. Start only the database and Redis")
    print("3. Run tests")
    print("4. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            print("\n🚀 Starting full development stack...")
            if run_command("make dev-setup", "Starting development environment"):
                print("\n🎉 Development environment is ready!")
                print("\nServices available at:")
                print("- API: http://localhost:8080")
                print("- API Docs: http://localhost:8080/docs")
                print("- Health Check: http://localhost:8080/healthz")
                print("- Database: localhost:5432")
                print("- Redis: localhost:6379")
                print("\nTo stop the environment, run: make down")
                print("To view logs, run: make logs")
            else:
                print("\n❌ Failed to start development environment")
                return 1
            break
            
        elif choice == "2":
            print("\n🚀 Starting database and Redis only...")
            if run_command("make up", "Starting database and Redis"):
                print("\n✅ Database and Redis are running")
                print("To start the API, run: make up")
            else:
                print("\n❌ Failed to start database and Redis")
                return 1
            break
            
        elif choice == "3":
            print("\n🧪 Running tests...")
            if run_command("make test", "Running tests"):
                print("\n✅ Tests completed")
            else:
                print("\n❌ Tests failed")
                return 1
            break
            
        elif choice == "4":
            print("\n👋 Goodbye!")
            return 0
            
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

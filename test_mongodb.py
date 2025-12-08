#!/usr/bin/env python3
"""Test MongoDB connection with Python 3.11"""

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get MongoDB URI from environment
MONGODB_URI = os.environ.get("MONGODB_URI")

if not MONGODB_URI:
    print("❌ MONGODB_URI environment variable is not set")
    exit(1)

print(f"Testing MongoDB connection...")
print(f"URI (masked): {MONGODB_URI[:20]}...{MONGODB_URI[-10:]}")

try:
    # Standard MongoDB connection
    client = MongoClient(
        MONGODB_URI,
        server_api=ServerApi('1'),
        serverSelectionTimeoutMS=10000
    )
    
    # Test connection
    result = client.admin.command('ping')
    print(f"✅ Successfully connected to MongoDB!")
    print(f"Ping result: {result}")
    
    # List databases
    dbs = client.list_database_names()
    print(f"📊 Available databases: {dbs}")
    
except Exception as e:
    print(f"❌ MongoDB connection failed!")
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    import traceback
    traceback.print_exc()

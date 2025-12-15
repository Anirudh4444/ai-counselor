#!/usr/bin/env python3
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi
import traceback

MONGODB_URI = "mongodb+srv://anirudhkkman_db_user:RpFFHqrSSDWHdv5k@counsellor.h7b1kaj.mongodb.net/?retryWrites=true&w=majority&appName=counsellor"

print("Testing MongoDB connection...")
print(f"URI: {MONGODB_URI[:50]}...")

try:
    print("\n1. Trying with certifi certificates...")
    client = MongoClient(
        MONGODB_URI,
        server_api=ServerApi('1'),
        serverSelectionTimeoutMS=10000,
        tlsCAFile=certifi.where()
    )
    client.admin.command('ping')
    print("✓ SUCCESS with certifi!")
    
except Exception as e:
    print(f"✗ Failed with certifi: {type(e).__name__}")
    print(f"Error: {str(e)[:200]}")
    
    try:
        print("\n2. Trying without SSL verification (tlsAllowInvalidCertificates)...")
        client = MongoClient(
            MONGODB_URI + "&tlsAllowInvalidCertificates=true",
            server_api=ServerApi('1'),
            serverSelectionTimeoutMS=10000
        )
        client.admin.command('ping')
        print("✓ SUCCESS without SSL verification!")
        
    except Exception as e2:
        print(f"✗ Failed: {type(e2).__name__}")
        print(f"Error: {str(e2)[:200]}")
        print("\nFull traceback:")
        traceback.print_exc()

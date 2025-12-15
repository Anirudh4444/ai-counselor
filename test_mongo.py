#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/anirudhkumar/.gemini/antigravity/scratch')

from db_config import mongodb_available, client

print(f"\nMongoDB Available: {mongodb_available}")

if mongodb_available:
    print("✓ MongoDB connection successful!")
    print(f"✓ Database: {client.counsellor_db.name}")
    print(f"✓ Collections: {client.counsellor_db.list_collection_names()}")
else:
    print("✗ MongoDB connection failed")

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv
import ssl
import certifi

# Load environment variables
load_dotenv()

# Get MongoDB URI from environment
MONGODB_URI = os.environ.get("MONGODB_URI")

if not MONGODB_URI:
    raise ValueError(
        "MONGODB_URI environment variable is not set. "
        "Please set it in your .env file."
    )

# Create MongoDB client with standard configuration
try:
    # Standard MongoDB connection - works well with Python 3.11
    client = MongoClient(
        MONGODB_URI,
        server_api=ServerApi('1'),
        serverSelectionTimeoutMS=10000
    )
    
    # Test connection
    client.admin.command('ping')
    print("✓ Successfully connected to MongoDB!")
    
    # Database instance
    db = client.counsellor_db
    
    # Collections
    users_collection = db.users
    chat_history_collection = db.chat_history
    session_summary_collection = db.session_summaries
    
    mongodb_available = True
    
except Exception as e:
    print(f"✗ MongoDB connection failed: {e}")
    print("⚠️  Server will start without database functionality")
    
    # Set collections to None to allow server to start
    client = None
    db = None
    users_collection = None
    chat_history_collection = None
    session_summary_collection = None
    mongodb_available = False

# Create indexes for better performance
def setup_indexes():
    """Create database indexes for optimized queries"""
    if not mongodb_available:
        print("⚠️  Skipping index creation - MongoDB not available")
        return
        
    try:
        # User collection indexes
        users_collection.create_index("username", unique=True)
        users_collection.create_index("email", unique=True)
        
        # Chat history indexes
        chat_history_collection.create_index("user_id")
        chat_history_collection.create_index("timestamp")
        
        # Session summary indexes
        session_summary_collection.create_index("user_id")
        session_summary_collection.create_index("session_date")
        
        print("✓ Database indexes created successfully")
    except Exception as e:
        print(f"Warning: Index creation failed: {e}")

# Initialize indexes on import
setup_indexes()

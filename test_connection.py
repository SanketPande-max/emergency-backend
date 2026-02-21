"""
Test MongoDB connection script
Run this to verify your database connection is working
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from pymongo import MongoClient

def test_connection():
    """Test MongoDB connection"""
    try:
        print("=" * 50)
        print("Testing MongoDB Connection...")
        print("=" * 50)
        print(f"Connection URI: {Config.MONGO_URI[:50]}...")
        print()
        
        # Create MongoDB client
        client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000)
        
        # Test connection with ping
        client.admin.command('ping')
        print("✓ Connection successful!")
        print()
        
        # Get database
        db = client.emergodb
        print(f"✓ Database: {db.name}")
        print()
        
        # List collections
        collections = db.list_collection_names()
        print(f"✓ Collections found: {len(collections)}")
        if collections:
            print(f"  Collections: {', '.join(collections)}")
        else:
            print("  (No collections yet - they will be created automatically)")
        print()
        
        # Test write operation
        test_collection = db.test_connection
        test_collection.insert_one({"test": "connection", "timestamp": "now"})
        test_collection.delete_one({"test": "connection"})
        print("✓ Write/Delete test successful!")
        print()
        
        print("=" * 50)
        print("✓ All tests passed! Database is ready to use.")
        print("=" * 50)
        
        client.close()
        return True
        
    except Exception as e:
        print("=" * 50)
        print("✗ Connection failed!")
        print("=" * 50)
        print(f"Error: {str(e)}")
        print()
        print("Troubleshooting:")
        print("1. Check your MongoDB Atlas cluster is running")
        print("2. Verify your IP is whitelisted in MongoDB Atlas")
        print("3. Check your username and password are correct")
        print("4. Ensure you have internet connectivity")
        print("5. Try running: pip install dnspython")
        return False

if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)

import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")


def get_db_client():
    """Establishes and returns a MongoDB client connection."""

    if not MONGO_URI:
        raise ValueError("MONGO_URI is not set in environment variables. Check your .env file.")

    try:
        client = MongoClient(MONGO_URI)
        client.admin.command('ping')
        return client

    except ConnectionFailure as e:
        print(f"Failed to connect to MongoDB: {e}")
        return None
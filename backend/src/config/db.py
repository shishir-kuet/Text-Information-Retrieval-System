from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "book_search_system"


def get_db():
    """Return the book_search_system database instance."""
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]

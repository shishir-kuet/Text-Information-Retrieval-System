from pymongo import MongoClient

from app.config.settings import settings

_client = None


def get_mongo_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.mongo_uri)
    return _client


def get_database():
    return get_mongo_client()[settings.db_name]

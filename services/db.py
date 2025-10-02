from pymongo import MongoClient
from config import Config

_client = None
_db = None

def get_db():
    global _client, _db
    if _db is None:
        _client = MongoClient(Config.MONGO_URI)
        _db = _client[Config.DB_NAME]
        _db.conversations.create_index([("user_id", 1), ("updated_at", -1)])
        _db.characters.create_index([("key", 1)], unique=True)
    return _db

from character_settings import get_default_characters
from services.db import get_db


if __name__ == "__main__":
    db = get_db()
    for character in get_default_characters():
        db.characters.update_one({"key": character["key"]}, {"$set": character}, upsert=True)
    print("Seeded characters.")

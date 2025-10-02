import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MONGO_URI = os.getenv("MONGO_URI")
    DB_NAME = os.getenv("DB_NAME", "ai_character_mvp")
    USE_GUEST_AUTH = os.getenv("USE_GUEST_AUTH", "false").lower() == "true"

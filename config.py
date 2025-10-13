import json
import os
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MONGO_URI = os.getenv("MONGO_URI")
    DB_NAME = os.getenv("DB_NAME", "ai_character_mvp")
    USE_GUEST_AUTH = os.getenv("USE_GUEST_AUTH", "false").lower() == "true"


    CONTEXT_MESSAGE_LIMIT = int(os.getenv("CONTEXT_MESSAGE_LIMIT", "15"))
    CONVERSATION_TRIM_COUNT = int(os.getenv("CONVERSATION_TRIM_COUNT", "30"))

    FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
    FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
    FIREBASE_AUTH_DOMAIN = os.getenv("FIREBASE_AUTH_DOMAIN")
    FIREBASE_APP_ID = os.getenv("FIREBASE_APP_ID")
    FIREBASE_MESSAGING_SENDER_ID = os.getenv("FIREBASE_MESSAGING_SENDER_ID")
    FIREBASE_MEASUREMENT_ID = os.getenv("FIREBASE_MEASUREMENT_ID")

    FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH")
    FIREBASE_CREDENTIALS_JSON = os.getenv("FIREBASE_CREDENTIALS_JSON")

    @classmethod
    def firebase_enabled(cls) -> bool:
        # ตรวจสอบว่ามีการตั้งค่าข้อมูล Firebase ครบถ้วนพอที่จะเปิดใช้งานได้หรือไม่
        return bool(
            cls.FIREBASE_PROJECT_ID
            and (cls.FIREBASE_CREDENTIALS_PATH or cls.FIREBASE_CREDENTIALS_JSON)
        )

    @classmethod
    def firebase_client_config(cls) -> Dict[str, Optional[str]]:
        # จัดเตรียมคอนฟิกฝั่งไคลเอนต์สำหรับเปิดใช้งาน Firebase บนหน้าเว็บ
        return {
            "apiKey": cls.FIREBASE_API_KEY,
            "authDomain": cls.FIREBASE_AUTH_DOMAIN,
            "projectId": cls.FIREBASE_PROJECT_ID,
            "appId": cls.FIREBASE_APP_ID,
            "messagingSenderId": cls.FIREBASE_MESSAGING_SENDER_ID,
            "measurementId": cls.FIREBASE_MEASUREMENT_ID,
        }

    @classmethod
    def firebase_credentials(cls) -> Optional[Dict[str, object]]:
        # แปลงข้อมูลไฟล์รับรองความถูกต้องของ Firebase จากตัวแปรสภาพแวดล้อมเป็นพจนานุกรม
        if cls.FIREBASE_CREDENTIALS_JSON:
            try:
                return json.loads(cls.FIREBASE_CREDENTIALS_JSON)
            except json.JSONDecodeError:
                return None
        return None


if os.getenv("DEBUG_ENV_PRINT", "").lower() == "true":
    masked = (Config.OPENAI_API_KEY or "")
    if masked:
        print(f"DEBUG OPENAI KEY: {masked[:6]}***")
    else:
        print("DEBUG OPENAI KEY: <empty>")

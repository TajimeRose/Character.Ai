from typing import Dict, List

from flask import Flask, Response, abort, render_template, request
from jinja2 import TemplateNotFound

from config import Config
from routes.chat import chat_bp
from routes.characters import characters_bp
from routes.conversations import convo_bp
from services.db import get_db


BETA_BANNER_TEXT = "This is a beta version created for portfolio presentation."


def _serialize_character(raw: Dict) -> Dict:
    # แปลงข้อมูลตัวละครจากฐานข้อมูลให้อยู่ในรูปแบบที่ฝั่งเว็บต้องการ
    avatar = raw.get("avatar_url") or raw.get("avatarUrl") or raw.get("image") or "images/characters/placeholder.svg"
    return {
        "key": raw.get("key"),
        "name": raw.get("name"),
        "description": raw.get("description"),
        "tagline": raw.get("tagline"),
        "avatarUrl": avatar,
        "themeColor": raw.get("theme_color"),
    }


def _load_characters() -> List[Dict]:
    # ดึงรายการตัวละครทั้งหมดจากฐานข้อมูลหรือหน่วยความจำ
    db = get_db()
    characters = []
    for character in db.characters.find():
        characters.append(_serialize_character(character))
    return characters


def create_app():
    # สร้างและตั้งค่าตัวแอปพลิเคชัน Flask พร้อมผูกบลูพริ้นต์
    app = Flask(__name__)
    app.config.from_object(Config)
    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(convo_bp, url_prefix="/api")
    app.register_blueprint(characters_bp, url_prefix="/api")

    @app.context_processor
    def inject_globals():
        # ป้อนค่าคอนฟิกที่จำเป็นให้เทมเพลตสามารถเรียกใช้งานได้ทั่วทั้งระบบ
        return {
            "use_guest": Config.USE_GUEST_AUTH,
            "firebase_config": Config.firebase_client_config(),
            "firebase_enabled": Config.firebase_enabled(),
            "beta_banner_text": BETA_BANNER_TEXT,
        }

    @app.route("/")
    def home():
        # แสดงหน้าแรกพร้อมรายการตัวละครที่พร้อมให้เลือกคุยได้ทันที
        return render_template(
            "index.html",
            page_id="home",
            characters=_load_characters(),
        )

    @app.route("/chat/<character_key>")
    def chat_page(character_key: str):
        # แสดงหน้าพูดคุยกับตัวละครที่เลือกและเตรียมประวัติสนทนาเริ่มต้น
        db = get_db()
        character = db.characters.find_one({"key": character_key})
        if not character:
            abort(404)
        initial_conversation_id = request.args.get("conversation")
        template_candidates = [f"characters/{character_key}.html", "chat.html"]
        try:
            return render_template(
                template_candidates,
                page_id="chat",
                character=_serialize_character(character),
                initial_conversation_id=initial_conversation_id,
            )
        except TemplateNotFound:
            return render_template(
                "chat.html",
                page_id="chat",
                character=_serialize_character(character),
                initial_conversation_id=initial_conversation_id,
            )

    @app.route("/history")
    def history_page():
        # แสดงหน้าประวัติการสนทนาของผู้ใช้
        return render_template(
            "history.html",
            page_id="history",
            characters=_load_characters(),
        )

    @app.route("/favicon.ico")
    def favicon():
        # ป้องกันการคืนค่า favicon ที่ไม่จำเป็นด้วยการส่งสถานะว่างกลับ
        return Response(status=204)

    return app


if __name__ == "__main__":
    create_app().run(debug=True)

from flask import Blueprint, jsonify

from services.db import get_db


characters_bp = Blueprint("characters", __name__)


def _serialize_character(character):
    # แปลงเอกสารตัวละครสำหรับการส่งออกฝั่งไคลเอนต์
    avatar = character.get("avatar_url") or character.get("avatarUrl") or character.get("image") or "images/characters/placeholder.svg"
    return {
        "key": character.get("key"),
        "name": character.get("name"),
        "description": character.get("description"),
        "tagline": character.get("tagline"),
        "avatarUrl": avatar,
        "themeColor": character.get("theme_color"),
    }


@characters_bp.route("/characters", methods=["GET"])
def list_characters():
    # ดึงรายการตัวละครทั้งหมดและคืนข้อมูลสำหรับแสดงผลบนหน้าเว็บ
    db = get_db()
    items = []
    for character in db.characters.find():
        items.append(_serialize_character(character))
    return jsonify(items)

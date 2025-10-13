from datetime import datetime
from typing import Any, Dict

from bson import ObjectId
from flask import Blueprint, jsonify, request

from services.auth import require_user
from services.db import get_db

convo_bp = Blueprint("conversations", __name__)


def _iso(dt):
    # แปลงค่าเวลาให้เป็นสตริง ISO 8601 หากอินพุตเป็น datetime
    return dt.isoformat() if isinstance(dt, datetime) else dt


def _serialize_message(message: Dict[str, Any]) -> Dict[str, Any]:
    # เตรียมรูปแบบข้อความสนทนาให้พร้อมส่งกลับไปยังฝั่งไคลเอนต์
    return {
        "role": message.get("role"),
        "text": message.get("text"),
        "ts": _iso(message.get("ts")),
    }


def _resolve_character_name(db, key: str) -> str:
    # แปลงคีย์ของตัวละครให้เป็นชื่อที่อ่านได้ หากไม่พบให้คืนคีย์เดิม
    if not key:
        return "Unknown character"
    character = db.characters.find_one({"key": key})
    return character.get("name") if character else key


@convo_bp.route("/conversations", methods=["GET"])
@require_user
def list_conversations(user):
    # ดึงรายการสนทนาของผู้ใช้เรียงลำดับตามการอัปเดตล่าสุด
    db = get_db()
    try:
        limit = int(request.args.get("limit", 20))
    except (TypeError, ValueError):
        limit = 20

    limit = max(1, min(limit, 100))

    cursor = (
        db.conversations
        .find({"user_id": user["_id"]})
        .sort("updated_at", -1)
        .limit(limit)
    )

    items = []
    for conv in cursor:
        items.append({
            "id": str(conv["_id"]),
            "character_key": conv.get("character_key"),
            "character_name": _resolve_character_name(db, conv.get("character_key")),
            "title": conv.get("title"),
            "updated_at": _iso(conv.get("updated_at")),
        })
    return jsonify(items)


@convo_bp.route("/conversations/<conv_id>", methods=["GET"])
@require_user
def get_conversation(user, conv_id):
    # คืนรายละเอียดบทสนทนาหนึ่งรายการพร้อมข้อความทั้งหมด
    try:
        oid = ObjectId(conv_id)
    except Exception:
        return jsonify({"error": "That conversation reference looks invalid."}), 400

    db = get_db()
    conv = db.conversations.find_one({"_id": oid, "user_id": user["_id"]})
    if not conv:
        return jsonify({"error": "We could not find that conversation."}), 404

    return jsonify({
        "id": str(conv["_id"]),
        "character_key": conv.get("character_key"),
        "character_name": _resolve_character_name(db, conv.get("character_key")),
        "title": conv.get("title"),
        "messages": [_serialize_message(m) for m in conv.get("messages", [])],
        "created_at": _iso(conv.get("created_at")),
        "updated_at": _iso(conv.get("updated_at")),
    })


@convo_bp.route("/conversations/<conv_id>", methods=["DELETE"])
@require_user
def delete_conversation(user, conv_id):
    # ลบบทสนทนาตามไอดีออกจากฐานข้อมูลของผู้ใช้
    try:
        oid = ObjectId(conv_id)
    except Exception:
        return jsonify({"error": "That conversation reference looks invalid."}), 400

    db = get_db()
    result = db.conversations.delete_one({"_id": oid, "user_id": user["_id"]})
    deleted = getattr(result, "deleted_count", 0)
    if not deleted:
        return jsonify({"error": "Conversation already removed."}), 404
    return ("", 204)

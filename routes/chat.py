from datetime import datetime
from typing import Optional

from bson import ObjectId
from flask import Blueprint, jsonify, request

from character_settings import get_character
from services.auth import require_user
from services.db import get_db
from services.llm_client import chat_complete

chat_bp = Blueprint("chat", __name__)


def _to_object_id(raw_id: Optional[str]) -> Optional[ObjectId]:
    # พยายามแปลงสตริงให้เป็น ObjectId หากรูปแบบถูกต้อง
    if not raw_id:
        return None
    try:
        return ObjectId(raw_id)
    except Exception:
        return None


@chat_bp.route("/chat", methods=["POST"])
@require_user
def send_message(user):
    # รับข้อความจากผู้ใช้ ประกอบบริบท แล้วส่งให้โมเดลตอบกลับ
    db = get_db()
    payload = request.get_json(silent=True) or {}
    character_key = (payload.get("character_key") or "").strip()
    text = (payload.get("text") or "").strip()
    conversation_id = (payload.get("conversation_id") or "").strip()

    if not character_key or not text:
        return jsonify({"error": "Please choose a character and share a message to continue."}), 400

    character_doc = db.characters.find_one({"key": character_key})
    character_profile = get_character(character_key)
    if not character_doc or not character_profile:
        return jsonify({"error": "We could not find that character."}), 404

    conversation = None
    if conversation_id:
        conversation_oid = _to_object_id(conversation_id)
        if conversation_oid:
            conversation = db.conversations.find_one({
                "_id": conversation_oid,
                "user_id": user["_id"],
            })
        if conversation is None:
            return jsonify({"error": "Conversation no longer exists."}), 404

    if conversation is None:
        now = datetime.utcnow()
        conversation = {
            "_id": ObjectId(),
            "user_id": user["_id"],
            "character_key": character_key,
            "title": character_doc.get("name") or character_key,
            "messages": [],
            "created_at": now,
            "updated_at": now,
        }
        db.conversations.insert_one(conversation)

    conversation_oid = conversation["_id"]
    stored_messages = (conversation.get("messages") or [])[-10:]

    history_payload = [
        {"role": msg.get("role"), "content": msg.get("text", "")}
        for msg in stored_messages
        if msg.get("role") in {"user", "assistant"}
    ]

    try:
        reply = chat_complete(
            character_key=character_key,
            history=history_payload,
            user_message=text,
        )
    except Exception:
        return jsonify({"error": "Our AI companion stumbled while replying. Please try again."}), 502

    now = datetime.utcnow()
    messages_to_store = [
        {"role": "user", "text": text, "ts": now},
        {"role": "assistant", "text": reply, "ts": now},
    ]

    update_doc = {
        "$push": {
            "messages": {
                "$each": messages_to_store,
                "$slice": -20,
            }
        },
        "$set": {"updated_at": now},
    }
    if not stored_messages:
        update_doc["$set"]["title"] = text[:80] or character_doc.get("name") or character_key

    db.conversations.update_one({"_id": conversation_oid}, update_doc, upsert=False)

    return jsonify({
        "conversation_id": str(conversation_oid),
        "assistant": reply,
    })

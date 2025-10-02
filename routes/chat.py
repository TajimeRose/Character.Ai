from flask import Blueprint, request, jsonify
from datetime import datetime
from bson import ObjectId
from services.db import get_db
from services.llm_client import chat_complete
from services.auth import require_user

chat_bp = Blueprint("chat", __name__)

def to_oid(s):
    try:
        return ObjectId(s)
    except Exception:
        return None

@chat_bp.route("/chat", methods=["POST"])
@require_user
def send_message(user):
    db = get_db()
    data = request.get_json(force=True)
    character_key = data.get("character_key")
    text = data.get("text", "").strip()
    conversation_id = data.get("conversation_id")

    if not character_key or not text:
        return jsonify({"error":"character_key and text are required"}), 400

    # โหลด persona
    char = db.characters.find_one({"key": character_key})
    if not char:
        return jsonify({"error":"character not found"}), 404

    # สร้าง/โหลดเธรด
    conv = None
    if conversation_id:
        oid = to_oid(conversation_id)
        conv = db.conversations.find_one({"_id": oid, "user_id": user["_id"]})
    if not conv:
        conv = {
            "user_id": user["_id"],
            "character_key": character_key,
            "title": f"{char['name']} {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            "messages": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        conversation_id = db.conversations.insert_one(conv).inserted_id
        conv = db.conversations.find_one({"_id": conversation_id})

    # เตรียมข้อความย้อนหลัง (ตัดย่อแค่ล่าสุด 10 ข้อความเพื่อประหยัดโควตา)
    history = conv.get("messages", [])[-10:]
    msgs = [{"role":"system","content": char["system_prompt"]}]
    for m in history:
        msgs.append({"role": m["role"], "content": m["text"]})
    msgs.append({"role":"user","content": text})

    # เรียก OpenAI
    reply = chat_complete(
        msgs,
        temperature=char.get("default_settings", {}).get("temperature", 0.7),
        max_tokens=char.get("default_settings", {}).get("max_tokens", 600)
    )

    # บันทึกทั้งคู่
    now = datetime.utcnow()
    db.conversations.update_one(
        {"_id": conv["_id"]},
        {"$push": {"messages": {"role":"user","text":text,"ts":now},
                   "messages": {"role":"assistant","text":reply,"ts":now}},
         "$set": {"updated_at": now}}
    )

    return jsonify({
        "conversation_id": str(conv["_id"]),
        "assistant": reply
    })

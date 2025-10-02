from flask import Blueprint, request, jsonify
from services.db import get_db
from services.auth import require_user
from bson import ObjectId

convo_bp = Blueprint("conversations", __name__)

def _to_public(conv):
    return {
        "_id": str(conv["_id"]),
        "character_key": conv["character_key"],
        "title": conv.get("title"),
        "updated_at": conv.get("updated_at"),
    }

@convo_bp.route("/conversations", methods=["GET"])
@require_user
def list_conversations(user):
    db = get_db()
    limit = int(request.args.get("limit", 20))
    cur = db.conversations.find({"user_id": user["_id"]}).sort("updated_at", -1).limit(limit)
    return jsonify([_to_public(c) for c in cur])

@convo_bp.route("/conversations/<conv_id>", methods=["GET"])
@require_user
def get_conversation(user, conv_id):
    db = get_db()
    try:
        oid = ObjectId(conv_id)
    except:
        return jsonify({"error":"invalid id"}), 400
    conv = db.conversations.find_one({"_id": oid, "user_id": user["_id"]})
    if not conv:
        return jsonify({"error":"not found"}), 404
    conv["_id"] = str(conv["_id"])
    # แปลง ts เป็น iso string ถ้าต้องการในอนาคต
    return jsonify(conv)

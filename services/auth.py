from functools import wraps
from flask import request, jsonify
from config import Config
from services.db import get_db

def _ensure_user(provider_id, email=None, name=None):
    db = get_db()
    u = db.users.find_one({"provider_id": provider_id})
    if not u:
        u = {
            "provider_id": provider_id,
            "email": email,
            "name": name or "User",
        }
        db.users.insert_one(u)
        u = db.users.find_one({"provider_id": provider_id})
    return u

def require_user(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # เบื้องต้น: รับ header Authorization: Bearer <uid or token>
        # เบต้าระดับรีบ: treat it as uid (จาก Firebase client)
        auth = request.headers.get("Authorization", "")
        if Config.USE_GUEST_AUTH and not auth:
            # สร้าง guest อัตโนมัติ
            user = _ensure_user("guest_demo", email=None, name="Guest")
            return f(user=user, *args, **kwargs)

        if not auth.startswith("Bearer "):
            return jsonify({"error":"Missing token"}), 401

        token = auth.split(" ",1)[1].strip()
        if not token:
            return jsonify({"error":"Invalid token"}), 401

        # สำหรับเดโม: ใช้ token เป็น provider_id ตรงๆ
        # ถ้าเชื่อม Firebase จริง ให้ verify token แล้วดึง uid/email แทน
        user = _ensure_user(provider_id=token, email=None, name=None)
        return f(user=user, *args, **kwargs)
    return wrapper

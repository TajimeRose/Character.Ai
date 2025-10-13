from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Dict, Optional

from flask import jsonify, request

from config import Config
from services.db import get_db

try:  # pragma: no cover - optional dependency in some environments
    import firebase_admin
    from firebase_admin import auth as firebase_auth
    from firebase_admin import credentials
except ImportError:  # pragma: no cover
    firebase_admin = None  # type: ignore
    firebase_auth = None  # type: ignore
    credentials = None  # type: ignore


_logger = logging.getLogger(__name__)
_firebase_app: Optional[firebase_admin.App] = None


def _ensure_user(provider_id: str, email: Optional[str] = None, name: Optional[str] = None) -> Dict[str, Any]:
    db = get_db()
    user = db.users.find_one({"provider_id": provider_id})
    if not user:
        doc = {
            "provider_id": provider_id,
            "email": email,
            "name": name or ("Guest" if provider_id.startswith("guest:") else "Explorer"),
        }
        db.users.insert_one(doc)
        user = db.users.find_one({"provider_id": provider_id})
    return user  # type: ignore[return-value]


def _initialize_firebase_app() -> Optional[firebase_admin.App]:
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app
    if not Config.firebase_enabled():
        return None
    if firebase_admin is None or credentials is None:
        _logger.warning("Firebase Admin SDK not installed; cannot verify ID tokens.")
        return None
    try:
        cred_obj = None
        cred_payload = Config.firebase_credentials()
        if cred_payload:
            cred_obj = credentials.Certificate(cred_payload)
        elif Config.FIREBASE_CREDENTIALS_PATH:
            cred_obj = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
        else:
            cred_obj = credentials.ApplicationDefault()
        options = {}
        if Config.FIREBASE_PROJECT_ID:
            options["projectId"] = Config.FIREBASE_PROJECT_ID
        _firebase_app = firebase_admin.initialize_app(cred_obj, options or None)
        return _firebase_app
    except Exception:  # pragma: no cover - initialization edge cases
        _logger.exception("Unable to initialize Firebase Admin app")
        return None


def _verify_token(token: str) -> Optional[Dict[str, Any]]:
    if token.startswith("guest:"):
        return {"uid": token, "email": None, "name": "Guest"}
    if Config.firebase_enabled() and firebase_auth is not None:
        app = _initialize_firebase_app()
        if app is None:
            return None
        try:
            decoded = firebase_auth.verify_id_token(token, app=app)
            if not decoded:
                return None
            return {
                "uid": decoded.get("uid") or decoded.get("sub") or decoded.get("user_id"),
                "email": decoded.get("email"),
                "name": decoded.get("name"),
            }
        except Exception:
            _logger.warning("Failed to verify Firebase ID token", exc_info=True)
            return None
    # Fallback: treat token as provider id (useful for local testing)
    return {"uid": token, "email": None, "name": None}


def require_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "").strip()

        def _guest_response():
            guest = _ensure_user("guest:demo", name="Guest")
            return func(user=guest, *args, **kwargs)

        if not auth_header or not auth_header.startswith("Bearer "):
            if Config.USE_GUEST_AUTH:
                return _guest_response()
            return jsonify({"error": "Authentication required."}), 401

        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            if Config.USE_GUEST_AUTH:
                return _guest_response()
            return jsonify({"error": "Missing bearer token."}), 401

        payload = _verify_token(token)
        if not payload or not payload.get("uid"):
            if Config.USE_GUEST_AUTH:
                return _guest_response()
            return jsonify({"error": "Invalid or expired token."}), 401

        user = _ensure_user(
            provider_id=str(payload.get("uid")),
            email=payload.get("email"),
            name=payload.get("name"),
        )
        return func(user=user, *args, **kwargs)

    return wrapper

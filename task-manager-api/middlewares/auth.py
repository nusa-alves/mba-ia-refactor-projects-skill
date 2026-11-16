from functools import wraps
from hmac import compare_digest
from flask import current_app, jsonify, request

def require_admin(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN", "")
        supplied = request.headers.get("X-Admin-Token", "")
        if not expected or not supplied or not compare_digest(expected, supplied):
            return jsonify({"error": "Acesso negado"}), 403
        return view(*args, **kwargs)
    return wrapped

from functools import wraps

from flask import current_app, jsonify, request


def require_admin(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        configured_token = current_app.config.get("ADMIN_TOKEN", "")
        supplied_token = request.headers.get("X-Admin-Token", "")
        if not configured_token or supplied_token != configured_token:
            return jsonify({"erro": "Acesso negado", "sucesso": False}), 403
        return view(*args, **kwargs)
    return wrapped


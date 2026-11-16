import re
import logging

from flask import jsonify, request

from controllers.errors import ApiError
from models import admin_model

logger = logging.getLogger(__name__)


def reset_database():
    admin_model.reset_database()
    logger.warning("Banco de dados resetado por solicitação administrativa")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


def executar_query():
    data = request.get_json(silent=True)
    query = data.get("sql", "") if isinstance(data, dict) else ""
    if not isinstance(query, str) or not query:
        raise ApiError("Query não informada")
    if not re.match(r"^\s*SELECT\b", query, re.IGNORECASE):
        raise ApiError("Somente consultas SELECT são permitidas")
    rows = admin_model.execute_read_query(query)
    if rows is None:
        raise ApiError("Somente consultas SELECT são permitidas")
    return jsonify({"dados": rows, "sucesso": True}), 200


def health_check():
    try:
        counts = admin_model.health_counts()
        return jsonify({
            "status": "ok", "database": "connected", "counts": counts,
            "versao": "1.0.0",
        }), 200
    except Exception:
        logger.exception("Falha ao verificar saúde do banco")
        return jsonify({"status": "erro", "detalhes": "Falha ao consultar o banco"}), 500


def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja", "versao": "1.0.0",
        "endpoints": {
            "produtos": "/produtos", "usuarios": "/usuarios", "pedidos": "/pedidos",
            "login": "/login", "relatorios": "/relatorios/vendas", "health": "/health",
        },
    })


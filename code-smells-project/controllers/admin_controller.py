import logging

from flask import jsonify

from models import admin_model

logger = logging.getLogger(__name__)


def reset_database():
    admin_model.reset_database()
    logger.warning("Banco de dados resetado por solicitação administrativa")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


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


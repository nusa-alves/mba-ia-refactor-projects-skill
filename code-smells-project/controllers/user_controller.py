import logging
import re

from flask import jsonify, request

from controllers.errors import ApiError
from models import user_model

logger = logging.getLogger(__name__)


def listar_usuarios():
    return jsonify({"dados": user_model.get_all(), "sucesso": True}), 200


def buscar_usuario(user_id):
    user = user_model.get_by_id(user_id)
    if user:
        return jsonify({"dados": user, "sucesso": True}), 200
    return jsonify({"erro": "Usuário não encontrado"}), 404


def criar_usuario():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError("Dados inválidos")
    name, email, password = data.get("nome", ""), data.get("email", ""), data.get("senha", "")
    if not all(isinstance(value, str) and value for value in (name, email, password)):
        raise ApiError("Nome, email e senha são obrigatórios")
    if len(name) > 200 or len(email) > 254 or len(password) > 1024:
        raise ApiError("Dados inválidos")
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise ApiError("Email inválido")
    user_id = user_model.create(name, email, password)
    logger.info("Usuário criado: %s", email)
    return jsonify({"dados": {"id": user_id}, "sucesso": True}), 201


def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError("Email e senha são obrigatórios")
    email, password = data.get("email", ""), data.get("senha", "")
    if not all(isinstance(value, str) and value for value in (email, password)):
        raise ApiError("Email e senha são obrigatórios")
    user = user_model.authenticate(email, password)
    if user:
        logger.info("Login bem-sucedido: %s", email)
        return jsonify({"dados": {key: user[key] for key in ("id", "nome", "email", "tipo")}, "sucesso": True, "mensagem": "Login OK"}), 200
    logger.info("Login falhou: %s", email)
    return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401


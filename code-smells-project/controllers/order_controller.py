import logging

from flask import jsonify, request

from controllers.errors import ApiError
from models import order_model

logger = logging.getLogger(__name__)


def criar_pedido():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError("Dados inválidos")
    user_id = data.get("usuario_id")
    items = data.get("itens", [])
    if isinstance(user_id, bool) or not isinstance(user_id, int) or not user_id:
        raise ApiError("Usuario ID é obrigatório")
    if not isinstance(items, list) or not items:
        raise ApiError("Pedido deve ter pelo menos 1 item")
    for item in items:
        if (not isinstance(item, dict)
                or isinstance(item.get("produto_id"), bool)
                or not isinstance(item.get("produto_id"), int)
                or isinstance(item.get("quantidade"), bool)
                or not isinstance(item.get("quantidade"), int)
                or item["quantidade"] < 1):
            raise ApiError("Dados inválidos")
    result = order_model.create(user_id, items)
    if "erro" in result:
        return jsonify({"erro": result["erro"], "sucesso": False}), 400
    logger.info("Pedido %s criado para usuário %s", result["pedido_id"], user_id)
    return jsonify({"dados": result, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


def listar_pedidos_usuario(usuario_id):
    return jsonify({"dados": order_model.get_for_user(usuario_id), "sucesso": True}), 200


def listar_todos_pedidos():
    return jsonify({"dados": order_model.get_all(), "sucesso": True}), 200


def atualizar_status_pedido(pedido_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError("Status inválido")
    new_status = data.get("status", "")
    if new_status not in order_model.ORDER_STATUSES:
        raise ApiError("Status inválido")
    order_model.update_status(pedido_id, new_status)
    if new_status in ("aprovado", "cancelado"):
        logger.info("Pedido %s teve status atualizado para %s", pedido_id, new_status)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200


def relatorio_vendas():
    return jsonify({"dados": order_model.sales_report(), "sucesso": True}), 200


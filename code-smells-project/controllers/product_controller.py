import logging

from flask import jsonify, request

from controllers.errors import ApiError
from models import product_model

logger = logging.getLogger(__name__)
VALID_CATEGORIES = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")


def _validated_product(data):
    if not isinstance(data, dict):
        raise ApiError("Dados inválidos")
    for field, message in (("nome", "Nome é obrigatório"), ("preco", "Preço é obrigatório"), ("estoque", "Estoque é obrigatório")):
        if field not in data:
            raise ApiError(message)
    if "nome" in data:
        if not isinstance(data["nome"], str):
            raise ApiError("Nome inválido")
        if len(data["nome"]) < 2:
            raise ApiError("Nome muito curto")
        if len(data["nome"]) > 200:
            raise ApiError("Nome muito longo")
    for field, label in (("preco", "Preço"), ("estoque", "Estoque")):
        if field in data:
            value = data[field]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ApiError(f"{label} inválido")
            if value < 0:
                raise ApiError(f"{label} não pode ser negativo")
    if "categoria" in data and data["categoria"] not in VALID_CATEGORIES:
        raise ApiError(f"Categoria inválida. Válidas: {list(VALID_CATEGORIES)}")
    return {
        "nome": data.get("nome", ""), "descricao": data.get("descricao", ""),
        "preco": data.get("preco"), "estoque": data.get("estoque"),
        "categoria": data.get("categoria", "geral"),
    }


def listar_produtos():
    produtos = product_model.get_all()
    logger.info("Listando %s produtos", len(produtos))
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria")
    try:
        preco_min = float(request.args["preco_min"]) if request.args.get("preco_min") else None
        preco_max = float(request.args["preco_max"]) if request.args.get("preco_max") else None
    except ValueError as exc:
        raise ApiError("Preço inválido") from exc
    resultados = product_model.search(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


def buscar_produto(product_id):
    produto = product_model.get_by_id(product_id)
    if produto:
        return jsonify({"dados": produto, "sucesso": True}), 200
    return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404


def criar_produto():
    data = _validated_product(request.get_json(silent=True))
    product_id = product_model.create(**{
        "name": data["nome"], "description": data["descricao"], "price": data["preco"],
        "stock": data["estoque"], "category": data["categoria"],
    })
    logger.info("Produto criado com ID %s", product_id)
    return jsonify({"dados": {"id": product_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(product_id):
    if not product_model.get_by_id(product_id):
        return jsonify({"erro": "Produto não encontrado"}), 404
    data = _validated_product(request.get_json(silent=True))
    product_model.update(product_id, data["nome"], data["descricao"], data["preco"], data["estoque"], data["categoria"])
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(product_id):
    if not product_model.get_by_id(product_id):
        return jsonify({"erro": "Produto não encontrado"}), 404
    product_model.delete(product_id)
    logger.info("Produto %s deletado", product_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


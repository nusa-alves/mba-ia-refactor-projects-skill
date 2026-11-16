from database import get_db


ORDER_STATUSES = ("pendente", "aprovado", "enviado", "entregue", "cancelado")
DISCOUNT_BRACKETS = ((10000, 0.10), (5000, 0.05), (1000, 0.02))


def create(user_id, items):
    db = get_db()
    total = 0
    products = []
    product_ids = list(dict.fromkeys(item["produto_id"] for item in items))
    placeholders = ", ".join("?" for _ in product_ids)
    rows = db.execute(
        f"SELECT id, nome, preco, estoque FROM produtos WHERE id IN ({placeholders})",
        product_ids,
    ).fetchall()
    products_by_id = {row["id"]: row for row in rows}
    for item in items:
        product = products_by_id.get(item["produto_id"])
        if product is None:
            return {"erro": f"Produto {item['produto_id']} não encontrado"}
        if product["estoque"] < item["quantidade"]:
            return {"erro": f"Estoque insuficiente para {product['nome']}"}
        products.append((item, product))
        total += product["preco"] * item["quantidade"]

    try:
        db.execute("BEGIN")
        cursor = db.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
            (user_id, total),
        )
        order_id = cursor.lastrowid
        for item, product in products:
            db.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (order_id, item["produto_id"], item["quantidade"], product["preco"]),
            )
            changed = db.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                (item["quantidade"], item["produto_id"], item["quantidade"]),
            ).rowcount
            if not changed:
                raise ValueError("Estoque insuficiente")
        db.commit()
        return {"pedido_id": order_id, "total": total}
    except Exception:
        db.rollback()
        raise


def _serialize_orders(rows):
    orders = {}
    for row in rows:
        order = orders.setdefault(row["id"], {
            "id": row["id"], "usuario_id": row["usuario_id"], "status": row["status"],
            "total": row["total"], "criado_em": row["criado_em"], "itens": [],
        })
        if row["item_id"] is not None:
            order["itens"].append({
                "produto_id": row["produto_id"], "produto_nome": row["produto_nome"] or "Desconhecido",
                "quantidade": row["quantidade"], "preco_unitario": row["preco_unitario"],
            })
    return list(orders.values())


def get_for_user(user_id):
    rows = get_db().execute(
        """SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
                  i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
           FROM pedidos p LEFT JOIN itens_pedido i ON i.pedido_id = p.id
           LEFT JOIN produtos pr ON pr.id = i.produto_id WHERE p.usuario_id = ?""",
        (user_id,),
    ).fetchall()
    return _serialize_orders(rows)


def get_all():
    rows = get_db().execute(
        """SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
                  i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
           FROM pedidos p LEFT JOIN itens_pedido i ON i.pedido_id = p.id
           LEFT JOIN produtos pr ON pr.id = i.produto_id"""
    ).fetchall()
    return _serialize_orders(rows)


def update_status(order_id, status):
    db = get_db()
    db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, order_id))
    db.commit()


def sales_report():
    db = get_db()
    totals = db.execute(
        """SELECT COUNT(*) AS total_pedidos, COALESCE(SUM(total), 0) AS faturamento,
                  SUM(CASE WHEN status = 'pendente' THEN 1 ELSE 0 END) AS pendentes,
                  SUM(CASE WHEN status = 'aprovado' THEN 1 ELSE 0 END) AS aprovados,
                  SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END) AS cancelados
           FROM pedidos"""
    ).fetchone()
    revenue = totals["faturamento"] or 0
    discount = next((revenue * rate for threshold, rate in DISCOUNT_BRACKETS if revenue > threshold), 0)
    count = totals["total_pedidos"]
    return {
        "total_pedidos": count,
        "faturamento_bruto": round(revenue, 2),
        "desconto_aplicavel": round(discount, 2),
        "faturamento_liquido": round(revenue - discount, 2),
        "pedidos_pendentes": totals["pendentes"] or 0,
        "pedidos_aprovados": totals["aprovados"] or 0,
        "pedidos_cancelados": totals["cancelados"] or 0,
        "ticket_medio": round(revenue / count, 2) if count > 0 else 0,
    }


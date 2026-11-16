from database import get_db


def _serialize(row):
    return {
        "id": row["id"], "nome": row["nome"], "descricao": row["descricao"],
        "preco": row["preco"], "estoque": row["estoque"], "categoria": row["categoria"],
        "ativo": row["ativo"], "criado_em": row["criado_em"],
    }


def get_all():
    return [_serialize(row) for row in get_db().execute("SELECT * FROM produtos").fetchall()]


def get_by_id(product_id):
    row = get_db().execute("SELECT * FROM produtos WHERE id = ?", (product_id,)).fetchone()
    return _serialize(row) if row else None


def create(name, description, price, stock, category):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (name, description, price, stock, category),
    )
    db.commit()
    return cursor.lastrowid


def update(product_id, name, description, price, stock, category):
    db = get_db()
    db.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (name, description, price, stock, category, product_id),
    )
    db.commit()


def delete(product_id):
    db = get_db()
    db.execute("DELETE FROM produtos WHERE id = ?", (product_id,))
    db.commit()


def search(term, category=None, price_min=None, price_max=None):
    query = "SELECT * FROM produtos WHERE 1=1"
    params = []
    if term:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        params.extend((f"%{term}%", f"%{term}%"))
    if category:
        query += " AND categoria = ?"
        params.append(category)
    if price_min is not None:
        query += " AND preco >= ?"
        params.append(price_min)
    if price_max is not None:
        query += " AND preco <= ?"
        params.append(price_max)
    rows = get_db().execute(query, params).fetchall()
    return [_serialize(row) for row in rows]


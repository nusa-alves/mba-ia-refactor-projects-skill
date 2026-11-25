from database import get_db


def reset_database():
    db = get_db()
    db.execute("DELETE FROM itens_pedido")
    db.execute("DELETE FROM pedidos")
    db.execute("DELETE FROM produtos")
    db.execute("DELETE FROM usuarios")
    db.commit()


def health_counts():
    db = get_db()
    return {
        "produtos": db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0],
        "usuarios": db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0],
        "pedidos": db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0],
    }


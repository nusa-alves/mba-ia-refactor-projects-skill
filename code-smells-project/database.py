import sqlite3

from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DB_PATH"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    from werkzeug.security import generate_password_hash

    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            descricao TEXT,
            preco REAL,
            estoque INTEGER,
            categoria TEXT,
            ativo INTEGER DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            email TEXT,
            senha TEXT,
            tipo TEXT DEFAULT 'cliente',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
            status TEXT DEFAULT 'pendente',
            total REAL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER REFERENCES pedidos(id) ON DELETE CASCADE,
            produto_id INTEGER REFERENCES produtos(id) ON DELETE SET NULL,
            quantidade INTEGER,
            preco_unitario REAL
        );
        """
    )
    if db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] == 0:
        products = [
            ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
            ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
            ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
            ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
            ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
            ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
            ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
            ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
            ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
            ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
        ]
        db.executemany(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            products,
        )
        users = [
            ("Admin", "admin@loja.com", generate_password_hash(current_app.config["SEED_ADMIN_PASSWORD"]), "admin"),
            ("João Silva", "joao@email.com", generate_password_hash(current_app.config["SEED_CUSTOMER_PASSWORD"]), "cliente"),
            ("Maria Santos", "maria@email.com", generate_password_hash(current_app.config["SEED_SECOND_CUSTOMER_PASSWORD"]), "cliente"),
        ]
        db.executemany(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)", users
        )
    db.commit()
    _ensure_order_foreign_keys(db)


def _ensure_order_foreign_keys(db):
    orders_have_fk = bool(db.execute("PRAGMA foreign_key_list(pedidos)").fetchall())
    items_have_fk = len(db.execute("PRAGMA foreign_key_list(itens_pedido)").fetchall()) >= 2
    if orders_have_fk and items_have_fk:
        return

    db.execute("PRAGMA foreign_keys = OFF")
    db.commit()
    try:
        db.execute("BEGIN")
        db.execute(
            """CREATE TABLE pedidos_novo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
                status TEXT DEFAULT 'pendente', total REAL,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        db.execute(
            """INSERT INTO pedidos_novo (id, usuario_id, status, total, criado_em)
               SELECT p.id, CASE WHEN u.id IS NULL THEN NULL ELSE p.usuario_id END,
                      p.status, p.total, p.criado_em
               FROM pedidos p LEFT JOIN usuarios u ON u.id = p.usuario_id"""
        )
        db.execute(
            """CREATE TABLE itens_pedido_novo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pedido_id INTEGER REFERENCES pedidos_novo(id) ON DELETE CASCADE,
                produto_id INTEGER REFERENCES produtos(id) ON DELETE SET NULL,
                quantidade INTEGER, preco_unitario REAL
            )"""
        )
        db.execute(
            """INSERT INTO itens_pedido_novo (id, pedido_id, produto_id, quantidade, preco_unitario)
               SELECT i.id, i.pedido_id,
                      CASE WHEN pr.id IS NULL THEN NULL ELSE i.produto_id END,
                      i.quantidade, i.preco_unitario
               FROM itens_pedido i
               JOIN pedidos_novo p ON p.id = i.pedido_id
               LEFT JOIN produtos pr ON pr.id = i.produto_id"""
        )
        db.execute("DROP TABLE itens_pedido")
        db.execute("DROP TABLE pedidos")
        db.execute("ALTER TABLE pedidos_novo RENAME TO pedidos")
        db.execute("ALTER TABLE itens_pedido_novo RENAME TO itens_pedido")
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.execute("PRAGMA foreign_keys = ON")


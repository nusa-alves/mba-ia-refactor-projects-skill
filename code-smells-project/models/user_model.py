from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db


def _serialize(row):
    return {
        "id": row["id"], "nome": row["nome"], "email": row["email"],
        "tipo": row["tipo"], "criado_em": row["criado_em"],
    }


def get_all():
    return [_serialize(row) for row in get_db().execute("SELECT * FROM usuarios").fetchall()]


def get_by_id(user_id):
    row = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (user_id,)).fetchone()
    return _serialize(row) if row else None


def create(name, email, password):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
        (name, email, generate_password_hash(password)),
    )
    db.commit()
    return cursor.lastrowid


def authenticate(email, password):
    db = get_db()
    row = db.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    if not row:
        return None
    stored_password = row["senha"] or ""
    try:
        valid = check_password_hash(stored_password, password)
    except (ValueError, TypeError):
        valid = False
    if not valid and stored_password == password:
        db.execute(
            "UPDATE usuarios SET senha = ? WHERE id = ?",
            (generate_password_hash(password), row["id"]),
        )
        db.commit()
        valid = True
    return _serialize(row) if valid else None


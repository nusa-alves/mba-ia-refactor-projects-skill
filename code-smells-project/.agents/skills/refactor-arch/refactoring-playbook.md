# Playbook de refatoração (Fase 3)

Cada transformação (`T-xx`) corrige um ou mais anti-patterns do catálogo. Os exemplos usam Python/Flask e Node/Express, mas o padrão vale para qualquer stack: adapte a sintaxe, mantenha a ideia.

## Ordem de execução

1. T-01 config e segredos (a estrutura de pastas nasce aqui)
2. T-03 estrutura MVC (mover código sem mudar o comportamento)
3. T-02 queries parametrizadas
4. T-04 e T-05 controllers finos e rotas separadas
5. T-12 injeção de dependência e fim do estado global
6. T-06, T-07, T-11 segurança (senha, campos sensíveis, rotas admin)
7. T-08 erros centralizados e T-18 validação
8. T-09, T-10, T-17, T-16 performance, transação, integridade, async
9. T-13, T-14, T-15 limpeza, deprecated, constantes e logging

Rode a validação ao fim de cada grupo grande, não só no final.

---

## T-01 Extrair configuração e segredos
**Corrige:** AP-01, AP-19

Antes (Python):
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
CORS(app)
```

Depois:
```python
# config/settings.py
import os

class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
    DB_PATH = os.environ.get("DB_PATH", "loja.db")
    PORT = int(os.environ.get("PORT", "5000"))
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")

# app.py
from config.settings import Settings
app.config["SECRET_KEY"] = Settings.SECRET_KEY
CORS(app, origins=Settings.CORS_ORIGINS)
app.run(host="127.0.0.1", port=Settings.PORT, debug=Settings.DEBUG)
```

Antes (Node):
```js
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_123", port: 3000 };
```

Depois:
```js
// src/config/settings.js
module.exports = {
  port: Number(process.env.PORT || 3000),
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
  adminToken: process.env.ADMIN_TOKEN || '',
};
```

Passos: leve cada literal sensível para variável de ambiente, documente em um `.env.example` (sem valores reais) e verifique que `.env` está no `.gitignore`. Se o valor real estava no código, avise o usuário no resumo final que ele deve **rotacionar** essa credencial, pois ela ficou no histórico do git.

---

## T-02 Parametrizar queries
**Corrige:** AP-02

Antes (Python):
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
query += " AND (nome LIKE '%" + termo + "%')"
```

Depois:
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))   # senha: veja T-06
params = []
if termo:
    query += " AND (nome LIKE ? OR descricao LIKE ?)"
    params += [f"%{termo}%", f"%{termo}%"]
cursor.execute(query, params)
```

Antes (Node):
```js
db.all(`SELECT * FROM courses WHERE id = ${id}`, cb);
```

Depois:
```js
db.all('SELECT * FROM courses WHERE id = ?', [id], cb);
```

Se a mesma rota ou função **executa SQL recebido do cliente** (`cursor.execute(request.json["sql"])`), parametrizar não basta: remova a execução, conforme T-11. Não deixe uma versão "restrita" ou "atrás de token".

Regras: valores sempre via placeholder; **nomes** de coluna ou tabela dinâmicos só a partir de uma allowlist fixa; `LIKE` recebe o padrão `%termo%` como parâmetro, nunca na string da query.

---

## T-03 Quebrar o God file/class em camadas MVC
**Corrige:** AP-03, AP-08

Antes: um arquivo (`models.py`, `AppManager.js`) com SQL, regra, rotas e formatação de vários domínios.

Depois (Node):
```
src/
├── app.js                      # compõe e inicia
├── config/settings.js
├── database/connection.js      # cria o banco e o schema
├── models/{userModel,courseModel,enrollmentModel,paymentModel}.js
├── controllers/{checkoutController,reportController,userController}.js
├── routes/index.js
└── middlewares/{errorHandler,auth}.js
```

Procedimento:

1. Liste as responsabilidades do arquivo: schema/seed, acesso a dados por entidade, regras, handlers, rotas.
2. Crie os destinos conforme `mvc-guidelines.md`.
3. Mova o código **sem alterá-lo** primeiro (mesmas funções, novos arquivos), ajuste imports e rode a validação.
4. Só então aplique as demais transformações sobre o código já separado.
5. Separe por domínio (produto, pedido, usuário), não por tipo técnico apenas.
6. Apague o arquivo antigo quando nada mais o referenciar.

---

## T-04 Controller fino: mover regra de negócio para o Model
**Corrige:** AP-07

Antes (controller com a regra):
```python
def relatorio_vendas():
    faturamento = ...
    if faturamento > 10000:
        desconto = faturamento * 0.1
    elif faturamento > 5000:
        desconto = faturamento * 0.05
    ...
    return jsonify({...})
```

Depois:
```python
# models/pedido_model.py
FAIXAS_DESCONTO = [(10000, 0.10), (5000, 0.05), (1000, 0.02)]

def calcular_desconto(faturamento):
    for limite, percentual in FAIXAS_DESCONTO:
        if faturamento > limite:
            return faturamento * percentual
    return 0

# controllers/relatorio_controller.py
def relatorio_vendas():
    dados = pedido_model.resumo_vendas()          # model devolve os números
    return jsonify({"dados": dados, "sucesso": True}), 200
```

Regra: o controller lê a entrada, chama o model, escolhe o status e monta a resposta. Regras que dependem só dos dados (totais, estoque, desconto) ficam no model, em funções puras e testáveis. Orquestração com efeitos (enviar e-mail) ficam em um serviço chamado pelo controller.

---

## T-05 Separar rotas dos controllers
**Corrige:** AP-08

Antes (Flask, handlers com SQL no arquivo principal):
```python
@app.route("/admin/reset-db", methods=["POST"])
def reset_database():
    db = get_db(); cursor = db.cursor(); cursor.execute("DELETE FROM pedidos") ...
```

Depois:
```python
# routes/routes.py
from flask import Blueprint
from controllers import produto_controller, admin_controller

bp = Blueprint("api", __name__)
bp.add_url_rule("/produtos", "listar_produtos", produto_controller.listar, methods=["GET"])
bp.add_url_rule("/admin/reset-db", "reset_db", admin_controller.reset_db, methods=["POST"])

# app.py
app.register_blueprint(bp)
```

Antes (Express):
```js
app.post('/api/checkout', (req, res) => { /* 50 linhas */ });
```

Depois:
```js
// src/routes/index.js
const router = require('express').Router();
router.post('/api/checkout', checkoutController.checkout);
module.exports = router;
```

Mantenha **os mesmos caminhos e métodos** de antes. Se o projeto já usa blueprints/routers por domínio, preserve-os.

---

## T-06 Armazenamento seguro de senha
**Corrige:** AP-04

Antes:
```python
cursor.execute("INSERT INTO usuarios (...) VALUES ('" + nome + "', '" + email + "', '" + senha + "')")
self.password = hashlib.md5(pwd.encode()).hexdigest()
```
```js
function badCrypto(pwd) { /* base64 repetido */ }
```

Depois (Python):
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, pwd):
    self.password = generate_password_hash(pwd)

def check_password(self, pwd):
    return check_password_hash(self.password, pwd)
```

Depois (Node, usando `crypto.scrypt` da biblioteca padrão, sem dependência nova):
```js
const crypto = require('crypto');
function hashPassword(pwd) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.scryptSync(pwd, salt, 64).toString('hex');
  return `${salt}:${hash}`;
}
function verifyPassword(pwd, stored) {
  const [salt, hash] = stored.split(':');
  const test = crypto.scryptSync(pwd, salt, 64);
  return crypto.timingSafeEqual(Buffer.from(hash, 'hex'), test);
}
```

Passos:

1. Nunca compare senha dentro do SQL. Busque o usuário por e-mail e verifique o hash no código.
2. **Dados já gravados:** se o banco tem senhas em texto puro ou MD5, o login passa a falhar. Trate assim: ao autenticar, se o valor armazenado não tiver o formato do novo hash, compare com o formato antigo e, se bater, regrave com o hash novo (migração no login).
3. Atualize os seeds e fixtures para gravar o hash novo.
4. Para **token falso** (`'fake-jwt-token-' + id`), emita um token assinado (JWT com `SECRET_KEY` ou sessão) ou, se a biblioteca não estiver disponível, um token aleatório guardado no servidor. Registre a mudança como contrato deliberado.
5. Nunca aceite `role` do cliente em cadastro público: ignore o campo ou restrinja a papéis não privilegiados.

---

## T-07 Parar de expor campos sensíveis
**Corrige:** AP-06

Antes:
```python
def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password, "role": self.role}
```
```python
return jsonify({"status": "ok", "secret_key": app.config["SECRET_KEY"], "debug": True, "db_path": "loja.db"})
```

Depois:
```python
SENSITIVE = {"password", "senha", "pass", "secret_key"}

def to_dict(self):
    return {"id": self.id, "email": self.email, "role": self.role}   # allowlist explícita

return jsonify({"status": "ok", "database": "connected", "counts": counts, "versao": VERSION})
```

Para logs: nunca registre senha, cartão (mesmo parcial além dos 4 últimos dígitos) ou chaves. Antes: `console.log(\`Processando cartão ${cc} na chave ${key}\`)`. Depois: `logger.info('Processando pagamento', { last4: cc.slice(-4) })`.

Isso muda o JSON devolvido: liste cada campo removido em "Contract changes".

---

## T-08 Tratamento de erros centralizado
**Corrige:** AP-15, AP-06

Antes:
```python
def listar_produtos():
    try:
        ...
    except Exception as e:
        print("ERRO: " + str(e))
        return jsonify({"erro": str(e)}), 500
```

Depois (Flask):
```python
# middlewares/error_handler.py
import logging
logger = logging.getLogger(__name__)

class AppError(Exception):
    def __init__(self, message, status=400):
        self.message, self.status = message, status

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(e):
        return jsonify({"erro": e.message, "sucesso": False}), e.status

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
```

Depois (Express):
```js
// src/middlewares/errorHandler.js
module.exports = (err, req, res, next) => {
  const status = err.status || 500;
  if (status >= 500) console.error(err);
  res.status(status).json({ erro: status >= 500 ? 'Erro interno do servidor' : err.message });
};
// app.js: app.use(errorHandler) depois das rotas
```

Os controllers lançam `AppError` (ou chamam `next(err)`) e **não** fazem `try/except` genérico. Troque `except:` por exceções específicas. Preserve o status e a chave de erro que os clientes já recebem (`erro`/`error`).

---

## T-09 Eliminar N+1
**Corrige:** AP-12

Antes:
```python
for row in pedidos:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in itens:
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```

Depois (JOIN único, agrupando em memória):
```python
cursor.execute("""
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
""")
pedidos = {}
for r in cursor.fetchall():
    p = pedidos.setdefault(r["id"], {"id": r["id"], "usuario_id": r["usuario_id"],
                                     "status": r["status"], "total": r["total"],
                                     "criado_em": r["criado_em"], "itens": []})
    if r["produto_id"] is not None:
        p["itens"].append({"produto_id": r["produto_id"],
                           "produto_nome": r["produto_nome"] or "Desconhecido",
                           "quantidade": r["quantidade"], "preco_unitario": r["preco_unitario"]})
return list(pedidos.values())
```

ORM (SQLAlchemy): use `joinedload`/`selectinload` e `query.options(...)`; para contagens, `GROUP BY` em vez de `count()` por linha. Garanta que o formato e a ordem do JSON final continuem iguais.

---

## T-10 Transação para escritas em vários passos
**Corrige:** AP-11

Antes:
```python
for item in itens: # verifica estoque
    ...
cursor.execute("INSERT INTO pedidos ...")
for item in itens:
    cursor.execute("INSERT INTO itens_pedido ...")
    cursor.execute("UPDATE produtos SET estoque = estoque - ...")
db.commit()
```

Depois:
```python
try:
    db.execute("BEGIN")
    # baixa atômica: só decrementa se houver estoque
    cur = db.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                     (qtd, produto_id, qtd))
    if cur.rowcount == 0:
        raise AppError("Estoque insuficiente", 400)
    ...  # INSERT pedido e itens
    db.commit()
except Exception:
    db.rollback()
    raise
```

Node (`sqlite3`): envolva em `db.serialize` com `BEGIN`/`COMMIT`/`ROLLBACK`, ou promisifique e use `try/catch`. ORM: `with db.session.begin():` e rollback no erro. Os passos dependentes (matrícula, pagamento, auditoria) entram na mesma transação, e o erro de qualquer um aborta tudo.

---

## T-11 Proteger rotas administrativas e destrutivas
**Corrige:** AP-05, AP-04

**Princípio:** a Recommendation do relatório é aplicada **por inteiro, cláusula por cláusula**. Se ela diz "proteger" *e* "retirar a execução arbitrária", são duas mudanças, e proteger não cumpre a segunda.

Antes:
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    cursor.execute(request.get_json().get("sql"))
```

Depois (SQL do cliente: a rota, o handler e a função do Model são **apagados**; o resto das rotas admin ganha o middleware):
```python
# middlewares/auth.py
from functools import wraps
from flask import request, jsonify
from config.settings import Settings

def require_admin(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        token = request.headers.get("X-Admin-Token", "")
        if not Settings.ADMIN_TOKEN or token != Settings.ADMIN_TOKEN:
            return jsonify({"erro": "Acesso negado", "sucesso": False}), 403
        return fn(*a, **kw)
    return wrapper
```
```js
// src/middlewares/auth.js
module.exports.requireAdmin = (req, res, next) => {
  const token = req.get('X-Admin-Token');
  if (!settings.adminToken || token !== settings.adminToken) return res.status(403).json({ erro: 'Acesso negado' });
  next();
};
```

Regras:

- As rotas administrativas **legítimas** (reset, health, relatórios) continuam existindo e passam a responder `403` sem o token. Sem `ADMIN_TOKEN` configurado, a rota fica fechada.
- **Execução de SQL (ou comando, ou código) vindo do cliente é removida por inteiro, nunca protegida.** Apague a rota, o handler do Controller e a função do Model que recebia a string; remova imports que ficaram sem uso e a menção na documentação. Token de admin e restrição a `SELECT` **não substituem** a remoção: `SELECT` ainda lê `usuarios.senha`, tabelas internas e permite consultas pesadas. A rota removida passa a responder `404`, e isso entra em "Contract changes (deliberate)". Se o usuário precisar de uma consulta administrativa, crie um endpoint dedicado com SQL **fixo** e parâmetros nomeados (por exemplo, `/admin/relatorio-vendas`), nunca um campo livre de SQL.
- Verificação obrigatória depois da remoção: busque no projeto (`grep -rnE "execute\(|executemany\(|\.query\(|\.all\(|\.run\("`) e confirme que nenhuma chamada recebe string originada em `request`/`req`. Cole o resultado no resumo.
- Aplique o middleware também em `DELETE` de usuário, relatório financeiro e demais rotas sensíveis que o relatório apontou.
- Registre como contrato deliberado: "rotas X agora exigem `X-Admin-Token`".

---

## T-12 Injeção de dependência e fim do estado global
**Corrige:** AP-09, AP-10

Antes:
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("loja.db", check_same_thread=False)
    return db_connection
```
```js
class AppManager { constructor() { this.db = new sqlite3.Database(':memory:'); } }
let globalCache = {}; let totalRevenue = 0;
```

Depois (Flask, conexão por requisição):
```python
# database.py
import sqlite3
from flask import g, current_app

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DB_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
```

Depois (Node, fábrica com dependências injetadas):
```js
// src/app.js
function createApp({ db, settings }) {
  const app = express();
  app.use(express.json());
  app.use('/', buildRoutes({ db, settings }));
  app.use(errorHandler);
  return app;
}
const db = createConnection(settings.dbPath);
createApp({ db, settings }).listen(settings.port);
```

Regras: nada de `global`, nem `let` exportado e reatribuído. Estado compartilhado vai para o banco, para uma classe injetada ou, no caso de cache, para um módulo com interface explícita. Se um contador ou cache **nunca é lido**, remova.

Atenção: se o banco é `:memory:` e populado no startup, mantenha esse comportamento (a conexão única continua, mas criada no composition root e injetada).

---

## T-13 Deduplicar código
**Corrige:** AP-13, AP-23

Antes (a mesma regra em 6 rotas, e o método do model sem uso):
```python
if t.due_date:
    if t.due_date < datetime.utcnow():
        if t.status != 'done' and t.status != 'cancelled':
            task_data['overdue'] = True
        ...
```

Depois:
```python
# models/task.py
def is_overdue(self):
    if not self.due_date or self.status in ("done", "cancelled"):
        return False
    return self.due_date < datetime.now(timezone.utc).replace(tzinfo=None)

def to_dict(self, include_overdue=False): ...

# controllers: use task.is_overdue() e task.to_dict() em todos os pontos
```

Antes (serialização copiada):
```python
result.append({"id": row["id"], "nome": row["nome"], "descricao": row["descricao"], ...})
```
Depois: uma função `row_to_produto(row)` no model, usada por todas as consultas.

Passos: encontre os blocos repetidos, escolha o ponto único (model ou módulo de utilitários), troque cada ocorrência, remova o código morto (imports sem uso, helpers sem chamada, dependências que nenhum arquivo importa) e confirme que nada mais os referencia antes de apagar. Valores repetidos como listas de status vão para constantes (T-15).

---

## T-14 Substituir APIs deprecated
**Corrige:** AP-16

Consulte a tabela do catálogo (AP-16) e aplique o equivalente. Exemplos:

```python
# Antes
Task.query.get(task_id)
datetime.utcnow()
# Depois
db.session.get(Task, task_id)
datetime.now(timezone.utc)
```
```js
// Antes
const b = new Buffer(str); app.use(bodyParser.json()); res.send(404, 'x');
// Depois
const b = Buffer.from(str); app.use(express.json()); res.status(404).send('x');
```

Cuidados:

- `datetime.now(timezone.utc)` devolve datetime **com fuso**. Se o banco ou o código compara com valores sem fuso (`due_date` gravada via `strptime`), isso gera `TypeError`. Use `datetime.now(timezone.utc).replace(tzinfo=None)` para manter o comportamento, ou converta tudo de forma consistente.
- `db.session.get(Model, id)` devolve `None` quando não acha, como `query.get`. Para `get_or_404`, use `db.get_or_404(Model, id)`.
- Atualize o manifesto de dependências só se a mudança for necessária. Não faça upgrade de versão maior sem pedido.

---

## T-15 Constantes, logging e nomes
**Corrige:** AP-20, AP-21, AP-22

Antes:
```python
if faturamento > 10000: desconto = faturamento * 0.1
categorias_validas = ["informatica", "moveis", ...]
print("Produto criado com ID: " + str(id))
```
```js
let u = req.body.usr, e = req.body.eml, cid = req.body.c_id, cc = req.body.card;
```

Depois:
```python
# constants.py (ou no model do domínio)
CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
STATUS_PEDIDO = ("pendente", "aprovado", "enviado", "entregue", "cancelado")

import logging
logger = logging.getLogger(__name__)
logger.info("Produto criado com ID %s", id)
```
```js
const { usr: userName, eml: email, pwd: password, c_id: courseId, card } = req.body;
```

Regras: renomeie **variáveis internas**, nunca os campos do contrato HTTP (`usr`, `c_id` continuam sendo as chaves aceitas no corpo). Nomes que sobrescrevem builtins (`id`) viram `produto_id`, `item_id`. Configure o logging uma vez, no entry point.

---

## T-16 Callbacks aninhados para async/await
**Corrige:** AP-18

Antes (relatório com 4 níveis de callbacks e contadores `pending--`):
```js
this.db.all("SELECT * FROM courses", [], (err, courses) => {
  courses.forEach(c => {
    this.db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], (err, enrollments) => { ... });
  });
});
```

Depois:
```js
// src/database/connection.js: helpers promisificados
const all = (db, sql, params = []) => new Promise((res, rej) => db.all(sql, params, (e, r) => e ? rej(e) : res(r)));
const get = (db, sql, params = []) => new Promise((res, rej) => db.get(sql, params, (e, r) => e ? rej(e) : res(r)));
const run = (db, sql, params = []) => new Promise((res, rej) =>
  db.run(sql, params, function (e) { e ? rej(e) : res({ lastID: this.lastID, changes: this.changes }); }));

// models/reportModel.js: uma query com JOIN (veja T-09) em vez de loops
const rows = await all(db, `
  SELECT c.id, c.title, u.name, p.amount, p.status
  FROM courses c
  LEFT JOIN enrollments e ON e.course_id = c.id
  LEFT JOIN users u ON u.id = e.user_id
  LEFT JOIN payments p ON p.enrollment_id = e.id
  ORDER BY c.id`);

// controller
exports.financialReport = async (req, res, next) => {
  try { res.json(await reportModel.financialReport()); } catch (err) { next(err); }
};
```

Preserve o formato do JSON final e a ordem dos itens (ordene por `id` para ficar determinístico). Em Express 4, erros de handlers `async` precisam de `try/catch` + `next(err)` (ou um wrapper).

---

## T-17 Integridade referencial
**Corrige:** AP-17

Antes:
```js
this.db.run("DELETE FROM users WHERE id = ?", [id], (err) => {
  res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.");
});
```

Depois:
```js
// model: remove os dependentes na mesma transação
await run(db, 'BEGIN');
try {
  await run(db, 'DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)', [id]);
  await run(db, 'DELETE FROM enrollments WHERE user_id = ?', [id]);
  const r = await run(db, 'DELETE FROM users WHERE id = ?', [id]);
  await run(db, 'COMMIT');
  return r.changes > 0;
} catch (e) { await run(db, 'ROLLBACK'); throw e; }
```

Passos: devolva `404` quando o registro não existe, trate o erro do banco, e prefira `FOREIGN KEY ... ON DELETE CASCADE` no schema (em SQLite, `PRAGMA foreign_keys = ON`) ou `cascade="all, delete-orphan"` no ORM. Mantenha o texto/formato de sucesso original quando possível.

---

## T-18 Camada de validação de entrada
**Corrige:** AP-14

Antes:
```python
dados = request.get_json()
if preco < 0: ...        # TypeError se preco for string
pedido_id = int(request.args["x"])
```

Depois:
```python
def validar_produto(dados, parcial=False):
    if not isinstance(dados, dict):
        raise AppError("Dados inválidos", 400)
    obrigatorios = [] if parcial else ["nome", "preco", "estoque"]
    for campo in obrigatorios:
        if campo not in dados:
            raise AppError(f"{campo.capitalize()} é obrigatório", 400)
    if "preco" in dados and (not isinstance(dados["preco"], (int, float)) or dados["preco"] < 0):
        raise AppError("Preço inválido", 400)
    ...
    return dados
```

Regras: `request.get_json(silent=True)` com checagem de nulo; verifique **tipos** antes de comparar; converta com `try/except ValueError` e responda `400`; mesma validação para create e update; não mude as mensagens e os status que já eram usados nos casos que já funcionavam.

---

# Protocolo de validação (usado na Fase 3)

Objetivo: provar que a aplicação sobe e que **todos os endpoints originais respondem como antes**.

## 1. Montar o arquivo de endpoints

Com as rotas descobertas na Fase 1 (código, `api.http`, README), crie um JSON com uma entrada por endpoint e guarde **fora do projeto** (por exemplo, no diretório temporário do sistema). Não commite esse arquivo.

```json
[
  {"name": "health", "method": "GET", "path": "/health"},
  {"name": "listar produtos", "method": "GET", "path": "/produtos"},
  {"name": "criar produto", "method": "POST", "path": "/produtos",
   "body": {"nome": "Teste", "preco": 10.5, "estoque": 3},
   "capture": {"novo_id": "dados.id"}, "expect_status": 201},
  {"name": "buscar criado", "method": "GET", "path": "/produtos/{novo_id}"},
  {"name": "remover criado", "method": "DELETE", "path": "/produtos/{novo_id}"}
]
```

Regras:

- Cubra **todas** as rotas, incluindo as de erro típicas (`404` para id inexistente, `400` para corpo inválido).
- `capture` guarda valores de respostas anteriores (caminho com pontos); use `{nome}` em `path` ou `body` para reutilizá-los.
- Ordene para que as leituras venham antes das escritas e para que o que for criado seja removido no fim.
- Rotas que exigem token passam `"headers": {"X-Admin-Token": "..."}`. Para o baseline (código antigo) a rota abre sem token, e depois da refatoração ela deve responder `403` sem o token. Registre essa diferença como contrato deliberado.
- Rotas destrutivas (`reset-db`, apagar usuário): deixe-as por último, ou use um banco descartável.

## 2. Baseline (antes de qualquer alteração)

```
python .agents/skills/refactor-arch/scripts/smoke_test.py --cmd "<comando de execução>" --base-url http://localhost:<porta> \
    --endpoints <endpoints.json> --out <baseline.json> [--reset-file <arquivo.db>]
```

- Se o banco é um arquivo SQLite **gerado pela aplicação** (e não versionado), passe `--reset-file` para apagá-lo antes de cada execução, assim baseline e comparação partem do mesmo estado. Confira com `git status` que ele não está versionado.
- Em Windows, use `python`; em Linux/macOS, pode ser `python3`.
- Se faltar dependência, crie um ambiente virtual (`python -m venv .venv`) e instale (`pip install -r requirements.txt`, `npm install`) antes. Não versione `.venv` nem `node_modules`.

## 3. Depois da refatoração

```
python .agents/skills/refactor-arch/scripts/smoke_test.py --cmd "<comando de execução>" --base-url http://localhost:<porta> \
    --endpoints <endpoints.json> --compare <baseline.json> [--reset-file <arquivo.db>]
```

O script sobe a aplicação, espera a porta abrir, chama cada endpoint, compara status e **formato** do JSON (chaves e tipos, não os valores) com o baseline e encerra a aplicação. Saída:

- `PASS`: status e formato iguais.
- `DIFF`: o formato mudou (campo removido ou adicionado). Se for correção deliberada de segurança, registre em "Contract changes". Se não for, corrija.
- `FAIL`: status diferente, erro de conexão ou a aplicação não subiu. Corrija e rode de novo.

## 4. Critérios para o resumo final

- ✓ Application boots: o script conseguiu conectar na porta.
- ✓ Endpoints: `N/M` com `PASS` ou `DIFF` deliberado; nenhum `FAIL` não explicado.
- ✓ Anti-patterns remaining: releia o código contra o catálogo e liste o que restou.

Se não for possível executar a aplicação neste ambiente (permissão, rede, dependência faltando), **diga isso**, mostre o que foi verificado de outro modo (por exemplo, import sem erro, `python -m py_compile`, `node --check`) e peça ao usuário que rode o comando de validação. Não declare sucesso sem execução.

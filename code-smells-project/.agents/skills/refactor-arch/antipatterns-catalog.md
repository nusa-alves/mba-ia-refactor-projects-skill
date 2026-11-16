# Catálogo de anti-patterns (Fase 2)

Cada entrada tem: **severidade**, **sinais de detecção** (o que procurar no código), **por que importa** e a **transformação** correspondente em `refactoring-playbook.md` (IDs `T-xx`).

Como usar:

1. Para cada entrada, aplique os sinais e as buscas sugeridas (por exemplo, com `grep -n`).
2. **Abra o arquivo e confirme o trecho.** Uma busca por texto só indica candidatos, e muitos são falsos positivos.
3. Registre o arquivo e as linhas exatas. Agrupe ocorrências da mesma natureza em um único finding, com a lista de locais.
4. Dê o título da entrada do catálogo (ou algo mais específico, se ajudar) e use a severidade indicada. Só mude a severidade com justificativa.

Verificação antes de registrar (vale para toda entrada):

- Leia as linhas exatas que vai citar. Linha em branco, comentário ou trecho de outro assunto invalida o finding.
- **Não rebaixe a severidade do catálogo.** Por exemplo, God Class/File é CRITICAL mesmo quando o projeto "tem alguns arquivos separados". Se achar que a severidade não se aplica, explique na `Description`.
- Itens de "sem uso" (imports, variáveis, funções): busque o nome no arquivo inteiro e, para funções, no projeto inteiro, antes de afirmar.
- Consulta fixa, sem valor externo (`SELECT * FROM pedidos`), não é SQL Injection.

Escala de severidade:

- **CRITICAL**: falha grave de arquitetura ou segurança, dado sensível exposto, ou violação total da separação de responsabilidades.
- **HIGH**: forte violação de MVC ou SOLID que dificulta manutenção e testes.
- **MEDIUM**: padronização, duplicação, performance moderada, validação ausente.
- **LOW**: legibilidade, nomenclatura, magic numbers.

---

## CRITICAL

### AP-01 Credenciais e segredos hardcoded
- **Sinais:** literais atribuídos a nomes como `SECRET_KEY`, `password`, `pass`, `senha`, `token`, `api_key`, `apiKey`, `secret`, `DB_PASS`; chaves com prefixos como `pk_live_`, `sk_`, `AKIA`; usuário e senha SMTP no código; `DEBUG = True` ou `debug=True` fixo; `host="0.0.0.0"` com debug ligado.
- **Busca:** `grep -nEi "(secret|passw|senha|token|api_?key|smtp)[a-z_]*\s*[:=]\s*['\"]"`
- **Por que importa:** quem lê o repositório obtém acesso a gateways, e-mail e sessões. O modo debug expõe console interativo.
- **Transformação:** T-01.

### AP-02 SQL Injection
- **Sinais:** query montada por concatenação (`"..." + var`), f-string, `.format()`, `%` em string, ou template literal com `${}` dentro de SQL passado a `execute`, `query`, `run`, `get`, `all`; `LIKE '%" + termo + "%'`; `cursor.execute(request.json["sql"])`.
- **Busca:** `grep -nE "(execute|query|run|get|all)\(.*(\+|f\"|f'|\\$\{|%s.*%|\.format)"`
- **Falso positivo:** consultas com placeholders (`?`, `%s` passado como parâmetro separado, `$1`, `:nome`), ORM com filtros parametrizados, ou consultas totalmente fixas, sem nenhum valor vindo de fora (por exemplo, `SELECT * FROM pedidos`).
- **Por que importa:** leitura, alteração ou destruição do banco e bypass de autenticação.
- **Transformação:** T-02.

### AP-03 God Class / God File / God Method
- **Sinais:** um único arquivo ou classe que reúne acesso a dados, regra de negócio, roteamento, validação e formatação; classe `*Manager` ou `*Service` que cria o banco, define rotas e processa pagamento; arquivo com várias centenas de linhas misturando domínios (produtos, pedidos, usuários) sem separação; método com 50+ linhas e callbacks aninhados. **Atenção:** existir um arquivo `models` e outro `controllers` não afasta o problema. Um único `models.py` (ou `controllers.py`) com mais de ~250 linhas e 3 ou mais domínios (por exemplo, produtos, usuários, pedidos e relatórios) é God File. Registre sempre que isso ocorrer, com a severidade CRITICAL, e cite o intervalo do arquivo.
- **Por que importa:** impossível testar em isolamento; qualquer mudança afeta tudo.
- **Transformação:** T-03 (com T-04, T-05).

### AP-04 Armazenamento de senha inseguro e autenticação falsa
- **Sinais:** senha gravada e comparada em texto puro (`WHERE senha = '`); MD5/SHA1 sem salt (`hashlib.md5`, `createHash('md5')`); "hash" caseiro (base64, rot, loops que concatenam); senha padrão (`"123456"`); seed com senhas em texto puro; token fixo ou previsível (`'fake-jwt-token-' + id`); `role` aceito do corpo da requisição (`role = data.get('role')`).
- **Por que importa:** credenciais recuperáveis, contas forjáveis e escalada de privilégio.
- **Transformação:** T-06 (e T-11 para o controle de acesso).

### AP-05 Endpoints sensíveis ou destrutivos sem autenticação
- **Sinais:** rotas como `/admin/*`, `reset-db`, `query` que executam SQL, `DELETE` de usuários, relatórios financeiros, tudo sem verificação de token, sessão ou papel; nenhum middleware ou decorator de autenticação em todo o projeto.
- **Por que importa:** qualquer cliente apaga dados ou lê informação financeira.
- **Transformação:** T-11.

### AP-06 Exposição de dados sensíveis
- **Sinais:** respostas JSON com `password`, `senha`, `pass`, `hash`, `secret_key`, `db_path`, `debug`; `to_dict()` ou serializer que inclui todos os campos; log do número completo do cartão, da chave do gateway ou de senhas (`print(f"...{cc}...")`, `console.log(\`...${card}\`)`); `str(e)` ou stack trace devolvido ao cliente.
- **Por que importa:** vazamento de credenciais e de dados de pagamento (PCI).
- **Transformação:** T-07, T-08, T-15.

---

## HIGH

### AP-07 Lógica de negócio na camada errada (controller gordo ou model gordo)
- **Sinais:** no controller ou rota: regras de preço, estoque, desconto, status, cálculo de totais, orquestração de vários passos, notificações; no model: regras de fluxo e decisão de HTTP (códigos, mensagens); handlers com mais de ~40 linhas.
- **Por que importa:** não dá para testar a regra sem HTTP, e ela se duplica.
- **Transformação:** T-04.

### AP-08 Roteamento ou view acessando o banco
- **Sinais:** arquivo de rotas ou `app` que importa `get_db`, `db`, `cursor`, `session` e executa SQL ou consultas diretamente; handler de rota definido no arquivo principal junto com acesso a dados.
- **Por que importa:** viola a separação de responsabilidades do MVC.
- **Transformação:** T-05 (com T-04).

### AP-09 Acoplamento forte sem injeção de dependência
- **Sinais:** o construtor ou módulo cria a conexão (`new Database(...)`, `sqlite3.connect(...)`); controllers importam o módulo de banco concreto; classes instanciam seus colaboradores; configuração importada de módulo global dentro da lógica.
- **Por que importa:** não dá para trocar o banco nem testar com mock.
- **Transformação:** T-12.

### AP-10 Estado global mutável
- **Sinais:** variáveis de módulo reatribuídas (`global x`, `let cache = {}` exportado), conexão global (`db_connection = None` + `global`), contadores e caches compartilhados, listas em memória que acumulam estado de requisições.
- **Por que importa:** acoplamento oculto, condições de corrida e testes dependentes de ordem.
- **Transformação:** T-12.

### AP-11 Escritas em vários passos sem transação
- **Sinais:** sequência de `INSERT`/`UPDATE`/`DELETE` dependentes (pedido + itens + baixa de estoque; matrícula + pagamento + auditoria) com um único commit no fim sem rollback, ou com commits intermediários; verificação de estoque separada da baixa; erro de um passo ignorado.
- **Por que importa:** falha no meio deixa dados inconsistentes, e requisições concorrentes causam estoque negativo.
- **Transformação:** T-10.

---

## MEDIUM

### AP-12 Queries N+1
- **Sinais:** consulta dentro de loop (`for ... : cursor.execute(...)`, `forEach` com `db.get`), relacionamento ORM lazy acessado em loop (`len(u.tasks)`), `Model.query.get(x.fk_id)` dentro de `for`.
- **Por que importa:** o número de queries cresce com o volume de dados.
- **Transformação:** T-09.

### AP-13 Código duplicado
- **Sinais:** o mesmo bloco de serialização (dict campo a campo) em vários lugares; a mesma regra reescrita (por exemplo, "tarefa atrasada") em várias rotas mesmo existindo um método para ela; validações copiadas entre create e update com regras divergentes; listas literais de status ou papéis repetidas.
- **Por que importa:** a correção precisa ser feita em todos os pontos, e as cópias divergem.
- **Transformação:** T-13.

### AP-14 Validação de entrada ausente ou inconsistente
- **Sinais:** `request.get_json()` ou `req.body` usado sem checar nulo; comparação numérica sem checar tipo (`priority < 1` com string); `int(x)` ou `float(x)` sem tratamento; campos obrigatórios não verificados; update com validação mais fraca que o create; sem validação de formato de e-mail; sem limite de tamanho.
- **Por que importa:** entrada inválida causa erro 500 ou dado ruim.
- **Transformação:** T-18.

### AP-15 Tratamento de erro engolido, repetido ou vazando detalhes
- **Sinais:** `except:` ou `except Exception` sem tratamento específico; `try/except` copiado em toda função devolvendo `str(e)`; callbacks que ignoram `err`; mensagem de sucesso mesmo quando houve erro; ausência de handler de erro central.
- **Por que importa:** bugs ficam escondidos e detalhes internos vazam.
- **Transformação:** T-08.

### AP-16 APIs deprecated ou obsoletas
- **Sinais:** uso de funções, módulos ou padrões marcados como deprecated ou removidos na **versão declarada** no manifesto. Confira a versão antes de classificar. Consulte a tabela abaixo.
- **Por que importa:** gera warnings hoje e quebra com atualizações.
- **Transformação:** T-14.

| Stack | API obsoleta | Equivalente moderno |
|---|---|---|
| Python 3.12+ | `datetime.utcnow()`, `datetime.utcfromtimestamp()` | `datetime.now(timezone.utc)`, `datetime.fromtimestamp(ts, timezone.utc)` |
| Python | `logging.warn()` | `logging.warning()` |
| Python 3.12+ | módulos `imp`, `distutils` (removidos) | `importlib`, `setuptools` / `packaging` |
| Python 3.10+ | `from collections import Mapping`, `Iterable`... | `collections.abc` |
| Python | `unittest` `assertEquals` e similares | `assertEqual` |
| SQLAlchemy 2.0 | `Model.query.get(id)` (legado) | `db.session.get(Model, id)` |
| SQLAlchemy 2.0 | `engine.execute(...)` (removido) | `with engine.connect() as c: c.execute(text(...))` |
| SQLAlchemy 2.0 | `from sqlalchemy.ext.declarative import declarative_base` | `from sqlalchemy.orm import declarative_base` |
| Flask 2.3+ | `@app.before_first_request` (removido) | inicialização no app factory ou `with app.app_context()` |
| Flask 2.3+ | `app.json_encoder`, `flask.json.JSONEncoder` (removidos) | `app.json` provider customizado |
| Flask 3.0 | `flask.escape`, `flask.Markup` (removidos) | `markupsafe.escape`, `markupsafe.Markup` |
| Node.js | `new Buffer(x)`, `Buffer(x)` | `Buffer.from(x)`, `Buffer.alloc(n)` |
| Node.js | `fs.exists()` | `fs.existsSync()` ou `fs.promises.access()` |
| Node.js | `url.parse()` | `new URL(...)` |
| Node.js | `crypto.createCipher/createDecipher` | `crypto.createCipheriv/createDecipheriv` |
| Node.js | `util.isArray` e similares | `Array.isArray` |
| Express 4.16+ | `body-parser` como dependência separada | `express.json()`, `express.urlencoded()` |
| Express 4 | `req.param('x')`, `res.send(status, body)`, `res.json(status, body)`, `res.redirect(body, status)`, `app.del()` | `req.params/query/body`, `res.status(n).send(...)`, `res.status(n).json(...)`, `res.redirect(status, url)`, `app.delete()` |
| Node.js | pacotes `request`, `node-uuid` (descontinuados) | `fetch`/`axios`/`undici`, `crypto.randomUUID()` / `uuid` |
| JS | `var` | `const` / `let` |

Se a versão declarada ainda suporta a API e ela não está marcada como deprecated, **não** registre como finding.

### AP-17 Integridade referencial e dados órfãos
- **Sinais:** `DELETE` de entidade pai sem tratar filhos (matrículas, pagamentos, itens, tarefas); ausência de `FOREIGN KEY` ou `ON DELETE`; exclusão manual de filhos em loop; mensagem que admite o problema; resposta de sucesso ignorando o erro do banco.
- **Por que importa:** dados sujos e relatórios errados.
- **Transformação:** T-17.

### AP-18 Callback hell
- **Sinais:** callbacks aninhados em 3 ou mais níveis, contadores manuais de "pendentes" (`pending--`), `res.json` chamado dentro do último callback; ordem não determinística do resultado.
- **Por que importa:** ilegível, propenso a erro e a respostas duplicadas.
- **Transformação:** T-16.

### AP-19 CORS aberto e configuração de produção insegura
- **Sinais:** `CORS(app)` ou `cors()` sem origens restritas (**sempre registre**, mesmo em API de exemplo), `Access-Control-Allow-Origin: *` em API com dados sensíveis; ambiente "producao" declarado com debug ligado.
- **Por que importa:** qualquer site pode chamar a API do navegador do usuário.
- **Transformação:** T-01 (origens via configuração).

---

## LOW

### AP-20 Magic numbers e magic strings
- **Sinais:** números de regra soltos no código (`10000`, `0.1`, `5000`); strings de status repetidas (`'PAID'`, `'pendente'`); listas literais de valores válidos; porta fixa.
- **Transformação:** T-15.

### AP-21 Logging por print/console.log
- **Sinais:** `print(...)`, `console.log(...)` como log de aplicação, sem nível nem formato.
- **Transformação:** T-15.

### AP-22 Nomenclatura ruim
- **Sinais:** variáveis de uma letra ou siglas (`u`, `e`, `p`, `cid`, `cc`), nomes que sobrescrevem builtins (`id`, `type`, `list`), mistura de idiomas ou estilos (camelCase e snake_case), classes genéricas (`Manager`, `Helper`, `Utils`).
- **Transformação:** T-15 (renomear sem mudar o contrato HTTP).

### AP-23 Código morto, imports e dependências sem uso
- **Verificação obrigatória:** para cada import, busque o nome no resto do arquivo (por exemplo, `request` pode estar importado e ser usado mais abaixo). Só é "sem uso" se aparecer apenas na linha do import.
- **Sinais:** imports não usados; funções, helpers e constantes nunca chamados; classes nunca instanciadas; dependências no manifesto que nenhum arquivo importa; aninhamento de `if/else` desnecessário que devolve booleano.
- **Transformação:** T-13.

---

## Distribuição mínima esperada

O catálogo cobre as quatro severidades. Em qualquer projeto, procure ativamente por pelo menos um item de cada severidade, mas **só reporte o que existe**. Um projeto sem ocorrência de uma entrada simplesmente não a lista.

# Refatoração Arquitetural Automatizada: skill `refactor-arch`

Skill de IA que **analisa, audita e refatora** um projeto backend para o padrão **MVC**, independente da tecnologia. O desafio usa 3 projetos legados: dois em Python/Flask (`code-smells-project`, `task-manager-api`) e um em Node.js/Express (`ecommerce-api-legacy`).

## Ferramenta e convenção de pastas

Ferramenta escolhida: **OpenAI Codex**. O enunciado usa o Claude Code como referência (`.claude/skills/refactor-arch/` e `claude "/refactor-arch"`). Conforme a nota do próprio desafio, adaptei para a convenção do Codex:

| Enunciado (Claude Code) | Este projeto (Codex) |
|---|---|
| `.claude/skills/refactor-arch/` | `.agents/skills/refactor-arch/` |
| `claude "/refactor-arch"` | `codex` e depois `$refactor-arch` |

A estrutura interna (`SKILL.md` + arquivos de referência em Markdown) é a mesma.

## Índice

- [A) Análise Manual](#a-análise-manual)
- [B) Construção da Skill](#b-construção-da-skill)
- [C) Resultados](#c-resultados)
- [D) Como Executar](#d-como-executar)

---

## A) Análise Manual

Convenção: `arquivo:linha(s)`. Severidades conforme a escala do desafio (CRITICAL, HIGH, MEDIUM, LOW).

---

### Projeto 1: code-smells-project (Python/Flask, API de E-commerce)

Arquitetura atual: 4 arquivos (`app.py`, `controllers.py`, `models.py`, `database.py`) e SQL cru com SQLite. As camadas existem só no nome: o model contém regra de negócio e o arquivo de rotas executa SQL.

| # | Sev. | Local | Problema | Por que é relevante |
|---|---|---|---|---|
| P1-1 | CRITICAL | `models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-128, 140, 149-166, 174, 188, 192, 220, 224, 279-281, 289-297` | SQL Injection: queries montadas por concatenação de strings | Qualquer parâmetro (`nome`, `email`, `termo`, `status`) permite ler, alterar ou apagar o banco. No login (`109-111`), `' OR '1'='1` ignora a autenticação. |
| P1-2 | CRITICAL | `app.py:47-57` (`/admin/reset-db`), `app.py:59-78` (`/admin/query`) | Endpoints administrativos sem autenticação, um deles executa SQL arbitrário | Qualquer cliente apaga todas as tabelas ou roda qualquer SQL. |
| P1-3 | HIGH | `models.py:133-169` (estoque e total do pedido), `235-273` (desconto por faturamento) | Regra de negócio e serialização dentro da camada Model | O model deveria só acessar dados. Misturar regra e SQL impede testar cada parte isolada. |
| P1-4 | HIGH | `app.py:47-78` | Rotas executam SQL direto, sem controller nem model | Viola a separação de camadas: o arquivo de roteamento conhece o banco. |
| P1-5 | HIGH (extra) | `database.py:4, 8-10` | Estado global mutável: `db_connection` único e compartilhado, com `check_same_thread=False` | Acoplamento oculto, difícil de testar e inseguro com concorrência. |
| P1-6 | MEDIUM | `models.py:187-193, 219-225` (e `154-161`) | Queries N+1 ao listar pedidos e itens | Uma nova query por pedido e por item. Degrada rápido com volume. |
| P1-7 | MEDIUM | `models.py:12-21, 31-40, 304-313` (produto); `178-200` e `211-232` (pedido); `controllers.py:30-50` e `74-90` | Código duplicado de serialização e validação | A mesma lógica copiada em vários pontos, e a validação do update é mais fraca que a do create. |
| P1-8 | LOW | `models.py:257-262`; `controllers.py:49, 52, 242` | Magic numbers e listas fixas (10000, 5000, 1000, percentuais, categorias, status) | Regras de negócio soltas, sem constante nomeada. |
| P1-9 | LOW | `controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 219, 248, 250`; `app.py:56, 83-86` | `print()` no lugar de logging | Sem níveis de log nem formato padrão. |
| P1-10 | LOW (extra) | `database.py:2, 5`; `models.py:2` | `import os` e `import sqlite3` sem uso, e `db_path` fixo no código | Poluição e configuração não externalizada. |

Observações: `requirements.txt` (`flask==3.1.1`, `flask-cors==5.0.1`) não tem APIs deprecated. Os achados abaixo foram vistos, mas deixados de fora da lista acima:

- Credenciais hardcoded e `DEBUG` ligado: `app.py:7-8, 88`.
- Senhas em texto puro, inclusive devolvidas por `GET /usuarios`: `models.py:83, 99, 110, 128`; seed em `database.py:76-78`.
- `secret_key` vazando no `/health`: `controllers.py:285-289`.
- Acoplamento do controller ao banco: `controllers.py:3, 266-275`.
- `criar_pedido` sem transação segura: `models.py:133-169`.
- Validações ausentes: `controllers.py:87-90, 157-158, 169-171, 198-201, 239-240`.
- Cancelar pedido não devolve estoque: `controllers.py:249-250`.
- `try/except` repetido que devolve `str(e)`: `controllers.py`, em quase toda função.
- CORS aberto: `app.py:9`.

---

### Projeto 2: ecommerce-api-legacy (Node.js/Express, LMS API com checkout)

Arquitetura atual: 3 arquivos em `src/`. Um único `AppManager.js` (141 linhas) cria o banco, define as rotas, processa pagamento e gera relatório. Banco SQLite em memória.

| # | Sev. | Local | Problema | Por que é relevante |
|---|---|---|---|---|
| P2-1 | CRITICAL | `utils.js:2-5` | Credenciais hardcoded (`dbPass`, `paymentGatewayKey: "pk_live_..."`, SMTP) | Segredos no repositório. Quem lê o código tem acesso ao gateway de pagamento. |
| P2-2 | CRITICAL | `AppManager.js:45` | O log imprime o número completo do cartão e a chave do gateway | Vazamento de dado de pagamento em log, violação de PCI. |
| P2-3 | CRITICAL | `utils.js:17-23`; `AppManager.js:18, 68` | `badCrypto` é base64 repetido, não um hash. Senha padrão `"123456"`, e o seed guarda `'123'` em texto puro | Senhas efetivamente reversíveis e previsíveis. |
| P2-4 | CRITICAL | `AppManager.js:4-139` | God Class: cria o banco, define rotas, processa pagamento, matrícula e relatório | Impossível testar em isolamento. Qualquer mudança afeta tudo. |
| P2-5 | HIGH | `AppManager.js:28-78` | Regra de negócio do checkout dentro do handler da rota | Controller pesado, sem service nem model. |
| P2-6 | HIGH | `utils.js:9-10, 12-15, 25`; `AppManager.js:59` | Estado global mutável (`globalCache`, `totalRevenue`) | Compartilhado por todo o processo. `totalRevenue` é exportado por valor e nunca atualiza. |
| P2-7 | HIGH | `AppManager.js:2, 7`; `app.js:8-10` | Acoplamento: o banco é criado no construtor e a config é importada direto, sem DI | Não dá para trocar o banco nem testar com um mock. |
| P2-8 | HIGH | `AppManager.js:80` (relatório financeiro), `131-137` (DELETE usuário) | Rotas sensíveis e destrutivas sem autenticação nem autorização | Qualquer pessoa lê dados financeiros ou apaga usuários. |
| P2-9 | MEDIUM | `AppManager.js:83-127` | Relatório financeiro com N+1 e 4 níveis de callbacks. Erros ignorados em `92-93, 104, 106` | Uma query por matrícula e outra por pagamento. Se `err`, `enrollments.length` quebra. |
| P2-10 | MEDIUM | `AppManager.js:50-63` | Checkout sem transação, com matrícula, pagamento e auditoria encadeados. O erro do audit é ignorado (`57`) | Falha no meio deixa matrícula sem pagamento. |
| P2-11 | MEDIUM | `AppManager.js:131-136` | DELETE de usuário deixa matrículas e pagamentos órfãos, ignora `err` e sempre responde sucesso | Integridade referencial quebrada. A própria mensagem admite o problema. |
| P2-12 | MEDIUM | `AppManager.js:35, 38, 41, 46` | Validação fraca (cartão "válido" se começa com `4`) e respostas inconsistentes (texto solto e JSON) | Sem formato de erro padronizado. |
| P2-13 | LOW | `AppManager.js:29-33` | Nomes crípticos: `u`, `e`, `p`, `cid`, `cc` | Dificulta a leitura. |
| P2-14 | LOW | `AppManager.js:46`; `utils.js:6, 19` | Magic strings e numbers: `'PAID'`, `'DENIED'`, prefixo `"4"`, porta `3000`, `10000` iterações | Valores soltos, sem constante. |
| P2-15 | LOW | `app.js:13`; `utils.js:13`; `AppManager.js:45` | `console.log` no lugar de logger | Sem níveis nem controle do que é logado. |
| P2-16 | LOW | `AppManager.js:2`; `utils.js:25` | Import e export sem uso (`totalRevenue`), e `logAndCache` grava um cache que nada lê | Código morto. |

APIs deprecated: nenhuma confirmada em `package.json`. `express ^4.18.2` está em manutenção, e vale checar a migração para a versão 5.

---

### Projeto 3: task-manager-api (Python/Flask, API de Task Manager)

Arquitetura atual: já tem `models/`, `routes/`, `services/` e `utils/`, mas as rotas fazem tudo (consulta, regra, serialização). `services/notification_service.py` e `utils/helpers.process_task_data` não são usados por ninguém.

| # | Sev. | Local | Problema | Por que é relevante |
|---|---|---|---|---|
| P3-1 | CRITICAL | `app.py:13, 34`; `services/notification_service.py:9-10` | `SECRET_KEY` e senha SMTP hardcoded, `debug=True` com `host='0.0.0.0'` | Segredos no código e console de debug exposto na rede. |
| P3-2 | CRITICAL | `models/user.py:29, 32` | Senhas com MD5 sem salt | Hash quebrável em segundos. |
| P3-3 | CRITICAL | `models/user.py:21`; `routes/user_routes.py:33, 85, 209` | O hash da senha é devolvido pela API (`to_dict`, criação, `GET /users/<id>`, login) | Vaza credenciais de todos os usuários. |
| P3-4 | CRITICAL | `routes/user_routes.py:52, 71-78, 207-210` | Token falso (`'fake-jwt-token-' + id`), nenhuma rota é autenticada e o cliente escolhe o próprio `role` (`admin`) | Qualquer um vira administrador e apaga dados. |
| P3-5 | HIGH | `routes/task_routes.py:12-63`; `routes/report_routes.py:12-101, 103-155` | Rotas com consulta, regra de negócio, agregação e serialização, e acesso direto ao ORM | Sem controllers nem services reais. Impossível testar a regra sem HTTP. |
| P3-6 | MEDIUM | `task_routes.py:41-57`; `user_routes.py:22`; `report_routes.py:55-56, 163` | Queries N+1 (usuário e categoria por tarefa, `len(u.tasks)`, tarefas por usuário, contagem por categoria) | Muitas queries a mais por requisição. |
| P3-7 | MEDIUM | `models/task.py:50-60` vs. `task_routes.py:30-39, 71-80, 284-287`; `user_routes.py:171-180`; `report_routes.py:34-36, 132-135` | Lógica de "atrasada" duplicada 6 vezes, embora `is_overdue()` já exista. A serialização de task também se repete (`task_routes.py:17-28`) | Uma regra, vários lugares. A correção precisa ser feita em todos. |
| P3-8 | MEDIUM | `task_routes.py:92-114, 166-184, 261, 264`; `helpers.py:57-108`; `report_routes.py:196-197` | Validação duplicada e divergente. O helper existe e não é usado. Prioridade como string, `int()` sem tratamento e `data` nulo geram erro 500 | Entradas inválidas derrubam o endpoint. |
| P3-9 | MEDIUM | `task_routes.py:62, 137, 204, 236`; `user_routes.py:130, 149`; `report_routes.py:186, 207, 221`; `helpers.py:46, 49, 88` | `except:` genérico (12 ocorrências) | Engole qualquer erro, incluindo bugs. |
| P3-10 | MEDIUM | 16 usos de `Model.query.get()` e 22 de `datetime.utcnow()` (ex.: `task_routes.py:42, 51, 67`; `models/task.py:15-16, 52`) | APIs deprecated: `Query.get()` (legado no SQLAlchemy 2.0, use `db.session.get(Model, id)`) e `datetime.utcnow()` (deprecated no Python 3.12, use `datetime.now(timezone.utc)`) | Vão quebrar ou gerar warnings em versões futuras. |
| P3-11 | LOW | `task_routes.py:149, 153, 219, 234`; `user_routes.py:83, 89, 147`; `helpers.py:39-41` | `print()` no lugar de logging | Sem níveis nem formato padrão. |
| P3-12 | LOW | `task_routes.py:110, 177`; `models/task.py:39`; `helpers.py:75, 110-116`; `user_routes.py:71, 120` | Status e roles repetidos como listas literais. As constantes de `helpers.py:110-116` existem e não são usadas | Magic values duplicados. |
| P3-13 | LOW | `app.py:7`; `task_routes.py:7`; `user_routes.py:6`; `report_routes.py:6, 8`; `helpers.py:2-7`; `requirements.txt` (`marshmallow`, `requests`, `python-dotenv`) | Imports e dependências sem uso | Superfície desnecessária e ruído. |

Atenção para a Fase 3: trocar MD5 por um hash seguro muda o valor armazenado, e remover o hash da resposta muda o contrato do JSON. A skill precisa tratar o seed e os endpoints que dependem disso, para os endpoints continuarem respondendo.

---

## B) Construção da Skill

### Decisões de design

A skill fica em `.agents/skills/refactor-arch/`. O `SKILL.md` é curto e funciona como o roteiro: diz o que fazer em cada fase e quais regras nunca podem ser quebradas. O conhecimento de domínio fica em arquivos de referência separados, em Markdown.

```
refactor-arch/
├── SKILL.md                   # as 3 fases, regras invariáveis e formatos de saída
├── project-analysis.md        # Fase 1: como detectar linguagem, framework, banco e arquitetura
├── antipatterns-catalog.md    # Fase 2: 23 anti-patterns, sinais de detecção, severidade, APIs deprecated
├── report-template.md         # Fase 2: formato exato do relatório
├── mvc-guidelines.md          # Fase 3: regras do MVC alvo e responsabilidade de cada camada
├── refactoring-playbook.md    # Fase 3: 18 transformações com antes/depois + protocolo de validação
└── scripts/
    ├── verify_report.py       # Fase 2: confere o relatório contra o código antes de mostrá-lo
    └── smoke_test.py          # Fase 3: sobe a aplicação, chama os endpoints e compara antes/depois
```

As escolhas principais:

- **O `SKILL.md` só organiza o trabalho.** Cada arquivo de referência é lido quando a fase dele começa. Assim o agente não carrega o catálogo inteiro durante a análise, e eu consigo ajustar um arquivo sem mexer nos outros.
- **A pausa da Fase 2 é uma regra que não pode ser quebrada.** O `SKILL.md` diz que nenhum arquivo do projeto é criado, alterado ou apagado antes do "y" da pessoa. O relatório só é salvo depois da confirmação.
- **Linha exata ou nada.** Todo finding precisa de arquivo e linhas reais, conferidos abrindo o arquivo. A skill proíbe estimar número de linha.
- **O contrato HTTP é preservado.** Rotas, métodos, formato das respostas e códigos de status continuam iguais. A exceção são as correções de segurança CRITICAL (por exemplo, parar de devolver senha na resposta). Cada exceção tem que aparecer no resumo final como "mudança de contrato deliberada".
- **Validar executando, não declarando.** O `smoke_test.py` grava o comportamento da aplicação antes da refatoração (status e formato do JSON de cada endpoint) e compara depois. A skill só marca "✓" no que ela executou e viu funcionar.
- **A skill não faz commit nem push.** Quem versiona é a pessoa. No fim, ela só sugere uma mensagem de commit.

### Anti-patterns do catálogo e por quê

O catálogo tem **23 anti-patterns** (6 CRITICAL, 5 HIGH, 8 MEDIUM e 4 LOW). Eu montei a lista a partir da minha análise manual dos 3 projetos e da escala de severidade do desafio.

| Severidade | Anti-patterns |
|---|---|
| CRITICAL | credenciais e segredos hardcoded, SQL Injection, God Class/File, senha insegura e autenticação falsa, endpoints sensíveis sem autenticação, exposição de dados sensíveis |
| HIGH | lógica de negócio na camada errada, rotas acessando o banco, acoplamento sem injeção de dependência, estado global mutável, escritas em vários passos sem transação |
| MEDIUM | N+1, código duplicado, validação ausente ou inconsistente, erros engolidos ou vazando detalhes, **APIs deprecated**, dados órfãos, callback hell, CORS aberto |
| LOW | magic numbers, `print`/`console.log` como log, nomes ruins, código morto e dependências sem uso |

Cada item do catálogo traz **sinais concretos de detecção** (por exemplo, "query montada por concatenação dentro de `execute`" ou "`except:` sem tipo"), uma busca sugerida, o que é falso positivo e qual transformação do playbook resolve. Os sinais vieram de problemas que eu vi nos 3 projetos.

A detecção de **APIs deprecated** (AP-16) tem uma tabela por stack (Python, Flask, SQLAlchemy 2.0, Node e Express) com o equivalente moderno. Por exemplo, `datetime.utcnow()` vira `datetime.now(timezone.utc)`, e `Model.query.get()` vira `db.session.get()`. A skill confere a versão declarada no manifesto de dependências antes de registrar o finding.

### Como garanti que a skill não depende de uma tecnologia

- **Sinais por stack, não código por stack.** A Fase 1 reconhece linguagem, framework e banco por tabelas de sinais (arquivos de dependências, imports, `CREATE TABLE`, classes de ORM). O catálogo descreve o problema ("consulta dentro de loop") e mostra como ele aparece em Python e em JavaScript.
- **MVC por responsabilidade.** O `mvc-guidelines.md` define o que cada camada pode e não pode fazer e dá estruturas-alvo para Flask e Express. Em outras linguagens as responsabilidades são as mesmas, só mudam os nomes.
- **Adaptação ao nível de organização.** Quando o projeto já tem camadas (como o `task-manager-api`), a skill mapeia o que existe, preserva o que está adequado e extrai só o que falta.
- **Playbook com exemplos nas duas stacks.** As transformações trazem antes e depois em Python/Flask e em Node/Express.

A prova prática foi rodar a mesma skill, sem alterar nada, em Flask sem camadas, em Express e em Flask parcialmente organizado.

### Desafios encontrados e como resolvi

Foram 3 versões da skill. Cada uma nasceu de um problema que apareceu quando eu rodei no projeto 1.

1. **Os números de linha vinham errados.** Nos primeiros relatórios do projeto 1, a skill apontou `request` como "import sem uso" (ele era usado) e atribuiu `print` a linhas que não tinham `print`, entre outras citações erradas. O agente "conferia de memória". *Como resolvi:* o `SKILL.md` passou a exigir que cada trecho seja reaberto antes de entrar no relatório, e eu escrevi o `scripts/verify_report.py`. Ele lê o relatório, abre cada arquivo e linha citados e acusa `ERROR` quando o trecho não mostra o que o finding diz. Também confere se a soma por severidade bate com o total.
2. **A conferência que o agente fazia sozinho quebrava no Windows.** Ele tentava conferir com `python -c "..."` no PowerShell, as aspas aninhadas davam erro e a checagem falhava sem ninguém perceber. *Como resolvi:* a conferência virou um arquivo de script, recebido por entrada padrão, e o `SKILL.md` proíbe o `python -c` com aspas aninhadas.
3. **A skill esquecia entradas do catálogo.** Nas rodadas do projeto 1, ela deixou passar God File e CORS aberto, mesmo eles estando no catálogo. *Como resolvi:* o `SKILL.md` manda percorrer **todas** as entradas do catálogo, uma a uma. O verificador ganhou uma checagem de cobertura: se ele encontra no código um sinal (por exemplo, `CORS(app)` sem origens ou um arquivo muito grande) e o relatório não tem finding sobre isso, ele avisa.
4. **A classificação da arquitetura precisava de um critério claro.** Projetos com `models.py` e `controllers.py`, mas com SQL nas rotas, podiam ser chamados de várias coisas. *Como resolvi:* acrescentei regras de desempate no `project-analysis.md`. Por exemplo, um arquivo por camada, com a camada "vazando", é "camadas apenas nominais", e "parcialmente em camadas" exige pastas de responsabilidade.
5. **Os acentos saíam quebrados no PowerShell.** A leitura dos arquivos da skill trazia `NÃ£o` no lugar de `Não`. *Como resolvi:* a skill ensina a ler sempre com `Get-Content -Raw -Encoding UTF8`.
6. **O resumo final nem sempre fechava a conta.** No projeto 1, o Codex escreveu "19 corrigidos e 1 não aplicado" para um relatório de 19 findings (ele havia corrigido um extra, e a soma passou do total). Eu corrigi para 18 + 1. No projeto 3, a conversa foi compactada no meio do trabalho e ele parou com só 11 dos 20 findings corrigidos. Eu percebi pelo resumo e pedi para continuar, até chegar em 19 corrigidos e 1 não aplicado, com o teste final passando.
7. **Coisas do ambiente.** O Flask em modo debug deixou um processo segurando o banco do projeto 1 durante o teste. No projeto 2, o `npm install` ficou incompleto dentro da pasta do OneDrive (provavelmente por causa da sincronização), e foi preciso um `npm ci` limpo. Em todos os projetos, gravar em `reports/` (fora da pasta do projeto) exigiu aprovação manual.

O que a skill ainda não faz bem:

- No projeto 3, ela **não registrou o `datetime.utcnow()`** como API deprecated, porque o projeto não declara a versão do Python. Na minha análise manual eu tinha encontrado 22 usos. A refatoração acabou removendo todos, mas o relatório não os listou. Dá para melhorar o catálogo para considerar também a versão do Python instalada.
- A severidade do **CORS aberto** saiu LOW no projeto 1 e MEDIUM no projeto 3. O catálogo diz MEDIUM, então a skill deveria justificar a diferença no texto do finding ou manter a regra.
- A skill foi testada só com a ferramenta **OpenAI Codex**. Em outra ferramenta, o nome da pasta e o comando de invocação mudam.

---

## C) Resultados

Os relatórios completos estão em `reports/`. A skill rodou, sem nenhuma alteração entre um projeto e outro, nos 3 projetos.

### Resumo dos relatórios de auditoria

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total | Corrigidos | Não aplicados | Relatório |
|---|---|---|---|---|---|---|---|---|
| 1. code-smells-project | 6 | 5 | 4 | 4 | **19** | 19 | 0 | [`reports/audit-project-1.md`](reports/audit-project-1.md) |
| 2. ecommerce-api-legacy | 5 | 5 | 5 | 4 | **19** | 19 | 0 | [`reports/audit-project-2.md`](reports/audit-project-2.md) |
| 3. task-manager-api | 5 | 4 | 7 | 4 | **20** | 19 | 1 | [`reports/audit-project-3.md`](reports/audit-project-3.md) |

Os itens **não aplicados** têm motivo:

- **Projeto 1:** nenhum. Na primeira rodada, `/admin/query` ficou atrás do token e só com `SELECT`, e eu contei como "não aplicado". A avaliação apontou que a Recommendation mandava remover a execução de SQL externo. Corrigi o playbook (T-11, T-02) e a Fase 3 do `SKILL.md` (aplicar a Recommendation cláusula por cláusula, com prova por `grep`) e rodei de novo: a rota, o handler e `execute_read_query` foram removidos.
- **Projeto 3:** a linha `db = SQLAlchemy()` continua global. Com o app factory (`create_app`), essa linha só declara a extensão do Flask-SQLAlchemy. Quem inicializa e controla a conexão é cada aplicação (`db.init_app(app)`), então não é uma conexão global compartilhada, e esse é o padrão do próprio Flask-SQLAlchemy. Por isso a skill manteve e justificou o item.

### A skill achou os problemas da análise manual?

Comparei a minha lista da seção A com os relatórios gerados pela skill:

| Projeto | Problemas da análise manual | Encontrados pela skill |
|---|---|---|
| 1 | 10 | 10 |
| 2 | 16 | 16 |
| 3 | 13 | 13, com uma ressalva |

A ressalva é o `datetime.utcnow()` do projeto 3 (item P3-10 da análise manual). A skill registrou o `Query.get()` deprecated, mas não o `utcnow()`. Além disso, a skill achou problemas que eu não tinha listado, como o God File `routes/task_routes.py` e a falta de integridade referencial no projeto 3.

### Estrutura antes e depois

**Projeto 1: code-smells-project** (4 arquivos, ~780 linhas)

Antes:
```
app.py  controllers.py  models.py  database.py  requirements.txt
```
Depois:
```
code-smells-project/
├── app.py                      # app factory e ponto de entrada
├── config/settings.py          # configuração lida do ambiente
├── database.py                 # conexão por requisição
├── routes/api_routes.py        # só mapeia URL e método
├── controllers/
│   ├── admin_controller.py
│   ├── order_controller.py
│   ├── product_controller.py
│   ├── user_controller.py
│   └── errors.py
├── models/
│   ├── admin_model.py
│   ├── order_model.py
│   ├── product_model.py
│   └── user_model.py
├── middlewares/
│   ├── auth.py                 # exige X-Admin-Token
│   └── error_handler.py        # tratamento de erro central
├── .env.example
└── .gitignore
```

**Projeto 2: ecommerce-api-legacy** (3 arquivos, ~180 linhas)

Antes:
```
src/app.js  src/AppManager.js  src/utils.js  api.http  package.json
```
Depois:
```
ecommerce-api-legacy/src/
├── app.js                      # ponto de entrada
├── config/settings.js
├── database/
│   ├── connection.js
│   └── initialize.js           # tabelas e seeds
├── routes/index.js
├── controllers/
│   ├── asyncHandler.js
│   ├── checkoutController.js
│   ├── reportController.js
│   └── userController.js
├── models/
│   ├── checkoutModel.js
│   ├── courseModel.js
│   ├── paymentStatus.js
│   └── userModel.js
└── middlewares/
    ├── auth.js
    ├── errorHandler.js
    └── logger.js
```

**Projeto 3: task-manager-api** (15 arquivos Python, ~1158 linhas)

Antes:
```
app.py  database.py  seed.py  requirements.txt
models/  routes/  services/  utils/
```
Depois:
```
task-manager-api/
├── app.py                      # app factory e ponto de entrada
├── database.py  seed.py
├── config/                     # settings.py e constants.py
├── routes/                     # só mapeiam URL e método
├── controllers/                # fluxo da aplicação e validação
│   ├── task_controller.py
│   ├── user_controller.py
│   ├── report_controller.py
│   └── validation.py
├── models/                     # Task, User, Category e as consultas (repositories.py)
├── middlewares/                # auth, error_handler e errors
├── .env.example
└── .gitignore
```
As pastas `services/` e `utils/` foram removidas porque o código delas não era usado por ninguém (`NotificationService`, que ainda trazia a senha de SMTP escrita no código, e funções auxiliares sem referência). As rotas continuam com os mesmos caminhos e métodos.

### Mudanças de comportamento (deliberadas)

A skill preserva as rotas, os métodos e o formato das respostas. As únicas exceções são correções de segurança, e cada uma ficou listada no resumo da Fase 3. Como elas mudam o comportamento da API, ficam registradas aqui.

**Projeto 1**
- `/admin/reset-db` e `/relatorios/vendas` exigem o header `X-Admin-Token`. Sem token (ou sem `ADMIN_TOKEN` configurado), respondem `403`.
- `/admin/query` foi **removida** (responde `404`). O projeto não executa mais SQL vindo do cliente.
- As respostas de usuários não trazem mais o campo da senha. O `/health` não devolve mais o ambiente, o caminho do banco, o modo debug nem a chave secreta.
- Erros 500 não mostram detalhes internos.
- As senhas do seed são guardadas com hash e configuradas pelo ambiente (`SEED_*_PASSWORD`). Senhas antigas viram hash no primeiro login válido.
- O CORS fica desligado, a menos que `CORS_ORIGINS` seja configurado.

**Projeto 2**
- O relatório financeiro (`GET /api/admin/financial-report`) e a exclusão de usuário (`DELETE /api/users/:id`) exigem `X-Admin-Token`.
- O checkout agora confere a senha de um usuário que já existe (senha errada devolve `401`). As senhas usam scrypt.
- A mensagem da exclusão de usuário agora diz que as matrículas e os pagamentos relacionados também foram removidos. O status continua `200`.

**Projeto 3**
- As respostas de usuários não trazem mais o campo `password`.
- O cadastro público sempre cria usuário com o papel `user`. Trocar o papel exige admin.
- O token de login agora é assinado, e não mais `fake-jwt-token-<id>`.
- Excluir tarefa, usuário e categoria, atualizar usuário e os relatórios exigem `X-Admin-Token`.
- As senhas usam scrypt, com migração do MD5 antigo no login.

### Checklist de validação

Marquei só o que foi verificado. Para cada projeto, a verificação veio de três fontes: a execução do `smoke_test.py` (boot e endpoints), a leitura do relatório gerado contra o código e a árvore de arquivos final.

#### Projeto 1: code-smells-project

**Fase 1: Análise**
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.1.1)
- [x] Domínio da aplicação descrito corretamente (API de e-commerce)
- [x] Número de arquivos analisados condiz com a realidade (4 arquivos, 780 linhas)

**Fase 2: Auditoria**
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos (conferido pelo `verify_report.py`, sem erros)
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (19)
- [x] Detecção de APIs deprecated incluída (se aplicável): não se aplica, as dependências não têm APIs deprecated
- [x] Skill pausa e pede confirmação antes da Fase 3

**Fase 3: Refatoração**
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para visualização ou roteamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente (21 de 21 com o mesmo status; 3 com formato diferente por segurança)

#### Projeto 2: ecommerce-api-legacy

**Fase 1: Análise**
- [x] Linguagem detectada corretamente (JavaScript/Node.js)
- [x] Framework detectado corretamente (Express 4.18.2)
- [x] Domínio da aplicação descrito corretamente (LMS com checkout)
- [x] Número de arquivos analisados condiz com a realidade (3 arquivos, 180 linhas)

**Fase 2: Auditoria**
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos (conferido pelo `verify_report.py`, sem erros)
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (19)
- [x] Detecção de APIs deprecated incluída (se aplicável): não se aplica, nenhuma foi confirmada em `package.json`
- [x] Skill pausa e pede confirmação antes da Fase 3

**Fase 3: Refatoração**
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para visualização ou roteamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente (6 de 6, sem diferença de formato)

#### Projeto 3: task-manager-api

**Fase 1: Análise**
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.0.0)
- [x] Domínio da aplicação descrito corretamente (gerenciador de tarefas, usuários, categorias e relatórios)
- [x] Número de arquivos analisados condiz com a realidade (15 arquivos, 1158 linhas)

**Fase 2: Auditoria**
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos (conferido pelo `verify_report.py`, sem erros)
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (20), mesmo em um projeto já organizado em pastas
- [x] Detecção de APIs deprecated incluída (`Query.get()`; o `utcnow()` ficou de fora, veja a seção B)
- [x] Skill pausa e pede confirmação antes da Fase 3

**Fase 3: Refatoração**
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para visualização ou roteamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente (26 de 26 com o mesmo status; 3 com formato diferente porque o hash da senha saiu das respostas)

### Evidências das aplicações rodando

A comparação com o comportamento original foi feita pelo `smoke_test.py`, que sobe a aplicação, chama cada endpoint e compara com o que foi gravado antes da refatoração. Este foi o resultado final de cada projeto, copiado do terminal:

```
Projeto 1:  Resumo: 21 endpoints | FAIL: 0 | DIFF: 3
Projeto 2:  Resumo: 6 endpoints  | FAIL: 0 | DIFF: 0
Projeto 3:  Resumo: 26 endpoints | FAIL: 0 | DIFF: 3
```

- `FAIL: 0` significa que nenhum endpoint mudou de status nem deixou de responder.
- `DIFF` conta os endpoints cujo formato do JSON mudou. Os 3 do projeto 1 e os 3 do projeto 3 são as mudanças de segurança listadas acima (senha e configuração saíram das respostas).
- Além da comparação, a skill chamou as rotas protegidas **sem token** e conferiu que elas respondem `403` (3 rotas no projeto 1, 2 no projeto 2 e 6 verificações no projeto 3).

<!-- Para completar: se quiser, adicione aqui prints do terminal de cada projeto rodando (python app.py / npm start) e de uma chamada em /health, salvos em uma pasta docs/ -->

### Observações sobre o comportamento em stacks diferentes

- **Projeto 1 (Flask sem camadas reais).** Foi a refatoração mais profunda. O `models.py` e o `controllers.py` viraram pastas com um arquivo por domínio (produtos, usuários, pedidos e admin). A skill também trocou a conexão global por uma conexão por requisição e as queries concatenadas por queries com parâmetros.
- **Projeto 2 (Express).** O arquivo único `AppManager.js` (uma classe com banco, rotas, checkout e relatório) foi dividido em config, banco, rotas, controllers, models e middlewares. A skill também trocou os callbacks aninhados por `async/await` e juntou as gravações do checkout numa transação. Foi o projeto em que a skill mais mostrou que não depende de Python, mas o ambiente deu mais trabalho (o módulo nativo do `sqlite3`).
- **Projeto 3 (Flask já organizado em pastas).** Aqui a skill não refez do zero. Ela manteve `routes/` como mapeamento de URL, tirou a lógica dos handlers para `controllers/` e as consultas para `models/`. Foi o projeto em que a análise precisou diferenciar "tem pastas" de "tem camadas de verdade". Foi também o único em que a Fase 3 parou no meio e precisou ser retomada.

---

## D) Como Executar

### Pré-requisitos

- **OpenAI Codex** instalado e autenticado (pela extensão do VS Code, ou pela linha de comando: `npm install -g @openai/codex` e depois `codex login`).
- Python 3 e `pip` (projetos 1 e 3), e Node.js com `npm` (projeto 2).
- Um terminal aberto na pasta do projeto (no Windows, o PowerShell funciona).

### Executar a skill em cada projeto

A skill está em `.agents/skills/refactor-arch/` dentro de cada um dos 3 projetos. A primeira pasta que usei foi `code-smells-project`, e depois copiei a skill para as outras duas.

```powershell
# Projeto 1
cd code-smells-project
codex
# dentro do Codex, digite:  $refactor-arch salve o relatório como audit-project-1.md

# Projeto 2 (copiando a skill antes)
cd ..
Copy-Item .\code-smells-project\.agents\skills\refactor-arch .\ecommerce-api-legacy\.agents\skills\ -Recurse -Force
cd .\ecommerce-api-legacy
codex
# $refactor-arch salve o relatório como audit-project-2.md

# Projeto 3 (copiando a skill antes)
cd ..
Copy-Item .\code-smells-project\.agents\skills\refactor-arch .\task-manager-api\.agents\skills\ -Recurse -Force
cd .\task-manager-api
codex
# $refactor-arch salve o relatório como audit-project-3.md
```

Como funciona na prática:

1. Ao digitar `$refactor-arch`, aparece a lista de skills. O primeiro Enter insere o nome e o segundo envia.
2. A skill faz a Fase 1 (análise) e a Fase 2 (auditoria) sem alterar nenhum arquivo e termina com a pergunta `Proceed with refactoring (Phase 3)? [y/n]`.
3. Leia o relatório. Se estiver de acordo, responda `y`. Aí a Fase 3 salva o relatório em `reports/`, refatora e valida.
4. Use o modo interativo (não `codex exec`), porque a Fase 2 precisa da sua resposta antes de modificar qualquer arquivo.
5. O Codex pede permissão para instalar dependências e para gravar fora da pasta do projeto (o `reports/`). Leia cada comando antes de aprovar.

### Como validar que a refatoração funcionou

**1. Rodar cada aplicação.** As rotas que antes eram abertas e agora exigem `X-Admin-Token` precisam da variável `ADMIN_TOKEN` configurada (veja o `.env.example` de cada projeto). Exemplo no PowerShell:

```powershell
# Projeto 1 (porta 5000)
cd code-smells-project
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:ADMIN_TOKEN = "troque-por-um-valor-longo"
python app.py

# Projeto 2 (porta 3000)
cd ecommerce-api-legacy
npm install
$env:ADMIN_TOKEN = "troque-por-um-valor-longo"
npm start

# Projeto 3 (porta 5000)
cd task-manager-api
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:ADMIN_TOKEN = "troque-por-um-valor-longo"
python seed.py
python app.py
```

Com a aplicação no ar, abra `http://localhost:<porta>/health` (projetos 1 e 3) ou use o `api.http` (projeto 2). Uma rota protegida sem o header deve responder `403`, e com o header `X-Admin-Token: <valor>` deve funcionar.

**2. Comparar com o comportamento anterior.** O script da skill faz isso automaticamente:

```powershell
python .agents/skills/refactor-arch/scripts/smoke_test.py --cmd "<comando de execução>" `
    --base-url http://localhost:<porta> --endpoints <endpoints.json> --compare <baseline.json>
```

`PASS` quer dizer status e formato iguais. `DIFF` quer dizer que o formato mudou (aceitável só nas correções de segurança listadas no resumo da Fase 3). `FAIL` quer dizer erro e precisa de correção.

**3. Conferir o relatório antes de aprovar a Fase 3.** O `verify_report.py` roda sozinho dentro da Fase 2, mas também dá para usá-lo à mão:

```powershell
python .agents/skills/refactor-arch/scripts/verify_report.py --root . --report ..\reports\audit-project-1.md
```

`ERROR` indica citação de linha errada ou contagem que não fecha. `WARN` indica algo para conferir.

**4. Ler o resumo da Fase 3** (nova estrutura, mudanças de contrato e o que ficou como "não aplicado") e conferir o `git diff` antes de commitar. A skill nunca faz commit sozinha.

### Ordem de execução que usei

1. Análise manual dos 3 projetos (seção A).
2. Criação da skill no projeto 1, com 3 versões até ela passar a conferir os próprios achados.
3. Execução nos projetos 1, 2 e 3, nessa ordem, com um commit por projeto.
4. Preenchimento deste README.

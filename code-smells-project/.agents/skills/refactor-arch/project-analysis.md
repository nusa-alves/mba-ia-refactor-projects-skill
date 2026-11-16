# Análise de projeto (Fase 1)

Objetivo: descobrir o que o projeto é, sem modificar nada. Tudo aqui é leitura.

## 1. Inventário de arquivos

Liste os arquivos-fonte e **ignore**:

- Dependências e ambientes: `node_modules/`, `venv/`, `.venv/`, `env/`, `vendor/`, `site-packages/`, `target/`, `bin/`, `obj/`
- Gerados: `__pycache__/`, `*.pyc`, `dist/`, `build/`, `.next/`, `coverage/`
- Controle de versão e IDE: `.git/`, `.idea/`, `.vscode/`, `.agents/`, `.claude/`
- Lockfiles: `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `poetry.lock`, `Pipfile.lock`
- Dados: `*.db`, `*.sqlite`, `*.sqlite3`, `*.log`
- Documentação e requests de exemplo (leia, mas não conte como código): `README*`, `*.http`

Conte arquivos-fonte e linhas de código reais (por exemplo, `wc -l` ou equivalente da plataforma). O número impresso na Fase 1 tem de bater com a realidade.

## 2. Linguagem

| Sinal | Linguagem |
|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py`, `*.py` | Python |
| `package.json`, `*.js`, `*.mjs`, `*.cjs` | JavaScript (Node.js) |
| `tsconfig.json`, `*.ts` | TypeScript |
| `pom.xml`, `build.gradle`, `*.java` | Java |
| `composer.json`, `*.php` | PHP |
| `Gemfile`, `*.rb` | Ruby |
| `go.mod`, `*.go` | Go |
| `*.csproj`, `*.cs` | C# |

Em caso de mistura, a linguagem é a do código do servidor (ignore scripts auxiliares).

## 3. Framework e versão

Leia o manifesto de dependências para obter a **versão declarada**. Confirme pelos imports no código.

| Dependência / import | Framework |
|---|---|
| `flask`, `from flask import` | Flask |
| `fastapi`, `from fastapi import` | FastAPI |
| `django`, `urls.py`, `settings.py` | Django |
| `express`, `require('express')`, `from 'express'` | Express |
| `@nestjs/core` | NestJS |
| `fastify`, `koa`, `hapi` | Fastify / Koa / Hapi |
| `spring-boot-starter-web` | Spring Boot |
| `laravel/framework` | Laravel |
| `rails` | Ruby on Rails |
| `gin-gonic/gin`, `labstack/echo` | Gin / Echo |

Anote também extensões relevantes (CORS, ORM, auth, validação, cliente HTTP, e-mail).

## 4. Banco de dados

| Sinal | Banco / acesso |
|---|---|
| `import sqlite3`, `sqlite3` no `package.json`, `sqlite:///`, `*.db` | SQLite |
| `psycopg2`, `pg`, `postgres://` | PostgreSQL |
| `mysql`, `mysql2`, `pymysql` | MySQL |
| `pymongo`, `mongoose`, `mongodb://` | MongoDB |
| `redis` | Redis |
| `flask_sqlalchemy`, `sqlalchemy` | ORM SQLAlchemy |
| `sequelize`, `typeorm`, `prisma`, `knex` | ORM / query builder JS |

Para listar **tabelas ou coleções**, procure por:

- `CREATE TABLE` (SQL cru)
- Classes que herdam de `db.Model`, `Base`, `Model`, `mongoose.Schema`, `@Entity`
- Arquivos de migration

Registre se o banco é arquivo local, em memória (`:memory:`) ou servidor externo.

## 5. Entry point e execução

Procure, nesta ordem: `scripts.start` no `package.json`, `main` no `package.json`, `if __name__ == "__main__"`, `app.run(`, `app.listen(`, `manage.py`, `Procfile`, `Dockerfile`, comando no README.

Registre o comando de execução e a porta.

| Stack | Comando típico |
|---|---|
| Flask | `python app.py` ou `flask run` |
| FastAPI | `uvicorn main:app` |
| Django | `python manage.py runserver` |
| Express | `npm start` ou `node src/app.js` |

## 6. Domínio

Deduza o domínio olhando, nesta ordem:

1. Nomes das rotas (`/produtos`, `/pedidos`, `/checkout`, `/tasks`)
2. Nomes das tabelas e dos models
3. Nomes dos arquivos e do README

Descreva em uma frase: "API de E-commerce (produtos, pedidos, usuários)", "LMS com fluxo de checkout (cursos, matrículas, pagamentos)", "Gerenciador de tarefas (tasks, usuários, categorias)".

## 7. Mapeamento de rotas

Liste as rotas (método e caminho) para usar na validação da Fase 3.

| Framework | Onde procurar |
|---|---|
| Flask | `@app.route`, `@bp.route`, `add_url_rule`, `register_blueprint` |
| FastAPI | `@app.get`, `@router.post` |
| Django | `urlpatterns` |
| Express | `app.get/post/put/delete`, `router.*`, `app.use('/prefix', router)` |

Anote o prefixo de cada blueprint ou router. Cruze com `api.http` ou README quando existir.

## 8. Classificação da arquitetura

Escolha **uma** e justifique em uma linha:

| Classe | Sinais |
|---|---|
| **Monolítica sem camadas** | Um ou poucos arquivos que misturam rotas, regras, SQL e formatação. Sem pastas de responsabilidade |
| **Camadas apenas nominais** | Existem arquivos como `models`, `controllers` ou `routes`, mas o model contém regra de negócio, o controller acessa o banco ou as rotas executam SQL |
| **Parcialmente em camadas** | Há pastas como `models/`, `routes/`, `services/`, `utils/`, mas as rotas concentram lógica e consulta, e há duplicação entre elas |
| **MVC adequado** | Responsabilidades separadas, configuração externalizada, tratamento de erro central, entry point claro |

**Como desempatar:**

- "Parcialmente em camadas" exige **pastas** de responsabilidade (`models/`, `routes/`, `services/`...) com arquivos por entidade ou domínio.
- Se existe só **um arquivo por camada** (`models.py`, `controllers.py`) e a camada vazou (SQL nos controllers ou rotas, regra de negócio nos models, handlers com acesso ao banco), classifique como **Camadas apenas nominais**.
- Na dúvida entre duas classes, escolha a **mais crítica** e cite o motivo na justificativa.

Complete com observações: onde mora a configuração, como o banco é acessado (conexão global, sessão do ORM), quem trata erros.

## 9. Saída

Imprima o bloco da Fase 1 definido no `SKILL.md`. Valores desconhecidos devem aparecer como "none detected" ou "unknown", nunca inventados.

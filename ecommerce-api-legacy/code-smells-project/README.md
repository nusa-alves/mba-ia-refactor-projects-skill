# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`. Depois da execução da skill, o projeto segue o padrão MVC: `routes/` mapeia URLs, `controllers/` concentram o fluxo, `models/` acessam os dados, `middlewares/` cuidam de autorização e de erros, e `config/` lê a configuração do ambiente.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

## Configuração

A configuração vem de variáveis de ambiente (veja `.env.example`). A aplicação não carrega arquivos `.env` sozinha, então defina as variáveis no terminal antes de iniciar.

- `ADMIN_TOKEN`: obrigatório para usar `/admin/reset-db`, `/admin/query` e `/relatorios/vendas`. Essas rotas exigem o header `X-Admin-Token`. Sem token configurado ou enviado, respondem `403`.
- `SECRET_KEY`, `DEBUG`, `PORT`, `DB_PATH`: configuração geral (padrões seguros).
- `CORS_ORIGINS`: lista de origens permitidas, separadas por vírgula. Sem valor, o CORS fica desligado.
- `SEED_ADMIN_PASSWORD`, `SEED_CUSTOMER_PASSWORD`, `SEED_SECOND_CUSTOMER_PASSWORD`: senhas dos usuários de exemplo. Sem valor, a aplicação gera senhas aleatórias.

As respostas de usuários não incluem mais senha, e o `/health` não expõe configuração interna.

# task-manager-api

API REST para gerenciamento de tarefas, usuários e categorias com Flask e SQLite, usada como entrada do desafio `refactor-arch`. Depois da execução da skill, a aplicação separa Routes (mapeamento de URL e método), Controllers (fluxos da aplicação) e Models (persistência e regras do domínio).

## Como rodar

```bash
python -m venv .venv
.venv\Scripts\activate   # no Windows (PowerShell)
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. Rode o `seed.py` **antes do primeiro boot**, senão os endpoints retornam listas vazias. O banco SQLite fica em `instance/tasks.db`.

## Configuração

A configuração vem de variáveis de ambiente (veja `.env.example`). A aplicação não carrega arquivos `.env` sozinha, então defina as variáveis no terminal antes de iniciar.

- `ADMIN_TOKEN`: obrigatório para as operações protegidas, que exigem o header `X-Admin-Token`: excluir tarefas, atualizar e excluir usuários, relatórios e excluir categorias. Sem token configurado ou enviado, essas rotas respondem `403`.
- `SECRET_KEY`: chave usada para assinar os tokens de login. Sem valor, uma chave aleatória é gerada a cada início, e os tokens antigos deixam de valer.
- `DEBUG`, `HOST`, `PORT`, `DATABASE_URL`, `CORS_ORIGINS`: configuração geral (padrões seguros).

Cadastros públicos sempre criam usuários com o papel `user`. Senhas MD5 que já existiam são migradas para scrypt no próximo login válido, e as respostas não incluem mais o hash da senha.

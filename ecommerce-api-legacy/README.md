# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Defina `ADMIN_TOKEN` no ambiente antes de iniciar a aplicação. As rotas `GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem esse valor no header `X-Admin-Token`; sem token configurado ou enviado, respondem `403`. `PORT`, `DB_PATH` e `SEED_USER_PASSWORD` também podem ser definidos no ambiente. A senha informada em `SEED_USER_PASSWORD` é aplicada à conta de seed somente quando ela é criada. O arquivo `.env.example` lista as variáveis, mas a aplicação não carrega arquivos `.env` automaticamente.

Exemplos de requisições estão em `api.http`.

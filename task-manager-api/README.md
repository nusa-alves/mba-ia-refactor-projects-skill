# task-manager-api

API REST para gerenciamento de tarefas, usu?rios e categorias com Flask e SQLite. A aplica??o segue separa??o entre Routes (mapeamento HTTP), Controllers (fluxos da aplica??o) e Models (persist?ncia e regras do dom?nio).

## Configura??o e execu??o

Crie um ambiente virtual, instale requirements.txt, copie .env.example para .env, execute python seed.py e depois python app.py.

Configure SECRET_KEY e ADMIN_TOKEN no ambiente antes de expor a API. Opera??es protegidas exigem o cabe?alho X-Admin-Token: exclus?o de tasks, altera??o/exclus?o de usu?rios, relat?rios e exclus?o de categorias. Sem ADMIN_TOKEN, essas rotas permanecem fechadas. Para desenvolvimento, o banco SQLite usa instance/tasks.db; execute seed.py para popular os dados de demonstra??o.

Cadastros p?blicos sempre criam usu?rios com papel user. Senhas MD5 j? existentes s?o migradas para scrypt no pr?ximo login v?lido.

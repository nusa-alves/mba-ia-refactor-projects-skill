================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0
Files:   15 analyzed | ~1158 lines of code

## Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 7 | LOW: 4

## Findings

### [CRITICAL] Credenciais e segredos hardcoded
File: app.py:13, app.py:34, services/notification_service.py:9-10
Description: A SECRET_KEY e as credenciais SMTP são literais no código; o servidor também inicia com debug=True e host 0.0.0.0 fixos.
Impact: O segredo de sessão e a conta de e-mail podem ser usados por terceiros, e o modo debug expõe recursos internos da aplicação.
Recommendation: Mover segredos, host, porta e debug para Config via ambiente, com defaults seguros (T-01).

### [CRITICAL] God Class / God File / God Method
File: routes/task_routes.py:1-299
Description: O arquivo inteiro reúne rotas, consultas ORM, validação, regras de prazo e prioridade, serialização e estatísticas; handlers e lógica de múltiplos domínios ficam concentrados em um único módulo de 299 linhas.
Impact: Alterações em tarefas, usuários, categorias e relatórios se acoplam e ficam difíceis de testar isoladamente.
Recommendation: Separar Routes de Controllers e Models por domínio, movendo regras de dados aos Models (T-03, T-04, T-05).

### [CRITICAL] Armazenamento de senha inseguro e autenticação falsa
File: models/user.py:29-32, seed.py:19, seed.py:26, seed.py:33, routes/user_routes.py:52, routes/user_routes.py:71-78, routes/user_routes.py:210
Description: Senhas são convertidas com MD5 sem salt; o seed usa senhas triviais; o cadastro aceita role do corpo, inclusive admin; e o login emite token previsível fake-jwt-token-<id>.
Impact: Senhas podem ser quebradas rapidamente e clientes podem forjar privilégios ou tokens de acesso.
Recommendation: Usar hash de senha resistente com salt, atribuir papéis privilegiados apenas por fluxo confiável e emitir token assinado ou aleatório validável (T-06, T-11).

### [CRITICAL] Endpoints sensíveis ou destrutivos sem autenticação
File: routes/task_routes.py:225-227, routes/user_routes.py:134-136, routes/report_routes.py:12-13
Description: Exclusões de tasks e usuários e o relatório agregado são rotas abertas; não há middleware ou decorator de autenticação aplicado às blueprints.
Impact: Qualquer cliente pode apagar dados e consultar informações agregadas de usuários e tarefas.
Recommendation: Proteger Routes sensíveis com Middlewares de autenticação e autorização, validando papel antes de permitir exclusões e relatórios (T-11).

### [CRITICAL] Exposição de dados sensíveis
File: models/user.py:21
Description: User.to_dict inclui o campo password e é usado nas respostas de consulta e login, expondo o hash MD5 armazenado.
Impact: Um vazamento de resposta permite obter hashes de credenciais e atacar contas offline.
Recommendation: Serializar User com allowlist sem password e remover o token previsível das respostas (T-07, T-08).

### [HIGH] Lógica de negócio na camada errada (controller gordo ou model gordo)
File: routes/task_routes.py:92-114, routes/task_routes.py:126-154, routes/task_routes.py:166-184, routes/task_routes.py:200-223
Description: Os handlers de criação e atualização concentram validação, decisão de status e prioridade, verificação de usuários e categorias, conversão de datas, persistência e montagem da resposta.
Impact: Regras do domínio dependem dos requests Flask e se repetem entre create e update.
Recommendation: Mover regras que dependem dos dados aos Models e deixar Controllers validarem a entrada, orquestrarem o fluxo e escolherem o status HTTP (T-04).

### [HIGH] Roteamento ou view acessando o banco
File: routes/task_routes.py:1-3, routes/task_routes.py:14, routes/task_routes.py:147-148
Description: O módulo de Routes importa db e Models e consulta Task.query diretamente nos handlers, além de persistir por db.session.
Impact: A camada HTTP conhece o ORM e mistura roteamento com persistência, dificultando testes e mudanças no banco.
Recommendation: Manter Routes no mapeamento de URL e delegar operações a Controllers; concentrar consultas nos Models (T-05, T-04).

### [HIGH] Acoplamento forte sem injeção de dependência
File: database.py:1, app.py:3, app.py:16, routes/task_routes.py:2
Description: db é criado como extensão global em database.py, inicializado pelo app global e importado diretamente pelas Routes, sem dependências fornecidas aos Controllers.
Impact: Testes e mudanças de configuração ficam acoplados ao singleton de banco e ao módulo Flask global.
Recommendation: Criar dependências no composition root e fornecê-las aos Controllers e Models conforme necessário (T-12).

### [HIGH] Escritas em vários passos sem transação
File: seed.py:11-14, seed.py:37, seed.py:63, seed.py:78-92
Description: seed_data apaga os dados e commita na linha 14, depois commita usuários e categorias separadamente antes de inserir tasks e commitar novamente.
Impact: Uma falha em qualquer etapa posterior deixa o banco vazio ou parcialmente populado, sem rollback da operação completa.
Recommendation: Executar a limpeza e a criação do seed em uma única transação, com rollback em falha (T-10).

### [MEDIUM] Queries N+1
File: routes/task_routes.py:14-16, routes/task_routes.py:41-52, routes/report_routes.py:53-57, routes/report_routes.py:159-164, routes/user_routes.py:12-22
Description: A listagem consulta usuário e categoria dentro do loop de tasks; os relatórios consultam tasks ou contagem de categoria dentro de loops e len(u.tasks) acessa relacionamento lazy para cada usuário.
Impact: O número de consultas cresce com tasks, usuários e categorias, degradando listagens e relatórios.
Recommendation: Consolidar consultas nos Models com joins, agregações e carregamento antecipado dos relacionamentos (T-09).

### [MEDIUM] Código duplicado
File: models/task.py:50-60, routes/task_routes.py:30-39, routes/task_routes.py:71-80, routes/task_routes.py:283-287, routes/user_routes.py:171-180, routes/report_routes.py:33-43, routes/report_routes.py:132-135
Description: A regra de task atrasada já existe em Task.is_overdue, mas é reimplementada nos handlers de listagem, detalhe, estatísticas e relatórios com blocos condicionais equivalentes.
Impact: Correções de prazo ou status podem divergir entre endpoints.
Recommendation: Centralizar a regra no Model Task e reutilizá-la nos Controllers (T-13).

### [MEDIUM] Validação de entrada ausente ou inconsistente
File: routes/task_routes.py:113-114, routes/task_routes.py:181-184, routes/task_routes.py:260-264, routes/report_routes.py:196-202
Description: Prioridade é comparada sem validar tipo; int() dos filtros não trata entradas inválidas; e update de categoria usa request.get_json sem verificar se retornou dados.
Impact: Strings, valores fora de formato ou corpo JSON ausente podem gerar erro 500 em vez de resposta 400 e deixar a API inconsistente.
Recommendation: Validar tipo e formato no Controller antes de comparar ou converter, aplicando a mesma regra em create e update (T-18).

### [MEDIUM] Tratamento de erro engolido, repetido ou vazando detalhes
File: routes/task_routes.py:62-63, routes/task_routes.py:137-138, routes/task_routes.py:151-154, routes/task_routes.py:204-205, routes/task_routes.py:221-223, routes/task_routes.py:236-238, routes/user_routes.py:87-90, routes/user_routes.py:130-132, routes/user_routes.py:149-151, routes/report_routes.py:186-188, routes/report_routes.py:207-209, routes/report_routes.py:221-223, services/notification_service.py:23-25, utils/helpers.py:46-50, utils/helpers.py:88-89
Description: Há except genérico ou nu em handlers e helpers, respostas de erro duplicadas por rota e nenhuma camada central de tratamento; NotificationService também imprime str(e) e converte qualquer falha em False.
Impact: Falhas inesperadas ficam escondidas, difíceis de rastrear e podem expor detalhes em logs.
Recommendation: Tratar exceções específicas nos Controllers e centralizar conversão para respostas HTTP em um Middleware de erro (T-08).

### [MEDIUM] APIs deprecated ou obsoletas
File: requirements.txt:2, routes/report_routes.py:105, routes/report_routes.py:192, routes/report_routes.py:213, routes/task_routes.py:42, routes/task_routes.py:51, routes/task_routes.py:67, routes/task_routes.py:117, routes/task_routes.py:122, routes/task_routes.py:158, routes/task_routes.py:188, routes/task_routes.py:195, routes/task_routes.py:227, routes/user_routes.py:29, routes/user_routes.py:94, routes/user_routes.py:136, routes/user_routes.py:155
Description: Flask-SQLAlchemy 3.1.1 exige SQLAlchemy 2.0.16 ou superior; Query.get é legado/deprecated nessa versão e deve ser substituído por db.session.get(Model, id). O projeto não fixa a versão Python, portanto datetime.utcnow não foi classificado neste finding. [Flask-SQLAlchemy changes](https://flask-sqlalchemy.palletsprojects.com/en/3.1.x/changes/); [SQLAlchemy Query.get docs](https://docs.sqlalchemy.org/en/20/orm/queryguide/query.html).
Impact: O uso da API legada gera deprecation warnings e dificulta futuras atualizações.
Recommendation: Substituir Model.query.get(id) por db.session.get(Model, id) nos Controllers ou Models conforme a responsabilidade (T-14).

### [MEDIUM] Integridade referencial e dados órfãos
File: models/task.py:13-14, models/task.py:20-21, routes/report_routes.py:211-223
Description: Task declara chaves estrangeiras sem ON DELETE ou cascade; a exclusão de Category tenta remover a categoria sem tratar tasks dependentes.
Impact: A exclusão pode falhar por restrição ou deixar tasks sem categoria, conforme a configuração de enforcement do SQLite.
Recommendation: Definir cascata apropriada nos Models e remover ou reatribuir dependentes na mesma transação do Controller (T-17).

### [MEDIUM] CORS aberto e configuração de produção insegura
File: app.py:15
Description: CORS(app) habilita CORS sem restringir origens.
Impact: Qualquer origem web pode enviar chamadas à API pelo navegador do usuário.
Recommendation: Definir origens permitidas em Config e passá-las explicitamente ao middleware CORS (T-01).

### [LOW] Magic numbers e magic strings
File: routes/task_routes.py:103-114, routes/task_routes.py:176-183, routes/report_routes.py:45
Description: Status, limites de prioridade 1 e 5 e janela de atividade de 7 dias são valores literais nos handlers; listas de status são repetidas apesar de haver constantes em utils.helpers.
Impact: Ajustes podem divergir entre endpoints e os números não mostram o significado da regra.
Recommendation: Usar constantes de domínio em Config ou Models e reutilizá-las nos Controllers (T-15).

### [LOW] Logging por print/console.log
File: routes/task_routes.py:149, routes/task_routes.py:153, routes/task_routes.py:219, routes/task_routes.py:234, routes/user_routes.py:83, routes/user_routes.py:89, routes/user_routes.py:147, services/notification_service.py:21, services/notification_service.py:24, utils/helpers.py:39, utils/helpers.py:41, seed.py:93-96
Description: Rotas, helpers, serviço e seed usam print como logging sem nível ou formato consistente; alguns prints incluem str(e).
Impact: Logs são difíceis de filtrar e investigar em produção.
Recommendation: Configurar logging estruturado no entry point e usar logger nos Controllers, Middlewares e Services (T-15).

### [LOW] Nomenclatura ruim
File: routes/report_routes.py:33, routes/report_routes.py:55, routes/task_routes.py:16, routes/report_routes.py:161, routes/user_routes.py:14, routes/user_routes.py:37
Description: Loops e handlers usam nomes de uma letra como t, u e c, tornando menos claro qual entidade cada variável representa.
Impact: A leitura e a manutenção dos fluxos ficam mais difíceis.
Recommendation: Usar nomes descritivos para task, user e category sem alterar o contrato HTTP (T-15).

### [LOW] Código morto, imports e dependências sem uso
File: app.py:7, models/task.py:3, routes/report_routes.py:7-8, routes/task_routes.py:7, routes/user_routes.py:6, utils/helpers.py:3-7, requirements.txt:4-6
Description: Imports os, sys, json, time, math, hashlib, format_date e calculate_percentage não são usados nos respectivos arquivos; Marshmallow, requests e python-dotenv também não são importados em nenhum arquivo-fonte.
Impact: Código e dependências sem uso aumentam ruído e custo de manutenção.
Recommendation: Remover imports e dependências não utilizadas após confirmar que não são requisitos operacionais (T-13).

================================
Total: 20 findings
================================

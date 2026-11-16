================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 6 | HIGH: 5 | MEDIUM: 4 | LOW: 4

## Findings

### [CRITICAL] Credenciais e segredos hardcoded
File: app.py:7-9, app.py:88
Description: SECRET_KEY está literal no código e DEBUG fica ativo na configuração e app.run.
Impact: Segredo de sessão exposto e console de depuração potencialmente acessível em execução na rede.
Recommendation: Externalizar segredos e configuração em Config e desativar debug fora do desenvolvimento (T-01).

### [CRITICAL] SQL Injection
File: models.py:28, models.py:47-50, models.py:57-61, models.py:68, models.py:92, models.py:109-111, models.py:126-129, models.py:140, models.py:148-150, models.py:155, models.py:157-160, models.py:163-166, models.py:174, models.py:188, models.py:192, models.py:220, models.py:224, models.py:279-281, models.py:289-299
Description: Consultas concatenam valores de produto, usuário, pedido, busca e status; /admin/query também passa SQL recebido no corpo diretamente a execute.
Impact: Entrada manipulada pode alterar consultas, contornar login, ler ou modificar dados e executar SQL arbitrário.
Recommendation: Usar parâmetros SQL em Models e remover execução de SQL externo, com o acesso roteado por Controllers (T-02).

### [CRITICAL] God File
File: models.py:1-314, controllers.py:1-292
Description: models.py (314 linhas) concentra persistência, serialização e regra de quatro domínios; controllers.py (292 linhas) concentra fluxo, validação, mensagens e notificações de produtos, usuários e pedidos.
Impact: Mudanças e testes ficam acoplados entre domínios e responsabilidades.
Recommendation: Separar Models e Controllers por domínio e manter Routes focadas no roteamento (T-03, T-04, T-05).

### [CRITICAL] Armazenamento de senha inseguro e autenticação falsa
File: database.py:75-78, models.py:83, models.py:99, models.py:109-110
Description: Seeds armazenam senhas em texto puro; os Models selecionam e retornam senha sem hash seguro.
Impact: Uma leitura do banco ou da API permite recuperar credenciais dos usuários.
Recommendation: Armazenar hashes seguros e validar credenciais nos Controllers, sem expor o campo senha (T-06, T-07).

### [CRITICAL] Endpoints sensíveis ou destrutivos sem autenticação
File: app.py:47-57, app.py:59-78
Description: /admin/reset-db apaga tabelas e /admin/query aceita comandos SQL sem verificação de sessão, token ou papel.
Impact: Qualquer cliente pode apagar os dados ou executar comandos no banco.
Recommendation: Proteger rotas administrativas com Middleware de autenticação e autorização; retirar a execução arbitrária (T-11).

### [CRITICAL] Exposição de dados sensíveis
File: models.py:79-86, models.py:95-102, controllers.py:276-290
Description: Dados serializados de usuários incluem senha, e a resposta de /health inclui db_path, debug e secret_key.
Impact: Respostas públicas revelam credenciais e configuração interna, incluindo o segredo da aplicação.
Recommendation: Restringir serialização de Models aos campos seguros e remover segredos e configuração interna das respostas (T-07, T-08).

### [HIGH] Lógica de negócio na camada errada
File: models.py:133-169, models.py:235-273, controllers.py:43-54, controllers.py:195-210, controllers.py:237-250
Description: Controllers validam regras de produto e status e simulam notificações; Models calculam estoque, total, desconto e ticket médio junto à persistência.
Impact: Regras de negócio não podem ser testadas isoladamente e ficam misturadas ao fluxo HTTP ou acesso a dados.
Recommendation: Manter regras que dependem dos dados nos Models e a orquestração e status HTTP nos Controllers (T-04).

### [HIGH] Roteamento ou view acessando o banco
File: app.py:47-55, app.py:59-78, controllers.py:264-274
Description: Handlers definidos diretamente em app.py executam SQL; health_check no Controller obtém conexão e executa consultas diretamente.
Impact: Rotas e Controllers dependem do SQLite concreto e contornam os Models.
Recommendation: Encaminhar acesso a dados dos Controllers para Models e registrar endpoints por Routes (T-05).

### [HIGH] Acoplamento forte sem injeção de dependência
File: database.py:7-12, models.py:1, controllers.py:3
Description: O módulo cria a conexão SQLite globalmente; Models e Controllers importam diretamente o módulo concreto de banco.
Impact: Trocar o banco ou isolar esses componentes em testes exige alterar dependências globais.
Recommendation: Centralizar configuração e fornecer conexão aos Models por uma interface de aplicação/configuração (T-12).

### [HIGH] Estado global mutável
File: database.py:4, database.py:7-10
Description: get_db modifica db_connection global e compartilha uma única conexão SQLite entre chamadas com check_same_thread=False.
Impact: Requisições e testes compartilham estado e podem interferir entre si sob concorrência.
Recommendation: Gerenciar conexões por contexto da aplicação e injetar a dependência nos Models (T-12).

### [HIGH] Escritas em vários passos sem transação
File: models.py:148-168
Description: criar_pedido insere pedido, itens e baixa estoque em múltiplas operações, mas não trata rollback em falhas intermediárias.
Impact: Uma falha pode deixar pedido, itens e estoque inconsistentes.
Recommendation: Agrupar as operações em transação atômica nos Models, com rollback em erro (T-10).

### [MEDIUM] Queries N+1
File: models.py:177-193, models.py:209-225
Description: Para cada pedido são consultados itens e, para cada item, o nome do produto em novas consultas.
Impact: O número de consultas cresce com pedidos e itens e torna as listagens lentas.
Recommendation: Buscar pedidos, itens e produtos em consultas agrupadas nos Models (T-09).

### [MEDIUM] Código duplicado
File: models.py:12-21, models.py:31-40, models.py:304-313, models.py:178-185, models.py:211-218, controllers.py:30-50, controllers.py:74-90
Description: Serialização de produto se repete em três blocos; estrutura de pedido e validações de criação/atualização de produto também são copiadas.
Impact: Ajustes de campos ou regras podem divergir entre endpoints.
Recommendation: Reutilizar serialização e validação nos Models e Controllers correspondentes (T-13).

### [MEDIUM] Validação de entrada ausente ou inconsistente
File: controllers.py:169-171, controllers.py:239-240, controllers.py:87-90
Description: login e atualização de status usam get_json e acessam dados sem validar se o JSON é nulo; validação do update de produto omite limites de nome e categoria aplicados na criação.
Impact: Payloads inválidos podem gerar 500 e atualizações podem aceitar dados que a criação rejeita.
Recommendation: Validar corpo, tipos e regras de campos de forma consistente nos Controllers (T-18).

### [MEDIUM] Tratamento de erro repetido ou vazando detalhes
File: controllers.py:10-12, controllers.py:60-62, controllers.py:254-255, controllers.py:291-292
Description: Controllers repetem captura genérica de Exception e devolvem str(e) ou detalhes internos ao cliente; não há handler central de erro.
Impact: Respostas expõem detalhes internos e o tratamento fica inconsistente entre endpoints.
Recommendation: Centralizar tratamento em Middleware e retornar mensagens públicas padronizadas (T-08).

### [LOW] CORS aberto
File: app.py:9
Description: CORS(app) habilita CORS sem restringir origens.
Impact: Sites de qualquer origem podem iniciar chamadas de navegador à API, inclusive a endpoints com dados sensíveis.
Recommendation: Definir origens permitidas em Config (T-01).

### [LOW] Magic numbers e magic strings
File: models.py:256-262, controllers.py:52-54, controllers.py:242-243, app.py:88
Description: Limites de desconto, categorias, status, porta e flag de debug aparecem como literais no código.
Impact: Alterações de regra exigem localizar e editar valores espalhados, com risco de inconsistência.
Recommendation: Nomear configurações e constantes em Config e nos Models/Controllers por domínio (T-15).

### [LOW] Logging por print
File: controllers.py:8, controllers.py:11, controllers.py:57, controllers.py:61, controllers.py:106, controllers.py:161, controllers.py:179, controllers.py:182, controllers.py:208-210, controllers.py:219, controllers.py:248, controllers.py:250, app.py:56, app.py:83-86
Description: Logs de aplicação usam print sem níveis ou formato estruturado.
Impact: Dificulta filtrar eventos e separar erros de mensagens operacionais.
Recommendation: Usar logger configurado pela aplicação e configuração central (T-15).

### [LOW] Código morto e imports sem uso
File: models.py:2, database.py:2
Description: Os imports sqlite3 em models.py e os em database.py aparecem apenas nas respectivas linhas de importação e não são usados no restante dos arquivos.
Impact: Imports sem uso aumentam ruído e indicam dependências acidentais.
Recommendation: Remover imports não utilizados (T-13).

================================
Total: 19 findings
================================
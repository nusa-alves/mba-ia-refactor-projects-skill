================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express 4.18.2
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 5 | HIGH: 5 | MEDIUM: 5 | LOW: 4

## Findings

### [CRITICAL] Credenciais e segredos hardcoded
File: src/utils.js:2-4
Description: Usuário, senha de banco e chave de pagamento estão definidos como literais no objeto de configuração.
Impact: Quem obtiver acesso ao código pode reutilizar credenciais e acessar serviços externos.
Recommendation: Externalizar segredos em Config via variáveis de ambiente e removê-los do código (T-01).

### [CRITICAL] God Class / God File / God Method
File: src/AppManager.js:4-141
Description: A classe inteira reúne conexão e criação do banco, seeds, rotas, validação, regras de checkout, consultas e montagem de respostas em múltiplos domínios.
Impact: Mudanças de banco, fluxo e HTTP ficam acopladas e difíceis de testar isoladamente.
Recommendation: Separar responsabilidades MVC entre Models, Routes e Controllers, mantendo regras de dados nos Models e orquestração HTTP nos Controllers (T-03, T-04, T-05).

### [CRITICAL] Armazenamento de senha inseguro e autenticação falsa
File: src/AppManager.js:18, src/AppManager.js:68-69, src/utils.js:17-22
Description: A seed armazena senha em texto puro; novas senhas passam por badCrypto, que repete Base64 e trunca o resultado, sem algoritmo seguro de hash de senha. Usuários novos também recebem a senha padrão "123456" quando pwd não é enviada.
Impact: Credenciais podem ser recuperadas ou previsíveis, permitindo tomada de contas.
Recommendation: Armazenar senhas com algoritmo próprio para password hashing e exigir senha válida no Controller (T-06).

### [CRITICAL] Credenciais expostas em log
File: src/AppManager.js:45
Description: O log de processamento registra o valor completo do cartão recebido e a chave do gateway.
Impact: Logs expõem dados de pagamento e segredo de integração.
Recommendation: Remover cartão e segredo dos logs; aplicar mascaramento e logging seguro em Controllers/Config (T-07, T-15).

### [CRITICAL] Endpoints sensíveis ou destrutivos sem autenticação
File: src/AppManager.js:80, src/AppManager.js:131-133
Description: O relatório financeiro administrativo e a exclusão de usuário não verificam autenticação ou papel antes de consultar ou apagar dados.
Impact: Qualquer cliente pode consultar receita e excluir usuários.
Recommendation: Proteger Routes com middleware de autenticação e autorização (T-11).

### [HIGH] Lógica de negócio na camada errada (controller gordo ou model gordo)
File: src/AppManager.js:28-35, src/AppManager.js:43-60, src/AppManager.js:66-75
Description: O handler de checkout valida dados, decide status do pagamento, cria usuário, matrícula e pagamento, registra auditoria e monta resposta HTTP.
Impact: Regras do domínio ficam presas ao Express e são difíceis de testar e reutilizar.
Recommendation: Mover regras de preço e pagamento para Models e deixar Controllers orquestrarem o fluxo e o status HTTP (T-04).

### [HIGH] Roteamento ou view acessando o banco
File: src/AppManager.js:25-26, src/AppManager.js:37-41
Description: setupRoutes define handlers e os handlers acessam diretamente this.db para executar consultas; a mesma estrutura ocorre nas demais rotas da classe.
Impact: Rotas e persistência ficam acopladas, dificultando testes e mudanças no banco.
Recommendation: Manter Routes focadas no mapeamento e delegar acesso a dados aos Models, chamados pelos Controllers (T-05, T-04).

### [HIGH] Acoplamento forte sem injeção de dependência
File: src/AppManager.js:4-7
Description: O construtor instancia diretamente SQLite em memória, acoplando a classe ao banco concreto.
Impact: A troca do banco e o uso de dependências simuladas em testes exigem alterar a classe.
Recommendation: Configurar a conexão em Config e fornecê-la às partes MVC que precisam dela (T-12).

### [HIGH] Estado global mutável
File: src/utils.js:9, src/utils.js:12-14
Description: globalCache é um objeto mutável compartilhado por todas as chamadas e modificado por logAndCache.
Impact: Requisições e testes compartilham estado implicitamente e podem interferir entre si.
Recommendation: Remover o estado global ou encapsulá-lo em dependência configurada e injetada (T-12).

### [HIGH] Escritas em vários passos sem transação
File: src/AppManager.js:50-57
Description: Checkout insere matrícula, pagamento e auditoria em etapas dependentes sem transação; falhas posteriores deixam gravações parciais, e o erro da auditoria é ignorado.
Impact: O banco pode registrar matrícula sem pagamento ou auditoria, embora o fluxo dependa da conclusão conjunta.
Recommendation: Executar as gravações dependentes em transação e tratar rollback no fluxo coordenado pelo Controller/Model (T-10).

### [MEDIUM] Queries N+1
File: src/AppManager.js:89-106
Description: Para cada curso consulta matrículas e, para cada matrícula, consulta usuário e pagamento individualmente.
Impact: O número de consultas cresce com cursos e matrículas, degradando o relatório.
Recommendation: Consolidar as consultas nos Models para carregar os dados relacionados em lote (T-09).

### [MEDIUM] Validação de entrada ausente ou inconsistente
File: src/AppManager.js:29-35
Description: A validação verifica apenas presença truthy de nome, e-mail, curso e cartão; não valida formato, tipo ou comprimento, e pwd pode faltar apesar de ser usado na criação.
Impact: Entradas inválidas passam ao fluxo ou produzem credenciais padrão, causando dados ruins e comportamento inesperado.
Recommendation: Validar campos e formatos no Controller antes de executar regras nos Models (T-18).

### [MEDIUM] Tratamento de erro engolido, repetido ou vazando detalhes
File: src/AppManager.js:57-60, src/AppManager.js:133-135
Description: O callback de auditoria ignora err e retorna sucesso mesmo se a gravação falhar; a exclusão também ignora err e sempre responde que o usuário foi deletado.
Impact: O cliente recebe confirmação falsa e falhas de persistência ficam ocultas.
Recommendation: Tratar erros nos Controllers e centralizar respostas de erro sem ocultar falhas (T-08).

### [MEDIUM] Integridade referencial e dados órfãos
File: src/AppManager.js:14-16, src/AppManager.js:131-135
Description: As tabelas de matrículas e pagamentos não declaram chaves estrangeiras; a rota exclui usuário sem tratar registros dependentes e até informa que eles ficam sujos.
Impact: Matrículas e pagamentos podem ficar órfãos e distorcer relatórios.
Recommendation: Definir integridade referencial nos Models e tratar exclusões dependentes em uma operação consistente (T-17).

### [MEDIUM] Callback hell
File: src/AppManager.js:92-106
Description: O relatório encadeia callbacks de consultas dentro de iterações para cursos e matrículas, com contadores manuais para decidir quando responder.
Impact: Fluxo assíncrono e erros ficam difíceis de acompanhar, com risco de resposta incorreta.
Recommendation: Simplificar o fluxo assíncrono coordenado pelo Controller e manter consultas nos Models (T-16).

### [LOW] Magic numbers e magic strings
File: src/utils.js:19-22, src/AppManager.js:46
Description: O limite 10000 e o tamanho 10 do hash, além dos status "PAID" e "DENIED", aparecem como valores literais de regra.
Impact: Alterações ficam sujeitas a inconsistência e os valores perdem contexto.
Recommendation: Nomear os limites e status em Config ou constantes de domínio usadas pelos Models (T-15).

### [LOW] Logging por print/console.log
File: src/app.js:12-13, src/AppManager.js:45, src/utils.js:13
Description: A aplicação usa console.log para inicialização, processamento de cartão e registro de cache, sem níveis ou estrutura; na linha 45 também são registrados dados sensíveis.
Impact: Logs ficam difíceis de filtrar e podem reter informações impróprias.
Recommendation: Usar logging estruturado e seguro nos Controllers e na inicialização (T-15).

### [LOW] Nomenclatura ruim
File: src/AppManager.js:29-33
Description: O handler usa abreviações pouco claras como u, e, p, cid e cc para dados do checkout.
Impact: A leitura e a manutenção do fluxo ficam menos claras.
Recommendation: Usar nomes descritivos nos Controllers sem alterar o contrato HTTP (T-15).

### [LOW] Código morto, imports e dependências sem uso
File: src/AppManager.js:2
Description: totalRevenue é importado do módulo utils, mas não é referenciado em nenhum outro ponto do arquivo.
Impact: Imports sem uso confundem a leitura e podem ocultar dependências reais.
Recommendation: Remover o import sem uso (T-13).

================================
Total: 19 findings
================================

---
name: refactor-arch
description: Audita e refatora qualquer projeto backend para o padrão MVC em 3 fases (análise, auditoria com relatório e pausa para confirmação, refatoração com validação). Use quando pedirem auditoria de arquitetura, code smells, anti-patterns ou refatoração para MVC.
---

# refactor-arch

Você é um arquiteto de software sênior. Esta skill analisa, audita e refatora uma codebase para o padrão **MVC**, em qualquer linguagem ou framework. Ela roda no diretório atual, que deve ser a raiz do projeto-alvo.

## Arquivos de referência

Leia cada arquivo **quando a fase correspondente começar**, não antes. Os caminhos são relativos a esta pasta (no projeto, `.agents/skills/refactor-arch/`). O script de validação roda com `python .agents/skills/refactor-arch/scripts/smoke_test.py` (use `python3` se `python` não existir).

**Codificação no Windows:** os arquivos desta skill e do projeto estão em UTF-8. No PowerShell, leia com `Get-Content -Raw -Encoding UTF8 <arquivo>`. Sem isso, os acentos aparecem quebrados (por exemplo, `NÃ£o` no lugar de `Não`) e podem ser mal interpretados. Ao gravar arquivos, use UTF-8.

| Arquivo | Usado em | Conteúdo |
|---|---|---|
| `project-analysis.md` | Fase 1 | Como detectar linguagem, framework, banco, domínio e arquitetura |
| `antipatterns-catalog.md` | Fase 2 | Catálogo de anti-patterns com sinais de detecção e severidade, incluindo APIs deprecated |
| `report-template.md` | Fase 2 | Formato exato do relatório de auditoria |
| `mvc-guidelines.md` | Fase 3 | Regras do MVC alvo e responsabilidade de cada camada |
| `refactoring-playbook.md` | Fase 3 | Transformações com exemplos antes/depois e protocolo de validação |
| `scripts/verify_report.py` | Fase 2 | Confere as linhas citadas, imports sem uso, contagens e cobertura do relatório |
| `scripts/smoke_test.py` | Fase 3 | Sobe a aplicação, chama os endpoints e compara antes/depois |

## Regras invariáveis

1. **Nenhum arquivo do projeto é criado, alterado ou apagado antes da confirmação do usuário na Fase 2.** Fases 1 e 2 são somente leitura.
2. **Todo finding precisa de arquivo e linhas reais.** Abra o arquivo, confira o trecho e só então registre. Nunca estime nem invente números de linha, e nunca cite linhas de memória: releia o intervalo (veja a reconferência da Fase 2, passo 4).
3. **Preserve o comportamento.** Rotas, métodos, formato dos payloads e códigos de status continuam iguais. A única exceção são as correções de segurança CRITICAL (por exemplo, parar de devolver senha ou segredo na resposta, proteger rotas administrativas, **remover rotas que executam SQL/comandos vindos do cliente**, que passam a responder 404). Cada exceção deve ser listada no resumo final como "mudança de contrato deliberada".
4. **Seja agnóstico de tecnologia.** Aplique os princípios ao stack detectado, sem assumir Python ou Node.
5. **Não cometa nem faça push.** Quem versiona é o usuário. No fim, sugira uma mensagem de commit.
6. **Seja honesto na validação.** Só escreva "✓" para o que você de fato executou e viu funcionar. Se não conseguiu rodar a aplicação, diga isso e por quê.

## Fase 1: Análise do projeto

1. Leia `project-analysis.md`.
2. Siga as heurísticas para detectar: linguagem, framework e versão, dependências, banco e tabelas, domínio, arquitetura atual, arquivos-fonte analisados (com contagem real) e como a aplicação inicia.
3. Imprima exatamente este bloco:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem>
Framework:     <framework + versão>
Dependencies:  <dependências relevantes>
Domain:        <domínio da aplicação em uma frase>
Architecture:  <classificação + justificativa curta>
Source files:  <N> files analyzed (~<L> lines of code)
DB tables:     <tabelas/coleções, ou "none detected">
Entry point:   <arquivo e comando de execução>
================================
```

## Fase 2: Auditoria

1. Leia `antipatterns-catalog.md` e `report-template.md`.
2. Percorra **todos** os arquivos-fonte contra o catálogo. Use os sinais de detecção e as buscas sugeridas. Confira cada ocorrência abrindo o arquivo. Passe por **todas as entradas do catálogo**, uma a uma, e decida para cada uma se foi encontrada ou não. Não pule nenhuma: as mais esquecidas são God File/Class, CORS aberto e APIs deprecated.
3. Inclua a detecção de **APIs deprecated**, verificando a versão real declarada no manifesto de dependências.
4. **Reconferência obrigatória, antes de imprimir qualquer coisa.** Para **cada** finding do rascunho, reabra o arquivo e leia exatamente as linhas que você vai citar, com os números de linha na tela. Corrija ou remova o que não passar:
   - Cada número de linha ou intervalo citado precisa ter sido lido e mostrar o problema descrito. Nunca cite linha em branco, linha de outro assunto, nem uma consulta fixa (sem valores vindos de fora) como SQL Injection.
   - Para "import ou variável sem uso", **busque o nome no arquivo inteiro** antes de afirmar. Se aparece em qualquer outro ponto além do import, ele está em uso e não é finding.
   - Para "consulta concatenada", confirme na própria linha que há concatenação ou interpolação de valor externo.
   - Prefira intervalos curtos e exatos a intervalos largos "por garantia". Quando o problema é o arquivo todo (por exemplo, God File), cite o intervalo do arquivo e diga isso na `Description`.
   - A severidade é a do catálogo. Só altere com justificativa escrita na `Description`.
   - Recalcule o `Summary` e o `Total` depois de remover ou corrigir findings.
5. **Verificador automático (obrigatório).** Escreva o rascunho do relatório e rode `verify_report.py`. Envie o rascunho pela entrada padrão, sem criar arquivo no projeto. No PowerShell:

```powershell
@'
<rascunho completo, de "ARCHITECTURE AUDIT REPORT" até "Total: N findings">
'@ | python .agents/skills/refactor-arch/scripts/verify_report.py --root . --report -
```

   Em outros shells, ou se preferir, grave o rascunho no **diretório temporário do sistema** (nunca dentro do projeto) e passe o caminho em `--report`.
   - `ERROR`: corrija ou remova o finding. Exemplos: linha que não tem o que o finding descreve, import "sem uso" que na verdade é usado, contagem errada.
   - `WARN`: leia o trecho mostrado e corrija se estiver impreciso. Na seção "Cobertura", um `WARN` significa que há um sinal no código sem finding correspondente (por exemplo, God File, CORS aberto, APIs deprecated): registre o finding, ou confirme por que não se aplica.
   - Rode de novo até não restar `ERROR`. Só então imprima o relatório final.
   - **Nunca** use `python -c "..."` com aspas aninhadas no PowerShell: o comando quebra. Use sempre arquivos de script ou a entrada padrão.
   - Se não conseguir executar o verificador, diga isso no relatório e faça a reconferência manual lendo cada trecho citado (`Select-String` ou `Get-Content arquivo | Select-Object -Index <n-1>`).
6. Produza o relatório **exatamente** no formato de `report-template.md`, com findings ordenados de CRITICAL a LOW.
7. Se o usuário informou um nome de arquivo para o relatório na invocação, use-o. Senão, use `audit-<nome-da-pasta>.md`. O arquivo só é salvo depois da confirmação (veja a Fase 3, passo 1).
8. **PARE.** Termine com a pergunta abaixo e aguarde a resposta do usuário. Não continue por conta própria.

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Se a resposta for `n`, encerre sem modificar nada. Se o usuário pedir ajuste no escopo, atualize o plano e pergunte de novo.

## Fase 3: Refatoração

Só execute depois de um "y" explícito.

1. **Salve o relatório** da Fase 2 em `reports/<nome>.md`. Se o projeto estiver dentro de um repositório git com várias pastas, use a pasta `reports/` na raiz do repositório (crie se não existir). É a única escrita permitida antes das transformações.
2. Leia `mvc-guidelines.md` e `refactoring-playbook.md`.
3. **Baseline antes de mexer**: descubra os endpoints (rotas do código, `api.http`, README), monte o arquivo de endpoints e rode `scripts/smoke_test.py` para registrar o comportamento atual. O procedimento está no fim de `refactoring-playbook.md`.
4. **Planeje** a estrutura MVC alvo conforme `mvc-guidelines.md`. Para projetos já parcialmente organizados, mapeie o que existe e melhore a estrutura sem reescrever o que já está adequado.
5. **Execute as transformações** do playbook, em ordem de severidade (CRITICAL primeiro). Cada finding aprovado tem de acabar corrigido ou explicitamente justificado como não aplicado.
   - **Aplique cada Recommendation por inteiro.** Quebre o texto da Recommendation em cláusulas (por exemplo, "parametrizar" + "remover execução de SQL externo" + "proteger rotas") e aplique todas. Aplicar só a parte mais fácil e marcar o finding como "Fixed" é erro.
   - **Mitigação não é correção.** Restringir, filtrar ou colocar atrás de token algo que a Recommendation manda **remover** (SQL, comando ou código vindo do cliente) não cumpre a cláusula. Remova.
   - "Not applied" é só para o que **não pode** ser feito sem quebrar algo comprovado (e o motivo cita o arquivo e a causa). Nunca use "Not applied" para finding CRITICAL cuja Recommendation seja viável: faça.
6. **Valide**:
   - A aplicação inicia sem erros.
   - Todos os endpoints originais respondem. Rode `scripts/smoke_test.py` de novo, comparando com o baseline.
   - Reexamine o código contra o catálogo e liste o que restou.
   - **Conferência cláusula a cláusula dos CRITICAL**: para cada finding CRITICAL, releia a Recommendation e prove cada cláusula com evidência (grep ou trecho do arquivo). Para SQL Injection e rotas administrativas, rode as buscas do passo final de T-11 e confirme que nenhuma chamada de banco recebe string originada na requisição e que a rota de SQL livre não existe mais. Se alguma cláusula não estiver provada, volte ao passo 5.
7. Se a validação falhar, corrija e valide de novo. Não encerre com a aplicação quebrada.
8. Imprima o resumo final neste formato:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios>

## Findings
Fixed: <N> | Not applied: <N> (com motivo)

## Contract changes (deliberate)
<lista, ou "none">

## Validation
✓/✗ Application boots without errors
✓/✗ <N>/<M> endpoints respond as before
✓/✗ Anti-patterns remaining: <N> (<quais>)

## Suggested commit message
<mensagem>
================================
```

Só use "Zero anti-patterns remaining" se você reexaminou o código e realmente não restou nenhum.

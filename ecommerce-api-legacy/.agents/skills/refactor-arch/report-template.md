# Template do relatório de auditoria (Fase 2)

Use **exatamente** esta estrutura. Substitua os valores entre `<>`. Não acrescente seções, não omita campos.

## Regras

1. **Ordenação:** todos os findings de CRITICAL primeiro, depois HIGH, MEDIUM e LOW. Dentro da mesma severidade, o de maior impacto vem antes.
2. **Localização exata:** `File:` sempre com `arquivo:linha` ou `arquivo:inicio-fim`. Quando houver várias ocorrências, liste todas separadas por vírgula. Caminhos relativos à raiz do projeto.
3. **Um finding por problema.** Ocorrências da mesma natureza (por exemplo, 14 queries concatenadas) formam um único finding com todos os locais.
4. **Título do finding** vem do catálogo (`antipatterns-catalog.md`) ou é uma versão mais específica dele.
5. **Contagens:** o `Summary` e o `Total` têm de bater com a quantidade real de findings do relatório.
6. **Findings de APIs deprecated** seguem o mesmo formato. Em `Description`, cite a versão declarada e o equivalente moderno.
7. **Textos em português**; os rótulos (`File`, `Description`, `Impact`, `Recommendation`) permanecem em inglês, como no template.
8. Mínimo de 5 findings, com pelo menos 1 CRITICAL ou HIGH, quando o código os contiver. Não invente finding para atingir o número.
9. **Todas as linhas citadas foram reabertas e conferidas** (Fase 2, passos 4 e 5), e o `verify_report.py` terminou **sem `ERROR`**. Se uma ocorrência não passou na conferência, ela sai do relatório.
10. **Severidade igual à do catálogo.** Se mudar, justifique em `Description`.
11. **Recomendações em vocabulário MVC** de `mvc-guidelines.md` (Models, Routes, Controllers, Middlewares, Config). Não proponha camadas fora do MVC (como "repositórios") no relatório. Para lógica de negócio, recomende: regras que dependem só dos dados (totais, descontos, estoque) no **Model**, e a orquestração do fluxo e a escolha do status HTTP no **Controller**.

## Modelo

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome da pasta do projeto>
Stack:   <linguagem> + <framework>
Files:   <N> analyzed | ~<L> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <título do anti-pattern>
File: <arquivo:linhas>[, <arquivo:linhas>...]
Description: <o que está errado, citando o trecho ou o comportamento>
Impact: <consequência concreta>
Recommendation: <correção, referenciando a transformação do playbook, por exemplo T-02>

### [CRITICAL] <...>
...

### [HIGH] <...>
...

### [MEDIUM] <...>
...

### [LOW] <...>
...

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Exemplo preenchido (trecho)

```
### [CRITICAL] SQL Injection
File: models.py:28, models.py:47-50, models.py:109-111
Description: Queries montadas por concatenação de strings com dados da requisição (por exemplo, o login em models.py:109-111 concatena email e senha).
Impact: Um atacante lê, altera ou apaga o banco e contorna a autenticação com ' OR '1'='1.
Recommendation: Usar queries parametrizadas (T-02).
```

## Depois da pergunta final

Não escreva mais nada. Aguarde a resposta do usuário.

---
name: implement
description: |
  Executa o plano de implementação da task, criando subagents para tasks complexas ou executando diretamente para tasks simples. Suporta flag --code-like-me para implementação cirúrgica. Use quando o usuário mencionar: "implementar task", "implement", "executar plano", ou quando a fase de implementação for ativada pelo GOD.
tools: Read, Glob, Grep, Bash, Edit, Write, Agent
---

# Implement — Sub-skill de Implementação

> Executa o plano de implementação da task, criando subagents para tasks complexas ou executando diretamente para tasks simples. Suporta flag `--code-like-me` para implementação cirúrgica.

## Flags

- `--code-like-me` — Ativa a sub-skill `code-like-me` para garantir que o código implementado siga exatamente os padrões e convenções do projeto existente. Quando ativa, cada passo de implementação deve seguir as diretrizes da skill `code-like-me`.

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos **na ordem**:

### 0. Executar hook `before implement`

Ler `GOD/hooks.md` e localizar a seção `# before implement`.

- Se o conteúdo for `skip-hook`: pular e seguir para o passo 1.
- Se houver instruções em linguagem natural: executá-las integralmente antes de prosseguir.

### 1. Identificar a task

- Se o contexto da conversa já contém o código da task, usar esse código
- Caso contrário, perguntar ao usuário o código da task (ex: `PROJ-123`)

### 2. Ler o plano

Ler o arquivo `GOD/tasks/{cod-da-task}/plan.md` para obter o plano de implementação.

- Se o plano estiver vazio, informar o usuário que precisa rodar a skill `plan` antes
- Se o plano existir, analisar sua estrutura e complexidade

### 2.1. Atualizar status para `implementing`

Antes de começar a implementação de fato, atualizar `GOD/tasks/{cod-da-task}/status.md`:

- `phase`: `implementing`
- `updated_at`: timestamp ISO 8601 em UTC
- `updated_by`: `implement`
- `branch`, `learned`, `prs`: preservar valores atuais

### 3. Carregar contexto visual (Figma)

Ler o `GOD/tasks/{cod-da-task}/description.md` e verificar se há links do Figma.

Se houver links do Figma:
- Acessar o Figma via MCP Figma (`get_design_context`) para cada link
- Usar o design como referência visual durante a implementação
- Cada subagent que implementar UI deve receber o contexto do Figma relevante ao seu escopo

### 4. Avaliar complexidade e decidir estratégia

Analisar o plano e decidir a estratégia de execução:

**Task simples (sem divisão de sub-tasks no plano):**
- Executar a implementação diretamente, seguindo os passos do plano na ordem

**Task complexa (com múltiplas sub-tasks no plano):**
- Criar um subagent (via Agent tool) para cada sub-task independente
- Sub-tasks que dependem umas das outras devem ser executadas sequencialmente
- Sub-tasks independentes podem ser executadas em paralelo
- Cada subagent recebe:
  - O contexto completo da task (descrição + plano)
  - Apenas o escopo da sua sub-task específica
  - As convenções do projeto (de `CLAUDE.md`, `ARCHITECTURE.md`, etc.)

### 5. Implementar

**Em ambos os modos (com ou sem `--code-like-me`), validar a cadeia completa sempre que aplicável** — ex: frontend → API → backend → banco. Uma feature não está pronta se só um dos lados foi tocado.

**Sem flag `--code-like-me` (modo livre, seguindo padrões do projeto):**
- Seguir o plano de implementação passo a passo
- Respeitar as convenções do projeto encontradas nos arquivos de configuração (lidos pelo `plan` e refletidos nas considerações técnicas)
- A IA tem liberdade para escolher a abordagem que achar melhor dentro das convenções, sem precisar replicar estilo dev-por-dev
- Validar cadeia completa (front → API → back → banco) onde aplicável

**Com flag `--code-like-me` (modo cirúrgico, imitando os devs do projeto):**
- Aplicar todas as diretrizes da sub-skill `code-like-me` durante a implementação
- Cada mudança deve ser cirúrgica — mínimo impacto, máxima aderência ao código existente
- Encontrar analogias no código existente antes de criar algo novo
- O código produzido deve ser indistinguível do que um dev do projeto escreveria
- Validar cadeia completa (front → API → back → banco) onde aplicável

### 6. Verificação pós-implementação

Após implementar:
- Ler os arquivos alterados para verificar consistência e coerência
- Verificar se todos os passos do plano foram executados

> ℹ️ Esta skill **não roda** type-check, linter, testes ou qualquer outro processo de validação automatizada. Esses processos são configurados pelo usuário nos hooks (`after implement` ou `before pack-up`, conforme preferência) e executados por aqueles hooks.

### 7. Atualizar status para `implemented`

Após concluir a verificação pós-implementação, atualizar `GOD/tasks/{cod-da-task}/status.md`:

- `phase`: `implemented`
- `updated_at`: timestamp ISO 8601 em UTC
- `updated_by`: `implement`
- `branch`, `learned`, `prs`: preservar valores atuais

### 8. Executar hook `after implement`

Ler `GOD/hooks.md` e localizar a seção `# after implement`.

- Se o conteúdo for `skip-hook`: pular e seguir para o passo 9.
- Se houver instruções em linguagem natural: executá-las integralmente antes do relatório final.

### 9. Reportar resultado

Apresentar ao usuário:
- Resumo do que foi implementado
- Arquivos criados ou modificados
- Se usou subagents, listar o que cada um fez
- Pendências ou pontos de atenção (se houver)
- Se hooks before/after foram executados, listar resumidamente o que rodou

---

## Guard-rails

- **Esta skill não escreve em `GOD/knowledge.md`.** Apenas a skill `learn` pode fazê-lo.

---
name: plan
description: |
  Enriquece a descrição da task (Jira, Figma, knowledge, Q&A) e escreve o plano de implementação. Busca dados em sistemas externos e consulta histórico antes de planejar. Use quando o usuário mencionar: "planejar task", "criar plano", "plan", ou quando a fase de planejamento for ativada pelo GDD.
tools: Read, Glob, Grep, Bash, Edit, Write, Agent
---

# Plan — Sub-skill de Planejamento

> Enriquece a descrição da task com dados externos (Jira, Figma), consulta knowledge por tasks semelhantes, faz Q&A com o usuário e então escreve o plano de implementação.

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos **na ordem**:

### 0. Executar hook `before plan`

Ler `GDD/hooks.md` e localizar a seção `# before plan`.

- Se o conteúdo for `skip-hook`: pular e seguir para o passo 1.
- Se houver instruções em linguagem natural: executá-las integralmente antes de prosseguir.

### 1. Identificar a task

- Se o contexto da conversa já contém o código da task, usar esse código
- Caso contrário, perguntar ao usuário o código da task (ex: `PROJ-123`)

### 2. Ler descrição atual

Ler o arquivo `GDD/tasks/{cod-da-task}/description.md` para obter o input bruto salvo pelo `init`.

A descrição pode estar em dois estados:
- **Bruta** (apenas input do usuário, como saída do `init`) — prosseguir com enriquecimento nos passos 3-6
- **Já enriquecida** (de uma execução anterior do `plan`) — pular para o passo 7 e confirmar com o usuário se quer re-enriquecer ou só atualizar o plano

### 3. Buscar dados no Jira (se aplicável)

Se o input bruto contém um link ou código do Jira:

- Acessar o Jira via MCP Atlassian (ex: `getJiraIssue`) e obter:
  - Título da task
  - Descrição completa
  - Links do Figma (nos campos ou na descrição)
  - Qualquer anexo ou contexto relevante
  - Parent task e subtasks, se existirem (contexto mais amplo)

Se o input bruto é apenas texto manual (sem código Jira), pular este passo.

### 4. Consultar knowledge por tasks semelhantes

Ler o arquivo `GDD/knowledge.md`. Verificar se existem tasks anteriores com contexto semelhante à task atual.

Se encontrar tasks semelhantes, guardar:
- **Códigos de commit** (hash1, hash2, ...) — para análise de referência no passo 5
- **Arquivos principais** — para prever impactos
- **Aprendizados** — para incluir no `description.md` como contexto

### 5. Analisar commits de referência

Para cada commit identificado via knowledge (passo 4):
- Executar `git diff {hash}~1..{hash}`
- Analisar o que foi feito nessas tasks anteriores: padrões, arquivos afetados, abordagens utilizadas

### 6. Analisar design do Figma (se aplicável)

Se o Jira trouxe links do Figma, ou se o input bruto já continha links:
- Acessar o Figma via MCP Figma (`get_design_context`) para cada link
- Analisar os elementos visuais, componentes e layout do design
- Cruzar com a descrição da task para entender o escopo visual
- Identificar quais elementos do design precisam ser implementados e quais já existem

Se não houver links do Figma, pular este passo.

### 7. Coletar contexto do projeto

Buscar e ler os seguintes arquivos na raiz do projeto (se existirem):
- `CLAUDE.md` — convenções e instruções do projeto para Claude
- `AGENTS.md` — configurações e instruções de agentes
- `ARCHITECTURE.md` — arquitetura do projeto
- `README.md` — visão geral, setup, comandos e descrição do projeto

Usar essas informações para entender as convenções, padrões, arquitetura e contexto geral do projeto antes de planejar. A busca deve ser case-insensitive (ex: `readme.md`, `Readme.md`, `README.md` são todos válidos).

### 8. Sessão de Q&A com o usuário

Fazer perguntas agrupadas ao usuário para esclarecer a task **e** confirmar detalhes do plano antes de escrever. Cobrir dois aspectos:

**Esclarecimento de escopo (antes do plano):**
- Pontos ambíguos ou faltantes na descrição do Jira ou no input manual
- Se há links do Figma, perguntar se o escopo do design é completo ou parcial
- Comportamento esperado em edge cases
- Impacto em funcionalidades existentes
- Dependências ou pré-requisitos

**Implementação (como fazer):**
- Escolha entre abordagens viáveis quando houver ambiguidade técnica
- Confirmação de padrões detectados no knowledge/contexto do projeto

Diretrizes:
- **Não pergunte demais** — foque apenas no que é ambíguo ou faltante
- **Não pergunte de menos** — garanta que entendeu o escopo, critérios de aceitação e edge cases relevantes
- **Agrupe perguntas** — faça várias de uma vez, não uma por uma
- Se a descrição já está clara e completa após o enriquecimento, informe ao usuário que não há dúvidas e siga adiante

**Registrar todas as perguntas e respostas** — serão incluídas no `description.md` enriquecido (passo 9).

### 9. Atualizar `description.md` com conteúdo enriquecido

Reescrever `GDD/tasks/{cod-da-task}/description.md` com o conteúdo completo:

```markdown
# {cod-da-task} — {título}

## Descrição
{descrição completa do Jira ou do input manual do usuário}

## Links
- Jira: {url do Jira, se houver}
- Figma: {links do Figma, se encontrados}

## Tasks semelhantes no knowledge
{para cada task semelhante encontrada no passo 4, listar código, commits de referência e aprendizados mais relevantes — se não houver, escrever "Nenhuma task semelhante encontrada"}

## Q&A
{sessão completa de perguntas e respostas do passo 8}

---

_Descrição enriquecida por `plan` em {timestamp}._
```

O input bruto original do usuário (conforme salvo pelo `init`) pode ser descartado nessa reescrita — o conteúdo enriquecido já contempla.

### 10. Escrever plano de implementação

Preencher o arquivo `GDD/tasks/{cod-da-task}/plan.md` com o plano de implementação contendo:

- Resumo do que será feito
- Arquivos que serão criados ou modificados
- Passos de implementação ordenados
- Considerações técnicas relevantes (baseadas no contexto coletado: knowledge, Figma, arquivos de convenção do projeto)
- Critérios de aceitação

### 11. Revisão do plano

Após escrever o plano, chamar a sub-skill `review --plan` passando o código da task.

- Se o relatório retornar **Aprovado**: apresentar o plano ao usuário para validação final
- Se o relatório retornar **Ajustes necessários**: avaliar as correções sugeridas, aplicar as pertinentes no `plan.md` e apresentar o plano corrigido ao usuário
- Se o relatório retornar **Reprovado**: reescrever o plano com base no feedback e rodar a review novamente

### 12. Atualizar status

Após a review ser aprovada (e o usuário validar o plano), atualizar `GDD/tasks/{cod-da-task}/status.md`:

- `phase`: `planned`
- `updated_at`: timestamp ISO 8601 em UTC
- `updated_by`: `plan`
- `branch`: preservar o valor atual
- `learned`: preservar o valor atual
- `prs`: preservar o valor atual

### 13. Executar hook `after plan`

Ler `GDD/hooks.md` e localizar a seção `# after plan`.

- Se o conteúdo for `skip-hook`: encerrar.
- Se houver instruções em linguagem natural: executá-las integralmente antes de encerrar.

---

## Guard-rails

- **Esta skill não escreve em `GDD/knowledge.md`.** Apenas a skill `learn` pode fazê-lo. Aqui, o knowledge é apenas **lido** para encontrar tasks semelhantes (passo 4).
- **Esta skill é a dona do enriquecimento da `description.md`.** O `init` cria o arquivo bruto; o `plan` enriquece. Outras skills não devem reescrever a descrição.

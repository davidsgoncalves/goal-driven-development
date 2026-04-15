---
name: plan
description: |
  Analisa a task, coleta contexto do projeto e do código, tira dúvidas com o usuário e escreve o plano de implementação. Use quando o usuário mencionar: "planejar task", "criar plano", "plan", ou quando a fase de planejamento for ativada pelo GDD.
tools: Read, Glob, Grep, Bash, Edit, Write, Agent
---

# Plan — Sub-skill de Planejamento

> Analisa a task, coleta contexto do projeto e do código, tira dúvidas com o usuário e escreve o plano de implementação.

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos **na ordem**:

### 1. Identificar a task

- Se o contexto da conversa já contém o código da task, usar esse código
- Caso contrário, perguntar ao usuário o código da task (ex: `PROJ-123`)

### 2. Ler descrição da task

Ler o arquivo `GDD/tasks/{cod-da-task}/description.md` para obter:
- Título e descrição da task
- Link do Jira (se disponível)
- Link(s) do Figma (se disponíveis)
- Commits de tasks semelhantes (se listados)

### 3. Analisar commits de referência

Se o `description.md` contiver códigos de commit de tasks semelhantes:
- Executar `git diff {hash}~1..{hash}` para cada commit listado
- Analisar o que foi feito nessas tasks anteriores para entender padrões, arquivos afetados e abordagens utilizadas

### 4. Analisar design do Figma

Se o `description.md` contiver links do Figma:
- Acessar o Figma via MCP Figma (`get_design_context`) para cada link
- Analisar os elementos visuais, componentes e layout do design
- Cruzar com a descrição da task e o Q&A para entender o escopo visual
- Identificar quais elementos do design precisam ser implementados e quais já existem

Se não houver links do Figma, pular este passo.

### 5. Coletar contexto do projeto

Buscar e ler os seguintes arquivos na raiz do projeto (se existirem):
- `AGENTS.md` — configurações e instruções de agentes
- `CLAUDE.md` — convenções e instruções do projeto
- `ARCHITECTURE.md` — arquitetura do projeto

Usar essas informações para entender as convenções, padrões e arquitetura do projeto antes de planejar.

### 6. Sessão de perguntas

Iniciar uma sessão de perguntas com o usuário para esclarecer dúvidas sobre a task. Diretrizes:

- **Não pergunte demais** — foque apenas no que é ambíguo ou faltante na descrição
- **Não pergunte de menos** — garanta que entendeu o escopo, critérios de aceitação e edge cases relevantes
- **Agrupe perguntas** — faça várias perguntas de uma vez em vez de uma por uma
- **Se a descrição já está clara e completa**, informe ao usuário que não há dúvidas e siga para o próximo passo

Exemplos de perguntas relevantes:
- Escopo exato da mudança (o que entra e o que não entra)
- Comportamento esperado em edge cases
- Impacto em funcionalidades existentes
- Dependências ou pré-requisitos

### 7. Escrever plano de implementação

Preencher o arquivo `GDD/tasks/{cod-da-task}/plan.md` com o plano de implementação contendo:

- Resumo do que será feito
- Arquivos que serão criados ou modificados
- Passos de implementação ordenados
- Considerações técnicas relevantes (baseadas no contexto coletado dos arquivos do projeto e commits anteriores)
- Critérios de aceitação

### 8. Revisão do plano

Após escrever o plano, chamar a sub-skill `review --plan` passando o código da task.

- Se o relatório retornar **Aprovado**: apresentar o plano ao usuário para validação final
- Se o relatório retornar **Ajustes necessários**: avaliar as correções sugeridas, aplicar as pertinentes no `plan.md` e apresentar o plano corrigido ao usuário
- Se o relatório retornar **Reprovado**: reescrever o plano com base no feedback e rodar a review novamente

### 9. Atualizar status

Após a review ser aprovada (e o usuário validar o plano), atualizar `GDD/tasks/{cod-da-task}/status.md`:

- `phase`: `planned`
- `updated_at`: timestamp ISO 8601 em UTC
- `updated_by`: `plan`
- `branch`: manter o valor atual (não alterar)

---

## Guard-rails

- **Esta skill não escreve em `GDD/knowledge.md`.** Apenas a skill `learn` pode fazê-lo.

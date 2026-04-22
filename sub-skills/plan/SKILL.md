---
name: plan
description: |
  Enriquece a descrição da task (Jira, Figma, knowledge, Q&A), detecta se o ambiente é single-project ou multi-project workspace, resolve a(s) branch(es) da task (nome + base) sem tocar no git, e escreve o plano de implementação com a instrução de branch explícita. Busca dados em sistemas externos e consulta histórico antes de planejar. Não cria branch no git — a criação física é responsabilidade do `implement`. Use quando o usuário mencionar: "planejar task", "criar plano", "plan", ou quando a fase de planejamento for ativada pelo GOD.
tools: Read, Glob, Grep, Bash, Edit, Write, Agent
---

# Plan — Sub-skill de Planejamento

> Enriquece a descrição da task com dados externos (Jira, Figma), consulta knowledge por tasks semelhantes, detecta modo single/multi-project, resolve a(s) branch(es) da task (nome + base por projeto afetado), faz Q&A com o usuário e então escreve o plano de implementação. Não cria branch no git — apenas determina os nomes e bases pra `implement` criar depois.

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos **na ordem**:

### 0. Executar hook `before plan`

Ler `GOD/hooks.md` e localizar a seção `# before plan`.

- Se o conteúdo for `skip-hook`: pular e seguir para o passo 1.
- Se houver instruções em linguagem natural: executá-las integralmente antes de prosseguir.

### 1. Identificar a task

- Se o contexto da conversa já contém o código da task, usar esse código
- Caso contrário, perguntar ao usuário o código da task (ex: `PROJ-123`)

### 2. Ler descrição atual

Ler o arquivo `GOD/tasks/{cod-da-task}/description.md` para obter o input bruto salvo pelo `init`.

A descrição pode estar em dois estados:
- **Bruta** (apenas input do usuário, como saída do `init`) — prosseguir com enriquecimento nos passos 3-6
- **Já enriquecida** (de uma execução anterior do `plan`) — pular para o passo 7 e confirmar com o usuário se quer re-enriquecer ou só atualizar o plano

### 2.1. Detectar modo single-project vs multi-project workspace

Antes de resolver a branch, identificar em qual tipo de ambiente o comando foi chamado:

- Executar `git rev-parse --show-toplevel` no diretório atual (`pwd`).
  - **Se sucede** e retorna um caminho: o diretório atual está dentro de um repositório git — **modo single-project**. A task terá **uma única branch**.
  - **Se falha** (erro "not a git repository"): o diretório atual é um workspace (pasta-mãe contendo múltiplos projetos, cada um com seu próprio `.git`) — **modo multi-project**. A task pode precisar de **uma branch em cada projeto afetado**.

Guardar o modo detectado em memória para os passos seguintes.

### 2.2. Resolver branch(es) da task

Esta skill é a responsável por **determinar** o nome e base da(s) branch(es), mas **não cria no git** — isso fica para o `implement`.

1. **Ler `GOD/patterns.md`** e extrair:
   - **Branch inicial** — uma única entrada (single-project comum) ou lista de entradas `{projeto, branch-base}` (multi-project ou single-project com múltiplos projetos listados)
   - **Padrão de nome de branch** — formato esperado (ex: `task/<cod-da-task>/<descrição-kebab-case>`)

2. **Resolução por modo:**

   **Modo single-project (a task se resolve em UMA branch):**
   - Se o `patterns.md` tem uma única entrada de branch inicial: usar direto como `branch_base`.
   - Se tem múltiplas entradas mas o contexto é single-project (o repo atual é um dos listados): identificar qual aplica usando o diretório raiz do repo (`git rev-parse --show-toplevel`) comparado com os nomes listados. Se ambíguo, perguntar ao usuário e memorizar a escolha apenas para esta execução.
   - Aplicar o padrão de nome pra compor o `branch` (ex: `task/PROJ-123/add-phone-field`). Se o padrão exige um slug e a descrição bruta/enriquecida não sugere um claro, perguntar ao usuário.

   **Modo multi-project (a task pode afetar N projetos):**
   - A identificação de **quais** projetos são afetados depende do escopo da task — provavelmente só fica claro após o passo 10 (plano escrito). Nesta etapa, apenas registrar que o modo é multi-project.
   - A resolução efetiva de nome/base por projeto acontece no **passo 11.5** (depois do plano estar escrito e os projetos afetados identificados).

3. **Idempotência** — se o `status.md` já tem `branch` e `branch_base` populados:
   - Confirmar com o usuário: "branch já resolvida como X (base: Y) — manter?"
   - Se manter, pular a re-resolução. Se trocar, refazer.

Guardar em memória o resultado da resolução (no caso single: `branch` string + `branch_base` string; no caso multi: marcador "multi, pendente de identificar projetos afetados").

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

Ler o arquivo `GOD/knowledge.md`. Verificar se existem tasks anteriores com contexto semelhante à task atual.

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

Reescrever `GOD/tasks/{cod-da-task}/description.md` com o conteúdo completo:

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

Preencher o arquivo `GOD/tasks/{cod-da-task}/plan.md` com o plano de implementação. A primeira seção do plano deve ser sempre **"Branch de trabalho"**. O conteúdo varia por modo:

**Modo single-project:**
```markdown
## Branch de trabalho

- **Base:** `{branch_base resolvido no passo 2.2}`
- **Branch da task:** `{branch resolvido no passo 2.2}`
- **Criação:** o `implement` criará a branch no início da execução partindo da base; esta skill apenas resolveu os nomes.

## Resumo
{...}
```

**Modo multi-project (resolução final acontece no passo 11.5, mas o bloco abaixo é escrito em placeholder aqui e depois atualizado no 11.5):**
```markdown
## Branch de trabalho

- **Modo:** multi-project workspace
- **Projetos afetados:** `{lista de diretórios identificados no plano}` (ex: `projeto-api`, `projeto-web`)
- **Branches a criar** (uma por projeto, nome idêntico):
  - `projeto-api`: base `main` → branch `task/PROJ-123/add-phone-field`
  - `projeto-web`: base `develop` → branch `task/PROJ-123/add-phone-field`
- **Criação:** o `implement` criará todas essas branches no início da execução. Esta skill apenas listou nomes e bases.

## Resumo
{...}
```

Seções restantes do plano (comuns a ambos os modos):
```markdown
## Arquivos afetados
{arquivos que serão criados ou modificados, agrupados por projeto quando multi-project}

## Passos de implementação
{passos ordenados}

## Considerações técnicas
{baseadas no contexto coletado}

## Critérios de aceitação
{critérios}
```

A seção "Branch de trabalho" é **obrigatória** e deve vir no topo. O `implement` lê diretamente do `status.md`, mas o registro explícito no `plan.md` serve como instrução literal pro humano que for ler o plano e deixa a decisão auditável.

### 11. Revisão do plano

Após escrever o plano, chamar a sub-skill `review --plan` passando o código da task.

- Se o relatório retornar **Aprovado**: apresentar o plano ao usuário para validação final
- Se o relatório retornar **Ajustes necessários**: avaliar as correções sugeridas, aplicar as pertinentes no `plan.md` e apresentar o plano corrigido ao usuário
- Se o relatório retornar **Reprovado**: reescrever o plano com base no feedback e rodar a review novamente

### 11.5. Resolução final de branches em modo multi-project

Executar apenas se o modo detectado no passo 2.1 foi **multi-project**.

Neste ponto o plano já está escrito e a lista de **projetos afetados** está explícita nos "Arquivos afetados" / "Passos de implementação".

1. **Identificar projetos afetados** — extrair do plano a lista de diretórios de projeto que serão modificados (ex: `projeto-api`, `projeto-web`). Se houver ambiguidade, perguntar ao usuário antes de prosseguir.
2. **Ler `GOD/patterns.md`** seção "Branch inicial" — obter a branch-base de cada projeto listado.
3. **Para cada projeto afetado**, resolver:
   - `project`: nome do projeto (ex: `projeto-api`)
   - `base`: branch-base desse projeto (do patterns)
   - `name`: aplicar o padrão de nome ao código da task (normalmente o mesmo nome em todos os projetos, ex: `task/PROJ-123/add-phone-field`)
4. **Atualizar o bloco "Branch de trabalho" do `plan.md`** substituindo o placeholder pelos valores finais.

Esta etapa **não toca em git** — apenas registra os nomes planejados. A criação física de cada branch é feita pelo `implement` (ver `implement/SKILL.md` passo 2.05).

### 12. Atualizar status

Após a review ser aprovada (e o usuário validar o plano), atualizar `GOD/tasks/{cod-da-task}/status.md`:

- `phase`: `planned`
- `updated_at`: timestamp ISO 8601 em UTC
- `updated_by`: `plan`
- **Single-project:**
  - `branch`: **nome da branch resolvida no passo 2.2** (string, ex: `task/PROJ-123/add-phone-field`)
  - `branch_base`: **branch base** (string, ex: `main`)
- **Multi-project:**
  - `branch`: **lista de objetos**, um por projeto afetado:
    ```yaml
    branch:
      - project: projeto-api
        name: task/PROJ-123/add-phone-field
        base: main
      - project: projeto-web
        name: task/PROJ-123/add-phone-field
        base: develop
    ```
  - `branch_base`: `null` (redundante — cada entrada do `branch` já carrega sua base)
- `learned`: preservar o valor atual
- `prs`: preservar o valor atual

### 13. Executar hook `after plan`

Ler `GOD/hooks.md` e localizar a seção `# after plan`.

- Se o conteúdo for `skip-hook`: encerrar.
- Se houver instruções em linguagem natural: executá-las integralmente antes de encerrar.

---

## Guard-rails

- **Esta skill não escreve em `GOD/knowledge.md`.** Apenas a skill `learn` pode fazê-lo. Aqui, o knowledge é apenas **lido** para encontrar tasks semelhantes (passo 4).
- **Esta skill é a dona do enriquecimento da `description.md`.** O `init` cria o arquivo bruto; o `plan` enriquece. Outras skills não devem reescrever a descrição.
- **Esta skill é a dona da detecção single/multi-project e da resolução dos nomes/bases de branch.** O `init` deixa `branch: null`; o `plan` determina; o `implement` cria no git.
- **Esta skill não cria branch no git.** Nem em single nem em multi. Só resolve nomes/bases e persiste em `status.md` e `plan.md`. A criação física é responsabilidade exclusiva do `implement`.

---
name: init-tree
description: |
  Inicializa em lote um conjunto de tasks a partir de uma árvore do Jira (tipicamente Epic → Stories → Subtasks). Desce recursivamente a árvore a partir de um nó-raiz passado pelo usuário, cria pastas de contexto para nós internos em `GOD/tasks/` e cria estrutura de execução vazia (`plan.md` + `status.md` com `phase: initialized`) para cada folha. **Não roda spec em batch** — cada folha é especificada depois, individualmente, via `spec {cod}`. Não toca no git. Use quando o usuário mencionar: "init em lote", "init tree", "iniciar Epic", "iniciar várias tasks", "subtasks do Jira", ou passar um link/código de Epic/Story com subtasks.
tools: Read, Glob, Grep, Bash, Edit, Write, Agent
---

# Init-Tree — Sub-skill de Inicialização em Lote via Árvore do Jira (v11)

> Inicializa em lote as tasks de uma árvore do Jira. Recebe um nó-raiz (Epic, Story ou Task com subtasks), desce recursivamente, filtra por status, confirma com o usuário e produz: (a) pastas de contexto pra nós internos em `GOD/tasks/`; (b) estrutura de execução vazia por folha em `GOD/tasks/{cod}/` (`plan.md` + `status.md` com `phase: initialized`). **Não roda spec em batch** — usuário escreve cada spec depois, individualmente, via `spec {cod}`.

> **Mudança v11 (init-tree estrutural):** antes (v9/v10), init-tree delegava ao `spec` em modo batch e gerava spec rascunho por folha. Agora delega ao `init` programaticamente — o que cada folha recebe é só a estrutura de execução vazia (mesma coisa que `init {cod}` produziria). O usuário escreve cada spec individualmente quando estiver pronto. Razão: gerar specs em batch sem Q&A produz lixo que ninguém refina; é melhor não gerar do que gerar mal.

## Banner

Ao iniciar esta skill, **antes de qualquer outra ação**, exiba exatamente este bloco no terminal:

```
  ██████   ██████  ██████  
 ██       ██    ██ ██   ██ 
 ██   ███ ██    ██ ██   ██ 
 ██    ██ ██    ██ ██   ██ 
  ██████   ██████  ██████  
  Goal Oriented Development
```

## Pré-requisitos

- MCP Atlassian disponível e autenticado (`getJiraIssue`, `searchJiraIssuesUsingJql`). Sem isso, a skill encerra com orientação para conectar.
- `GOD/` existe na versão atual (a orquestradora já garante isso antes de delegar).

## Flags

- `--context-only` — apenas cria pastas de contexto pra nós internos; **não** cria estrutura de execução pras folhas. Útil se você só quer mapear a árvore documentalmente sem inicializar tasks.

## Instruções

Quando o usuário invocar esta skill, execute os passos **na ordem**:

### 1. Receber input da raiz

O usuário deve fornecer **uma** das opções:

- **Link do Jira do nó-raiz** — ex: `https://empresa.atlassian.net/browse/PROJ-100`
- **Código do nó-raiz** — ex: `PROJ-100`

Se o usuário não passou nada, perguntar: "Qual o código ou link do nó-raiz da árvore (Epic, Story ou Task com subtasks)?"

Extrair o código (ex: `PROJ-100`) do input.

### 2. Buscar a árvore completa no Jira (recursivo)

Começando pelo nó-raiz, montar a árvore de issues descendo por todos os níveis:

1. `getJiraIssue(PROJ-100)` — obter título, descrição, tipo (Epic/Story/Task/Subtask), status, e lista de **filhos imediatos** (no Jira isso pode aparecer como `subtasks`, `issuelinks` do tipo "is parent of", ou filhos de Epic via JQL `"Epic Link" = PROJ-100`).
2. Para cada filho encontrado, repetir o fetch recursivamente até que um nó não tenha mais filhos (folha).
3. Montar a estrutura em memória:
   ```
   {
     code: "PROJ-100",
     type: "Epic",
     title: "...",
     status: "In Progress",
     children: [
       {
         code: "PROJ-101",
         type: "Story",
         ...
         children: [
           { code: "PROJ-103", type: "Subtask", children: [] },
           ...
         ]
       },
       ...
     ]
   }
   ```

**Observações:**
- O tipo de hierarquia no Jira varia por projeto. Usar relacionamento parent/subtask, não assumir tipos.
- Se fetch falhar pra algum nó (permissão, erro de API), **não abortar**: marcar o nó como "fetch falhou" e seguir.

### 3. Filtrar por status

1. **Ler filtro de status do `patterns.md`** — seção opcional `## Status Jira a ignorar em batch`. Default:
   ```
   Done, Cancelled, Closed, Resolved, Won't Do
   ```

2. **Aplicar o filtro apenas às folhas.** Contextos (nós internos) nunca são filtrados.

3. Marcar cada nó:
   - `will_create: true` se é contexto OU folha que passou no filtro
   - `will_create: false` se é folha com status filtrado

### 4. Detectar duplicatas (idempotência)

Para cada nó com `will_create: true`:
- **Contexto** — checar `GOD/tasks/{cod}/`. Se existe (com `description.md` típico de contexto), marcar `existing: true`.
- **Folha** — checar `GOD/tasks/{cod}/status.md`. Se existe, marcar `existing: true` (a task já foi inicializada — preservar).
- Se a pasta/status.md não existe: marcar `new: true`.

> **Sem flag `--refresh` (v11):** existências são sempre preservadas. Não há reescrita automática de pastas inicializadas — pra reinicializar, o usuário deve apagar a pasta manualmente. Init-tree v11 é puramente aditivo.

### 5. Mostrar preview + confirmação

Apresentar visualização da árvore:

```
🌲 init-tree PROJ-100

Árvore detectada no Jira:
  PROJ-100 "Epic: Redesign onboarding" (Epic)                [context, novo]
    PROJ-101 "Story: Tela de boas-vindas" (Story)            [context, novo]
      PROJ-103 "Implementar header" (Subtask, In Progress)   [exec, novo]
      PROJ-104 "Implementar CTA" (Subtask, Backlog)          [exec, novo]
      PROJ-105 "A/B test botão" (Subtask, Done)              [pulado por filtro]
    PROJ-102 "Story: Fluxo de senha" (Story)                 [context, existente — preservado]
      PROJ-106 "Validação no front" (Subtask, To Do)         [exec, existente — preservado]
      PROJ-107 "Endpoint /reset" (Subtask, Cancelled)        [pulado por filtro]

Resumo:
  - Contextos novos:           3
  - Estruturas de execução:    2 novas (folhas — pasta + plan.md vazio + status.md com phase: initialized)
  - Existentes:                1 contexto + 1 folha (preservados)
  - Pulados:                   2 folhas (filtro de status)

⚠️  Importante (v11):
  - Esta skill NÃO escreve specs. Cada folha vira `GOD/tasks/{cod}/` com `plan.md` vazio + `status.md` (phase: initialized).
  - Você escreve a spec de cada folha individualmente depois, com `spec {cod}` (Q&A interativa).
  - Conforme cada spec é escrita, a phase de cada folha vai pra `specified` e segue o ciclo normal.

Confirmar? (sim / não)
```

- **Sim** → prosseguir.
- **Não** → encerrar sem criar nada.

### 6. Criar estruturas

Percorrer a árvore em **pré-ordem** (pai antes dos filhos).

**Para nó interno (contexto):**

Criar pasta `GOD/tasks/{cod-do-no}/` contendo apenas `description.md` (não tem `plan.md` nem `status.md` — contextos não passam por execução):

```markdown
---
kind: context
jira_type: {Epic|Story|Task}
parent: {cod-do-pai ou null se raiz}
children: [{cod-filho-1}, {cod-filho-2}, ...]
---

# {cod-do-no} — {título do Jira}

## Descrição

{descrição completa do Jira}

## Metadados do Jira

- **Tipo:** {Epic|Story|Task}
- **Status:** {status atual no Jira}
- **Link:** {url do Jira}

## Filhos diretos

{lista dos filhos diretos, com código e título de cada um}

---

> Esta é uma pasta de contexto (não uma task real). Não há `plan.md` nem `status.md` aqui. As tasks reais (folhas) têm estrutura de execução em `GOD/tasks/{cod}/` (criada por esta skill) e sua spec é escrita individualmente via `spec {cod}` quando o usuário estiver pronto.
```

**Para folha (task real):**

Se a flag `--context-only` está ativa, pular a folha (apenas registrar no relatório).

Caso contrário, **delegar à skill `init` programaticamente** passando o código da folha (sem flag de profile — usa default `normal`). Resultado:

- `GOD/tasks/{cod}/plan.md` vazio
- `GOD/tasks/{cod}/status.md` com:
  ```yaml
  phase: initialized
  profile: normal
  spec_path: null
  spec_version_consumed: null
  branch: null
  branch_base: null
  learned: false
  prs: []
  ```

> **Comportamento idempotente:** se `status.md` já existe na folha, init-tree pula essa folha (preserva). Mesmo comportamento pra contextos.

**Falha parcial:** se a criação de algum nó falhar, registrar erro, continuar. Persistir o que foi criado.

### 7. Reportar resultado

```
✅ init-tree PROJ-100 concluído!

Criadas:
  📁 3 pastas de contexto (Epic + 2 Stories)
  📦 2 estruturas de execução (PROJ-103, PROJ-104) em GOD/tasks/

Preservadas (já existiam):
  📁 PROJ-102 (contexto)
  📦 PROJ-106 (estrutura de execução)

Puladas (filtro de status):
  PROJ-105 (Done), PROJ-107 (Cancelled)

Falhas (se houver):
  ⚠️ PROJ-XXX — {motivo}

💡 Próximos passos (v11):
  1. Pra cada folha nova, rode `spec {cod}` quando estiver pronto pra escrever a spec — abre Q&A interativa, classifica perfil, valida com `review --spec` e atualiza o status.md pra phase `specified`. As novas: PROJ-103, PROJ-104.
  2. Quando a spec estiver aprovada (e publicada via `publish-spec` se for crítica), rode `plan {cod}` pra produzir o plano técnico.
  3. Pastas de contexto (PROJ-100, PROJ-101, PROJ-102) ficam só como referência documental — não passam por spec/plan/implement.
  4. Pra adicionar folhas novas que apareceram no Jira depois, basta re-rodar `init-tree PROJ-100` — existentes são preservadas, só novas são criadas.
```

---

## Guard-rails

- **Esta skill não toca no git.** Nem em folhas nem em contextos.
- **Esta skill não escreve em `GOD/knowledge.md`.** Apenas a skill `learn`.
- **Esta skill não chama `spec`/`plan`/`implement` automaticamente.** Downstream é sempre manual, uma folha por vez. O ciclo completo de cada folha (`spec → plan → implement → pack-up`) é feito a posteriori.
- **Esta skill não escreve specs.** A geração em batch foi removida na v11 — produzia rascunho que ninguém refinava. Quem quer spec, roda `spec {cod}` por folha.
- **Esta skill não publica nada.** Sem hook `after spec` (porque spec não roda aqui).
- **Esta skill não apaga pastas existentes.** Existências sempre preservadas — init-tree é puramente aditivo na v11.
- **Esta skill não assume nomes de status Jira.** Usa lista configurável em `patterns.md` ou default documentado.
- **Esta skill não aborta em falha parcial.** Continua criando o que der, reporta no final.

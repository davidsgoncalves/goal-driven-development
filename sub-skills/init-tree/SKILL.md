---
name: init-tree
description: |
  Inicializa em lote um conjunto de tasks a partir de uma árvore do Jira (tipicamente Epic → Stories → Subtasks). Desce recursivamente a árvore a partir de um nó-raiz passado pelo usuário, cria pastas em `GOD/tasks/` para cada nó — folhas (sem filhos no Jira) viram tasks reais; nós internos (pai e intermediários) viram pastas de contexto com frontmatter `kind: context`. Não toca no git. Use quando o usuário mencionar: "init em lote", "init tree", "iniciar Epic", "iniciar várias tasks", "subtasks do Jira", "criar tasks da árvore", ou passar um link/código de Epic/Story com subtasks.
tools: Read, Glob, Grep, Bash, Edit, Write, Agent
---

# Init-Tree — Sub-skill de Inicialização em Lote via Árvore do Jira

> Inicializa em lote as tasks de uma árvore do Jira. Recebe um nó-raiz (Epic, Story ou Task com subtasks), desce recursivamente por todos os níveis, filtra por status, confirma com o usuário e cria pastas em `GOD/tasks/`. Folhas viram tasks reais (delegadas ao `init`); nós internos viram pastas de contexto documental.

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

- `--refresh` — re-lê o Jira e atualiza o `description.md` de todas as pastas já existentes (contextos e folhas) com os dados mais recentes. Sem essa flag, pastas existentes são preservadas intactas.

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
- O tipo de hierarquia no Jira varia por projeto (Epic → Story → Subtask; Task → Subtask; etc.). Usar o relacionamento parent/subtask do Jira, não assumir tipos.
- Se o fetch de algum nó falhar (permissão, erro de API), **não abortar** o fluxo inteiro: marcar o nó como "fetch falhou" e seguir. No passo de relatório, listar os nós com falha para o usuário resolver manualmente.

### 3. Filtrar por status

1. **Ler filtro de status do `patterns.md`** — seção opcional `## Status Jira a ignorar em batch`. Se a seção não existir, usar o default:
   ```
   Done, Cancelled, Closed, Resolved, Won't Do
   ```

2. **Aplicar o filtro apenas às folhas** (nós sem filhos). Contextos (nós internos) nunca são filtrados — se o usuário quer trabalhar em alguma folha do subtree, o contexto pai precisa existir.

3. Marcar cada nó da árvore com:
   - `will_create: true` se é contexto OU se é folha que passou no filtro
   - `will_create: false` se é folha com status filtrado

### 4. Detectar duplicatas (idempotência)

Para cada nó com `will_create: true`:
- Se `GOD/tasks/{cod-do-no}/` já existe: marcar como `existing: true` e **não tocar** (a menos que a flag `--refresh` esteja ativa, nesse caso marcar como `will_refresh: true`).
- Se a pasta não existe: marcar como `new: true`.

### 5. Mostrar preview + confirmação

Apresentar ao usuário uma visualização da árvore indicando o que vai acontecer:

```
🌲 init-tree PROJ-100

Árvore detectada no Jira:
  PROJ-100 "Epic: Redesign onboarding" (Epic)                [context, novo]
    PROJ-101 "Story: Tela de boas-vindas" (Story)            [context, novo]
      PROJ-103 "Implementar header" (Subtask, In Progress)   [task, novo]
      PROJ-104 "Implementar CTA" (Subtask, Backlog)          [task, novo]
      PROJ-105 "A/B test botão" (Subtask, Done)              [task, pulado por filtro]
    PROJ-102 "Story: Fluxo de senha" (Story)                 [context, existente — preservado]
      PROJ-106 "Validação no front" (Subtask, To Do)         [task, existente — preservado]
      PROJ-107 "Endpoint /reset" (Subtask, Cancelled)        [task, pulado por filtro]

Resumo:
  - Criações novas:   3 contextos + 2 tasks reais
  - Existentes:       1 contexto + 1 task (preservados)
  - Pulados (filtro): 2 folhas

Confirmar? (sim / não)
```

- **Sim** → prosseguir para o passo 6.
- **Não** → encerrar sem criar nada.

Se o usuário quiser ajustar o filtro, orientar: "edite `GOD/patterns.md` seção `Status Jira a ignorar em batch` e rode `init-tree` de novo". Se quiser excluir um nó específico, orientar: "rode `init-tree`, aguarde a criação, e apague manualmente a pasta que não quer".

### 6. Criar estruturas — contextos e tasks

Percorrer a árvore em **pré-ordem** (pai antes dos filhos) para garantir que cada filho saiba o código do pai imediato.

Para cada nó com `will_create: true` e `new: true`:

**Se é contexto (nó interno, com filhos):**

Criar pasta `GOD/tasks/{cod-do-no}/` contendo **apenas** `description.md` (não cria `plan.md` nem `status.md` — contextos não passam por plan/implement):

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

{lista dos filhos diretos, com código e título de cada um — útil pra humano navegar a árvore}

---

> Esta é uma pasta de contexto (não uma task real). Não há `plan.md` nem `status.md` aqui. As tasks reais (folhas) estão em pastas irmãs dentro de `GOD/tasks/`.
```

**Se é folha (task real):**

Delegar à skill `init` passando:
- **código da task** = código do Jira da folha
- **input bruto** = link do Jira (`https://.../browse/{cod}`) para que o `plan` futuramente fetche os detalhes
- **parent** = código do pai imediato (será gravado no frontmatter de `description.md`)

A skill `init` cria `description.md` (com `kind: task`, `parent: {pai}`), `plan.md` vazio e `status.md` com `phase: initialized`, `branch: null`, `branch_base: null`.

Para cada nó com `will_refresh: true` (flag `--refresh` ativa):
- **Contextos:** reescrever `description.md` com os dados atualizados do Jira (preservar ordem dos campos; `children` reflete a árvore atual — pode ter ganho ou perdido filhos).
- **Folhas (tasks reais):** reescrever apenas o bloco "Descrição" do `description.md` com o texto atualizado do Jira, **preservando** qualquer enriquecimento já feito por `plan` (Q&A, links de Figma, tasks semelhantes). Se a descrição já foi enriquecida, anexar um bloco no final: `> Atualizado do Jira em {timestamp} por init-tree --refresh`.

**Falha parcial:** se a criação de um nó falhar (erro de filesystem, permissão, etc.), registrar o erro, continuar com os próximos nós. Persistir o que foi criado.

### 7. Reportar resultado

```
✅ init-tree PROJ-100 concluído!

Criadas:
  📁 3 pastas de contexto (Epic + 2 Stories)
  📄 2 tasks reais (PROJ-103, PROJ-104)

Preservadas (já existiam):
  📁 PROJ-102 (contexto)
  📄 PROJ-106 (task — fase atual: planned)

Puladas (filtro de status):
  PROJ-105 (Done), PROJ-107 (Cancelled)

Falhas (se houver):
  ⚠️ PROJ-XXX — {motivo}

💡 Próximos passos:
  - Rode `plan PROJ-103` para planejar a primeira task
  - Rode `plan PROJ-104` quando for pegar a segunda
  - Pastas de contexto (PROJ-100, PROJ-101, PROJ-102) não têm `plan`/`implement` — são apenas referência documental
  - Se quiser atualizar descrições a partir do Jira, rode `init-tree PROJ-100 --refresh`
```

---

## Guard-rails

- **Esta skill não toca no git.** Nem em folhas nem em contextos. Git é responsabilidade exclusiva do `implement` (cria branch da folha) — contextos nunca têm branch.
- **Esta skill não escreve em `GOD/knowledge.md`.** Apenas a skill `learn`.
- **Esta skill não chama `plan` nem `implement` automaticamente.** Downstream é sempre manual, uma folha por vez.
- **Esta skill não apaga pastas existentes.** Sem `--refresh`, existentes são preservadas intactas. Com `--refresh`, descrições são atualizadas mas `plan.md`/`status.md` das folhas existentes nunca são tocados.
- **Esta skill não assume nomes de status Jira.** Usa a lista configurável em `patterns.md` (seção `## Status Jira a ignorar em batch`) ou o default documentado.
- **Esta skill não aborta em falha parcial.** Continua criando o que der, reporta o que falhou no final.

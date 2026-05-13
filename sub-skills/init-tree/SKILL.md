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
- `--stack` *(v12)* — após criar estruturas, lê `issuelinks` (`is blocked by`) das folhas, monta DAG, topo-sorta e grava `stack_parent` + `stack_order` no `status.md` de cada folha. Skills downstream (`plan`, `implement`, `ready`) usam esses campos pra: (a) basear branch da folha N na branch da N-1 em vez de `main`; (b) fazer cascata de rebase quando a parent muda; (c) recomendar `ready` em ordem conforme cada PR mergeia. Se nenhuma folha tem `is blocked by` apontando pra outra folha no escopo, `--stack` vira no-op e emite aviso ("nenhuma dependência detectada — árvore é independente").
- `--auto` *(v12)* — encadeia o ciclo completo em todas as folhas após o init-tree: invoca a skill `worktree` (com symlink de `node_modules`), depois `spec-tree` (Q&A unificada em batch pra todas as folhas), depois loop `plan → implement → pack-up` por folha. Em falha irresolúvel para e chama humano. Composável com `--stack` — quando ambos estão presentes, o loop respeita a ordem do stack e a cascata de rebase. Ver sub-skill `spec-tree` e seção "Modo auto" abaixo.

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

### 6.5. Aplicar stack (se `--stack` presente)

Pra cada folha criada/preservada com `will_create: true` e estrutura de execução já gerada:

1. **Coletar `is blocked by`** — pra cada folha, ler `issuelinks` do payload do Jira (já obtido no passo 2). Filtrar por tipo `Blocks` na direção "is blocked by" (a task em questão é bloqueada **por** outra). Pode ser inferido pelo MCP via `inwardIssue.key`. Só considerar links cujo target está no escopo (também é uma folha desta árvore) — fora-do-escopo gera warning mas não bloqueia.

2. **Montar payload pro helper:**
   ```json
   {"tasks": {"{cod}": {"blocked_by": ["{cod}", ...]}, ...}}
   ```

3. **Rodar topo-sort** via `python3 sub-skills/_lib/parse_jira_deps.py < payload.json`:
   - Exit 0 → ler `order`, `stack`, `warnings` do stdout JSON.
   - Exit 2 (ciclo) → **abortar `--stack`**, registrar erro com lista de nós em ciclo, encerrar init-tree com aviso ("DAG do Jira tem ciclo — corrija os links `is blocked by` no Jira e re-rode"). Estruturas criadas continuam, mas sem stack metadata.
   - Exit 1 (input malformado) → fallback LLM: a própria orquestradora faz topo-sort manual (descrito em comentário no script). Para árvores até ~20 folhas, é viável inline.
   - Python ausente → fallback LLM idem.

4. **Gravar `stack_parent`/`stack_order` em cada status.md:**
   Pra cada `{cod}` em `stack`:
   ```yaml
   stack_parent: {cod-do-parent ou null}
   stack_order: {N inteiro}
   stack_depth: {N inteiro}
   ```
   Delegar pra `python3 sub-skills/_lib/update_status.py` se disponível.

5. **Caso "sem dependências":** se `order` tem só folhas com `stack_parent: null` (DAG plano), emitir aviso "nenhuma dependência detectada entre as folhas — `--stack` foi no-op" e prosseguir sem stack metadata. (Persistir `stack_parent: null` ainda é OK — registra que a varredura rodou.)

6. **Warnings do helper** (lineages divergentes) → relatar no passo 7 sob "Atenções".

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

## Modo auto (v12) — `init-tree --auto`

Quando `--auto` está presente, após terminar os passos 1–7 (criação de estruturas + opcional stack), o init-tree encadeia automaticamente:

### A. Worktree

Invocar a skill global `worktree` programaticamente — cria `.worktrees/<branch-leaf>` e copia os arquivos de env ignorados (`.env*`, `.envrc`, etc.). Depois, criar **symlink** de `node_modules` (e `vendor/` em projetos PHP, se aplicável) do repo principal pro worktree pra evitar reinstall.

> Nome do worktree: usa o **código da raiz** da árvore (ex: `PROJ-100`). Cada folha será uma branch dentro desse worktree, não worktrees separados.

### B. Spec-tree (Q&A unificada upfront)

Delegar pra sub-skill **`spec-tree`** passando a lista de folhas criadas. Spec-tree:

1. Lê todas as descrições de folha.
2. Agrupa perguntas por tema (auth, payments, UI, infra...) usando a heurística do `spec` v10.1.
3. Faz **uma única sessão de Q&A** com o usuário cobrindo tudo.
4. Gera cada spec individual aplicando o que coletou.
5. Roda `review --spec` em batch (subagent isolado por spec).
6. Atualiza cada `status.md` pra `phase: specified`.

**Falha aqui = parada total.** Se o usuário abandona o Q&A, ou alguma spec é reprovada pelo review e não tem como corrigir automaticamente, init-tree --auto encerra com mensagem orientando rodar `spec {cod}` manual pras folhas pendentes.

### C. Loop plan → implement → pack-up

Pra cada folha em ordem (de `stack` se `--stack` também presente; ou ordem natural da árvore caso contrário):

1. **plan** → escreve `plan.md`, resolve branch + base.
   - Se `stack_parent` populado, `branch_base` = branch do parent (não `main`).
2. **implement** → cria branch, executa plano.
   - Se `stack_parent` populado, fazer rebase contra estado atual do parent antes de codar.
   - Conflito de rebase irresolúvel → **parar e chamar humano**.
3. **pack-up** → commit + push + cria **PR em draft contra `main`**.

Após pack-up de cada folha, **não** invoca `ready` automaticamente — `ready` é sempre humano.

### D. Critérios pra chamar humano

A IA decide quando interromper baseada no objetivo (entregar todas as tasks corretamente). Casos típicos:

- Q&A obrigatório aparece no meio do implement (não foi resolvido pelo spec-tree)
- Conflito de rebase irresolúvel em cascata de stack
- Build/test falhando após 2 tentativas de correção
- MCP/ferramenta externa indisponível (Jira, gh) após retry
- Plano detecta incompatibilidade com a spec (drift inesperado)

Sempre: registrar contexto detalhado e qual task parou. Usuário retoma com `resume {cod}` ou ajustando manualmente.

### E. Relatório final

```
✅ init-tree --auto PROJ-100 concluído!

Worktree: .worktrees/PROJ-100 (symlinks: node_modules)
Specs geradas: 4 (PROJ-101, PROJ-102, PROJ-103, PROJ-104)
PRs criados em draft: 4
  PROJ-101 → PR #234 (base: main)
  PROJ-102 → PR #235 (base: PROJ-101-branch via stack)
  PROJ-103 → PR #236 (base: PROJ-101-branch via stack)
  PROJ-104 → PR #237 (base: PROJ-103-branch via stack)

💡 Próximos passos:
  • Revise os PRs em draft
  • Conforme cada PR mergeia em main, rode `ready` pra liberar os dependentes
```

---

## Guard-rails

- **Esta skill não toca no git no modo padrão.** Sem `--auto`, nunca cria branch nem worktree. Em `--auto`, a skill `worktree` chamada programaticamente é quem mexe — init-tree continua sem chamar git diretamente.
- **Esta skill não escreve em `GOD/knowledge.md`.** Apenas a skill `learn`.
- **Esta skill não chama `spec`/`plan`/`implement` automaticamente no modo padrão.** Downstream é manual, uma folha por vez. No modo `--auto` (v12), encadeia explicitamente — mas é opt-in claro via flag, não comportamento implícito.
- **Esta skill não escreve specs.** A geração em batch foi removida na v11 — produzia rascunho que ninguém refinava. Quem quer spec, roda `spec {cod}` por folha.
- **Esta skill não publica nada.** Sem hook `after spec` (porque spec não roda aqui).
- **Esta skill não apaga pastas existentes.** Existências sempre preservadas — init-tree é puramente aditivo na v11.
- **Esta skill não assume nomes de status Jira.** Usa lista configurável em `patterns.md` ou default documentado.
- **Esta skill não aborta em falha parcial.** Continua criando o que der, reporta no final.

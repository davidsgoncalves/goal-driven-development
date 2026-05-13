---
name: init
description: |
  Entry point estrutural do fluxo single-task na v11. Cria a pasta `GOD/tasks/{cod}/` com `plan.md` vazio e `status.md` (`phase: initialized`). Não exige spec, não toca em git, não busca dados externos. Aceita `--profile=trivial|normal|critical` (default `normal`) só pra carimbar label informativa. Use quando o usuário mencionar: "iniciar task", "init", "criar estrutura da task", ou quando começar uma task nova no fluxo single-task.
tools: Read, Glob, Grep, Bash, Edit, Write
---

# Init — Entry point estrutural (v11)

> Cria a estrutura de execução de uma task em `GOD/tasks/{cod}/`. Roda **antes** de `spec` no fluxo v11 — vira o ponto zero do single-task. Não cria branch no git (continua sendo responsabilidade do `implement`), não busca dados externos (continua sendo `spec`).

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

## Posição no fluxo (v11)

```
init → spec → [publish-spec] → plan → implement → pack-up
^^^^
você está aqui
```

> **Mudança v11 (init estrutural):** init agora roda **antes** de `spec`. A spec ainda não existe quando esta skill é invocada. Init vira puramente estrutural — cria a pasta da task vazia. A spec é escrita pelo `spec` depois, que também atualiza o `status.md` criado aqui (phase `initialized → specified`).
>
> **Diferença pra v9/v10:** antes, init exigia spec existir e flag `--type=trivial` era escape hatch pra mudanças cosméticas. Agora init nunca exige spec e o flag morreu — `--profile=trivial` é só uma label no status.md, sem mudar comportamento da skill.

## Flags

- `--profile=trivial|normal|critical` — registra o perfil da task no `status.md`. Default `normal`. Não muda o comportamento desta skill, só carimba label que skills downstream consultam (ex: `pack-up` em task `critical` pode exigir aprovação extra; task `trivial` orienta o usuário a pular spec/plan).
- `--stack` *(v12)* — detecta se esta task tem `is blocked by` apontando pra outra task que **já tem pasta em `GOD/tasks/`** e está com `phase ≥ planned` (já tem branch). Se sim, grava `stack_parent` no `status.md` — o `plan` vai usar a branch desse parent como `branch_base` em vez de `main`, e `implement` vai fazer cascata de rebase. Se nenhum blocker em escopo, vira no-op e emite aviso. Exige MCP Atlassian autenticado pra ler `issuelinks`.
- `--auto` *(v12)* — encadeia o ciclo completo após init: `spec → plan → implement → pack-up` sem gates. Antes de começar, invoca a skill `worktree` (com symlink de `node_modules`). Em falha irresolúvel para e chama humano. Composável com `--stack`. Ver seção "Modo auto" abaixo.
- `--debug` *(v10.6)* — registra passos em `debug.log` via `_lib/debug_log.py`. Pontos: identificar task (1), criar estrutura (3), hooks (0/4). Ver SKILL raiz.

## Invocação programática

Esta skill pode ser invocada:

- **Interativamente pelo usuário** (fluxo padrão) — entry point single-task.
- **Programaticamente por `spec`** — auto-init silencioso quando o usuário invoca `spec` sem ter rodado `init` antes.
- **Programaticamente por `init-tree`** — para cada folha da árvore Jira que ela está processando.

## Otimização v10.2

Quando `python3 ≥ 3.8` está disponível, esta skill delega criação inicial de `status.md` pra `sub-skills/_lib/update_status.py` (mais rápido que LLM gerar YAML manualmente). Falha cai pro Write tradicional. Ver "Delegação pra `_lib/`" no SKILL.md raiz.

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos **na ordem**:

### 0. Executar hook `before init`

Ler `GOD/hooks.md` e localizar a seção `# before init`.

- Se o conteúdo for `skip-hook`: pular e seguir para o passo 1.
- Se houver instruções em linguagem natural: executá-las integralmente antes de prosseguir. Se as instruções falharem ou pedirem confirmação, pausar e consultar o usuário.

### 1. Identificar a task

Receber **uma** das opções:

- **Código da task** — ex: `PROJ-123` (caso normal — Jira).
- **Link do Jira** — extrair código da URL.
- **Texto livre** — pedir um identificador curto (ex: `fix-button-copy`, `feat-onboarding`).

Se nada foi passado, perguntar: "Qual o código ou identificador da task?"

Esta skill **não busca dados em sistemas externos** — não chama Jira, Figma, etc. Esse fetch é responsabilidade de `spec`.

### 2. Resolver `specs_path` (apenas pra registro, não pra checagem)

Ler `GOD/config.md` e extrair `specs_path`. Se ausente, usar default `docs/specs/`.

> **Mudança v11:** init **não verifica** se `<specs_path>/tasks/{cod}.md` existe. A spec ainda nem foi escrita quando init roda. O caminho será populado em `status.md` mais tarde, pelo próprio `spec` quando rodar.

### 3. Criar estrutura da task

Criar a seguinte estrutura em `GOD/tasks/`:

```
GOD/tasks/{cod-da-task}/
├── plan.md
└── status.md
```

> **Mudança v11:** `description.md` **não é mais criado**. O input bruto vai direto pra seção `## Input bruto` da spec quando o usuário rodar `spec`.

**`plan.md`** — criar vazio, será preenchido pela skill `plan`.

**`status.md`** — criar com YAML frontmatter (mesmo conteúdo independente do profile):

```yaml
---
phase: initialized
profile: {trivial|normal|critical}  # default 'normal' se flag ausente
updated_at: {timestamp-iso-8601-utc}
updated_by: init
spec_path: null
spec_version_consumed: null
branch: null
branch_base: null
learned: false
prs: []
---
```

**Notas dos campos:**
- `phase: initialized` — pasta criada, spec ainda não escrita. Próxima transição é pra `specified` (após `spec`) ou `planned` (após `plan` em modo trivial sem spec).
- `profile`: registrado pra dashboards e roteamento. **Não muda** comportamento de init — é só label informativa.
- `spec_path`, `spec_version_consumed`: `null` — `spec` resolve quando rodar. Em fluxo trivial sem spec, ficam `null` permanentemente.
- `branch`, `branch_base`: `null` — `plan` resolve, `implement` cria fisicamente.

**Campos opcionais v12** (adicionados sob demanda, não fazem parte do template default):
- `stack_parent`: cod da task da qual esta depende (gravado por `--stack` ou `init-tree --stack`). Ausente em tasks independentes.
- `stack_order`, `stack_depth`: índice e profundidade no DAG (gravados por `init-tree --stack`).
- `ready`, `ready_at`, `ready_reviewers`: marcadores de que `ready` já foi rodado (gravados pela sub-skill `ready`).

### 3.3. Aplicar stack (se `--stack` presente)

Apenas quando flag `--stack` está ativa:

1. **Buscar issuelinks no Jira:** chamar MCP `getJiraIssue({cod})` e extrair links do tipo "is blocked by" (inward `Blocks`). Lista de códigos de blockers.
   - Sem MCP Atlassian → registrar warning, pular stack, prosseguir.
   - Task não-Jira (ID livre tipo `fix-button-copy`) → pular stack silenciosamente, sem warning.

2. **Filtrar blockers em escopo:** pra cada blocker, verificar se `GOD/tasks/{blocker}/status.md` existe E `phase ∈ {planned, implementing, implemented, packed-up}` (tem branch já criada).
   - Zero blockers em escopo → no-op, emitir aviso ("nenhum blocker em andamento no GOD — `--stack` não tem onde basear").
   - 1 blocker em escopo → ele vira `stack_parent`.
   - N > 1 em escopo → perguntar ao usuário qual usar como base, ou aceitar default "o mais profundo" (maior `stack_depth` no status.md; em empate, o mais recente por `updated_at`).

3. **Gravar no `status.md`:**
   ```yaml
   stack_parent: {cod-do-blocker-escolhido}
   stack_depth: {stack_depth do parent + 1}
   ```
   - `stack_order` não é gravado em single-task init — só faz sentido em init-tree onde existe ordem global.

### 3.5. Retrocompat com tasks legacy v8

Se a pasta `GOD/tasks/{cod}/` já existe com `description.md` (legacy v8), preservar — não tocar no arquivo. Apenas adicionar `plan.md` (se ausente) e `status.md` (se ausente).

Se for task nova v11, **não criar `description.md`**.

### 4. Executar hook `after init`

Ler `GOD/hooks.md` e localizar a seção `# after init`.

- Se o conteúdo for `skip-hook`: pular e seguir para o passo 5.
- Se houver instruções em linguagem natural: executá-las integralmente antes do relatório final.

### 5. Reportar resultado

**Para perfil `normal` ou `critical` (caso padrão):**

> ✅ Task `{cod-da-task}` inicializada (perfil: {perfil})!
>
> 📋 `GOD/tasks/{cod-da-task}/plan.md` — vazio (será preenchido por `plan`)
> 📍 `GOD/tasks/{cod-da-task}/status.md` — fase: `initialized`, branch: `null`
>
> 💡 Próximo passo: rode `spec {cod}` — busca Jira/Figma se aplicável, faz Q&A focada em escopo, escreve REQs/ACs/cenários e atualiza esse status.md pra fase `specified`.

**Para perfil `trivial`:**

> ✅ Task `{cod-da-task}` inicializada (perfil: trivial)!
>
> 📋 `GOD/tasks/{cod-da-task}/plan.md` — vazio (modo trivial não exige plano)
> 📍 `GOD/tasks/{cod-da-task}/status.md` — fase: `initialized`, branch: `null`
>
> 💡 Próximo passo (trivial): você pode pular `spec` e `plan` e rodar `implement {cod}` direto — mude o que precisar e siga pro `pack-up`. Use trivial só pra mudanças cosméticas (typo, copy, dep upgrade).

Se a skill foi invocada programaticamente (por `spec` no auto-init ou por `init-tree`), o relatório final é consolidado pela skill chamadora; aqui basta retornar controle silenciosamente após a criação bem-sucedida.

---

## Modo auto (v12) — `init --auto`

Quando `--auto` está presente, após terminar os passos 0–5, init encadeia automaticamente o ciclo completo da task em sequência, sem gates de aprovação:

### A. Worktree

Invocar a skill global `worktree` programaticamente — cria `.worktrees/{cod}` e copia `.env*`/`.envrc`. Em seguida, criar **symlink** de `node_modules` (e `vendor/` em projetos PHP) do repo principal pro worktree.

> Se a skill `worktree` não estiver disponível, init --auto continua direto no repo principal e emite aviso. Não é fatal — a maior parte do trade-off do worktree é poder paralelizar, e em single-task não há paralelismo.

### B. Ciclo encadeado

```
spec → plan → implement → pack-up
```

Sem pausas entre etapas, sem confirmação humana. Cada skill é invocada programaticamente com o `{cod}` da task.

**Q&A em spec:** mesmo em `--auto`, se a spec não tem informação suficiente, `spec` faz Q&A — a IA responde com base em descrição/contexto quando possível, e chama o humano quando inevitável (campo obrigatório sem fonte). Não há "responder default" silencioso pra preservar qualidade.

### C. Cascata de rebase (se `--stack` co-aplicado)

Se `stack_parent` foi populado no passo 3.3:
- `plan` resolve `branch_base` = branch do parent.
- `implement` faz rebase contra estado atual do parent antes de codar. Conflito irresolúvel → parar e chamar humano.

### D. Critérios pra chamar humano

A IA decide com base no objetivo (entregar a task corretamente). Casos comuns: Q&A obrigatório sem fonte automática, conflito de rebase, build/test falhando após 2 tentativas, ferramenta externa indisponível após retry. Sempre: registrar contexto detalhado em `changelog.md`, marcar `paused: true`, sair. Usuário retoma com `resume {cod}`.

### E. Relatório final

```
✅ init --auto {cod} concluído!

Worktree: .worktrees/{cod} (symlinks: node_modules)
Spec: <specs_path>/tasks/{cod}.md
Branch: {branch} (base: {base})
PR: {url} (draft)

💡 Próximos passos:
  • Revise o PR em draft
  • Quando estiver pronto, rode `ready {cod}` pra liberar pra review humano
```

---

## Guard-rails

- **Esta skill não toca no git no modo padrão.** Não faz checkout, não cria branch, não valida estado. Resolução do nome da branch é responsabilidade do `plan`; criação física é do `implement`. No modo `--auto`, a skill `worktree` chamada programaticamente é quem mexe — init continua sem chamar git diretamente.
- **Esta skill não escreve em `GOD/knowledge.md`.** Apenas a skill `learn` pode fazê-lo.
- **Esta skill não busca dados em sistemas externos** (Jira, Figma). Esse fetch é do `spec`.
- **Esta skill não faz Q&A com o usuário sobre escopo.** Q&A acontece no `spec`.
- **Esta skill não exige spec existir.** Pelo contrário — init roda antes de spec na v11.
- **Esta skill não escreve nem cria spec.** Apenas registra placeholders (`spec_path: null`).
- **Esta skill não cria `description.md` em tasks novas.** Em tasks legacy v8 que já tinham, preserva.
- **`profile` não muda comportamento desta skill.** É label pura — skills downstream (pack-up, implement, dashboards) é que consomem.

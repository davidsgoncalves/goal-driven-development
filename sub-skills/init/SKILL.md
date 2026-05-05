---
name: init
description: |
  Cria a estrutura de execução de uma task **depois** que a spec já existe (v9 spec-first). Lê a spec canônica em `<specs_path>/tasks/{cod}.md`, cria a pasta `GOD/tasks/{cod}/` com `plan.md` vazio e `status.md` apontando pra spec (phase `specified`). Não toca no git, não busca dados em sistemas externos. Aceita `--type=trivial` que dispensa spec pra mudanças cosméticas. Use quando o usuário mencionar: "iniciar task", "init", "criar estrutura da task", ou quando a fase de inicialização for ativada pelo GOD após a spec.
tools: Read, Glob, Grep, Bash, Edit, Write
---

# Init — Sub-skill de Inicialização de Task (pós-spec na v9)

> Cria a estrutura de execução de uma task em `GOD/tasks/{cod}/` apontando pra spec já produzida em `<specs_path>/tasks/{cod}.md`. Roda **depois** de `spec` no fluxo v9 (spec-first). Aceita `--type=trivial` que pula spec inteira pra mudanças cosméticas. Não cria branch no git — isso continua sendo responsabilidade do `implement`.

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

## Posição no fluxo (v9)

```
spec → [publish-spec] → init → plan → implement → pack-up
                       ^^^^
                       você está aqui
```

> **Mudança v9 (spec-first):** init agora roda **depois** de `spec`. A spec da task já existe em `<specs_path>/tasks/{cod}.md` quando esta skill é invocada (exceto em `--type=trivial`). Init não captura mais input bruto — isso virou responsabilidade do `spec`.

## Flags

- `--type=trivial` — atalho pra mudanças cosméticas (copy, typo, dep upgrade) que não justificam spec. Cria estrutura mínima sem exigir spec prévia. **Spec não é gerada nesse modo.** Plano e implementação seguem fluxo normal a partir da estrutura criada.
- `--type=normal|critical` — apenas registra o perfil em `status.md`. Spec deve ter sido produzida pela skill `spec` antes desta invocação. Útil pra coerência de status (ex: dashboards filtrarem por perfil).
- `--debug` *(v10.6)* — registra passos em `debug.log` via `_lib/debug_log.py`. Pontos: identificar task (1), criar estrutura (3), hooks (0/4). Ver SKILL raiz.

## Invocação programática

Esta skill pode ser invocada:

- **Interativamente pelo usuário** (fluxo padrão) — após o `spec` rodar.
- **Programaticamente pela skill `init-tree`** — para cada folha da árvore Jira que ela está processando, depois que `init-tree` produziu specs em batch.

## Otimização v10.2

Quando `python3 ≥ 3.8` está disponível, esta skill delega criação inicial de `status.md` pra `sub-skills/_lib/update_status.py` (mais rápido que LLM gerar YAML manualmente). Falha cai pro Write tradicional. Ver "Delegação pra `_lib/`" no SKILL.md raiz.

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos **na ordem**:

### 0. Executar hook `before init`

Ler `GOD/hooks.md` e localizar a seção `# before init`.

- Se o conteúdo for `skip-hook`: pular e seguir para o passo 1.
- Se houver instruções em linguagem natural: executá-las integralmente antes de prosseguir. Se as instruções falharem ou pedirem confirmação, pausar e consultar o usuário.

### 1. Identificar a task e perfil

Receber **uma** das opções:

- **Código da task** — ex: `PROJ-123` (caso normal — spec já existe).
- **Link do Jira** — extrair código da URL.
- **Texto livre** (apenas em `--type=trivial`) — pedir um identificador curto (ex: `fix-button-copy`).

Determinar o perfil:

- Se a flag `--type=` foi passada: usar direto.
- Se não foi passada e a spec existe em `<specs_path>/tasks/{cod}.md`: ler o frontmatter `profile` da spec — esse é o perfil oficial da task.
- Se não foi passada e a spec não existe: orientar o usuário:

  > ⚠️ Não encontrei spec em `<specs_path>/tasks/{cod}.md`.
  >
  > - Se essa task é uma feature/bug com escopo: rode `spec {cod}` antes de `init`.
  > - Se é uma mudança trivial (copy, typo, dep upgrade): rode `init {cod} --type=trivial`.

  Encerrar.

### 2. Resolver `specs_path` (apenas se não-trivial)

Se o perfil é `normal` ou `critical`, ler `GOD/config.md` e extrair `specs_path`. Se ausente, usar default `docs/specs/`.

Resolver path absoluto. Verificar que `<specs_path>/tasks/{cod}.md` existe — se não existir, abortar com a mesma mensagem do passo 1.

Em modo `--type=trivial`, pular este passo (sem spec envolvida).

### 3. Criar estrutura da task

Criar a seguinte estrutura em `GOD/tasks/`:

```
GOD/tasks/{cod-da-task}/
├── plan.md
└── status.md
```

> **Mudança v9:** `description.md` **não é mais criado**. O input bruto vive na seção `## Input bruto` da própria spec (modo trivial não tem input bruto registrado em arquivo — o usuário sabe o que está fazendo).

**`plan.md`** — criar vazio, será preenchido pela skill `plan`.

**`status.md`** — criar com YAML frontmatter:

**Para perfil `normal` ou `critical` (spec existe):**

```yaml
---
phase: specified
profile: {normal|critical}
updated_at: {timestamp-iso-8601-utc}
updated_by: init
spec_path: {caminho relativo ou absoluto da spec}
spec_version_consumed: {spec_version lida do frontmatter da spec atual}
branch: null
branch_base: null
learned: false
prs: []
---
```

**Para perfil `trivial` (sem spec):**

```yaml
---
phase: planned
profile: trivial
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
- `phase`:
  - `specified` quando spec existe (init consumiu uma spec já produzida — próximo passo é `plan`).
  - `planned` em modo trivial pra pular conceitualmente o estágio de planejamento (próximo passo é `implement` direto, sem `plan` formal).
- `profile`: registrado pra dashboards e roteamento (ex: `pack-up` em task crítica pode exigir aprovação extra).
- `spec_path`: caminho da spec resolvido. Em modo trivial, `null`.
- `spec_version_consumed`: a versão lida agora. Se a spec for atualizada via `update-spec` depois, `implement` detecta drift comparando.
- `branch`, `branch_base`: `null` — `plan` resolve, `implement` cria fisicamente. Em modo trivial, `plan` será pulado mas o `implement` ainda resolve a branch sozinho (ver guard-rail).

### 3.5. Criar pasta de retrocompat opcional

Se a task é legacy v8 (já tinha `description.md` na pasta antes de v9), preservar — não tocar no arquivo. Apenas adicionar `plan.md` (se ausente) e `status.md` (se ausente).

Se for task nova v9, **não criar `description.md`**.

### 4. Executar hook `after init`

Ler `GOD/hooks.md` e localizar a seção `# after init`.

- Se o conteúdo for `skip-hook`: pular e seguir para o passo 5.
- Se houver instruções em linguagem natural: executá-las integralmente antes do relatório final.

### 5. Reportar resultado

**Para perfil `normal` ou `critical`:**

> ✅ Task `{cod-da-task}` inicializada (perfil: {perfil})!
>
> 📐 Spec referenciada: `{spec_path}` (spec_version: {N})
> 📋 `GOD/tasks/{cod-da-task}/plan.md` — aguardando planejamento
> 📍 `GOD/tasks/{cod-da-task}/status.md` — fase: `specified`, branch: `null`
>
> 💡 Próximo passo: rode `plan {cod}` — vai ler a spec e produzir o plano técnico (arquitetura, arquivos, passos referenciando ACs).

**Para perfil `trivial`:**

> ✅ Task `{cod-da-task}` inicializada (perfil: trivial)!
>
> 📋 `GOD/tasks/{cod-da-task}/plan.md` — vazio (modo trivial)
> 📍 `GOD/tasks/{cod-da-task}/status.md` — fase: `planned`, branch: `null`
>
> 💡 Próximo passo: rode `implement {cod}` direto — sem spec/plan, mude o que precisar e siga pro `pack-up`.

Se a skill foi invocada pelo `init-tree`, o relatório final é consolidado pela skill chamadora; aqui basta retornar controle silenciosamente após a criação bem-sucedida.

---

## Guard-rails

- **Esta skill não toca no git.** Não faz checkout, não cria branch, não valida estado. A resolução do nome da branch é responsabilidade do `plan`; a criação física é do `implement`. Em modo `--type=trivial`, o próprio `implement` resolve a branch (porque `plan` é pulado).
- **Esta skill não escreve em `GOD/knowledge.md`.** Apenas a skill `learn` pode fazê-lo.
- **Esta skill não busca dados em sistemas externos** (Jira, Figma). Esse fetch é do `spec`.
- **Esta skill não faz Q&A com o usuário sobre escopo.** Q&A acontece no `spec`.
- **Esta skill não escreve nem modifica a spec.** Apenas referencia (`spec_path`).
- **Esta skill não cria `description.md` em tasks novas.** Em tasks legacy v8 que já tinham, preserva.
- **Modo `--type=trivial` é exceção consciente.** Pula spec pra mudanças cosméticas. Não use pra fugir de spec em mudança real — `pack-up` em task de domínio sem spec vai gerar PR sem rastreabilidade, e isso é dívida que volta no code review.

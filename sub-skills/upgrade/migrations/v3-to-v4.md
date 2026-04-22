# Migração v3 → v4

## Objetivo

A v4 é uma versão grande com cinco mudanças agrupadas:

1. **Novas sub-skills `pause` e `resume`** — permitem congelar uma task em andamento (com observação do usuário) e retomá-la depois, sem perder contexto. Úteis quando o `implement` ou `plan` detecta uma barreira (código ausente, dependência externa indisponível, decisão pendente) ou quando o usuário arbitrariamente quer interromper.
2. **`implement` passa a manter um `changelog.md` por task** — atualizado incrementalmente a cada sub-task concluída. Esse é o "documento de continuidade" que sobrevive a interrupções e é lido pelo `resume` para retomada.
3. **Novo campo `paused` no `status.md`** — modificador paralelo à `phase`. Não altera a fase, apenas sinaliza que a task está congelada.
4. **Reorganização de responsabilidades no ciclo `init → plan → implement` + nova sub-skill `init-tree`:**
   - `init` fica enxuto: só cria pastas + description.md bruto. **Não toca no git** e **não lê `patterns.md`**.
   - `plan` ganha: detectar single vs multi-project (via `git rev-parse --show-toplevel` — se falha, é workspace multi-project), resolver **nome e base** da branch (uma em single, lista por projeto em multi), escrever uma seção **"Branch de trabalho"** no topo do `plan.md` e persistir em `status.md`. Continua sem criar branch no git.
   - `implement` ganha a responsabilidade de **criar fisicamente a branch no git** no início da execução (lendo `branch`/`branch_base` do status), validar estado do git e oferecer opções (reverter/stash/abortar) em caso de pendências.
   - **Nova sub-skill `init-tree`** — inicializa em lote a partir de uma árvore do Jira (Epic → Stories → Subtasks). Folhas viram tasks reais (delegadas ao `init`); nós internos viram pastas de contexto (`kind: context` no frontmatter). Filtro por status configurável via seção opcional `## Status Jira a ignorar em batch` no `patterns.md`.
   - **Novo campo `kind`** no frontmatter do `description.md` — `kind: task` (default) ou `kind: context`. O `status` ignora pastas `kind: context` no dashboard.

Do ponto de vista do usuário, nada precisa ser reconfigurado. A migração é essencialmente um bump de versão — as features novas ficam disponíveis automaticamente após o upgrade.

## Arquivos afetados

**Atualizado:**
- `GOD/VERSION` — conteúdo muda de `v3` para `v4`

**Inalterados (nenhuma reescrita automática):**
- `GOD/knowledge.md`
- `GOD/patterns.md` (usuário pode opcionalmente adicionar a nova seção `## Status Jira a ignorar em batch` se for usar `init-tree`)
- `GOD/hooks.md`
- `GOD/tasks/` (todas as tasks, `status.md`, `description.md`, `plan.md`)
- `GOD/tasks/.archived/` (se existir)

**Novos (opcionais, criados sob demanda pelas skills):**
- `GOD/tasks/{cod}/changelog.md` — criado pelo `implement` na primeira execução em tasks futuras, ou pelo `pause` se invocado antes do `implement`. Tasks antigas não recebem changelog retroativo
- Campo `paused: true` no `status.md` — só aparece quando uma task é pausada
- Campo `branch_base` no `status.md` — populado pelo `plan` quando resolve a branch. Tasks antigas (v3) sem esse campo continuam funcionando; quando re-rodarem `plan`, ele popula
- Frontmatter `kind: task` em `description.md` de tasks novas criadas pelo `init`; `kind: context` em pastas criadas pelo `init-tree` como nós pai/intermediários. Tasks antigas sem `kind` são tratadas como `kind: task` por padrão
- No modo multi-project workspace (pasta sem `.git` contendo N repos), o campo `branch` no `status.md` passa a ser uma lista `[{project, name, base}]` em vez de string simples

**Reorganização de skills (mudança de contrato, não de arquivos):**
- `init` fica offline e sem git — passos de git e patterns saíram
- `plan` ganha resolução de branch (nome + base) e multi-project
- `implement` ganha criação de branch no git
- `init-tree` é skill nova

## Riscos conhecidos

- **Nenhum risco de perda de dados.** A migração não toca em tasks existentes nem em arquivos do usuário além do `VERSION`.
- **Tasks antigas não terão `changelog.md`.** Se o usuário retomar uma task v3 (em `phase: implementing`) após o upgrade, a skill `implement` vai criar o `changelog.md` na primeira passada e começar a registrar dali em diante — histórico anterior à v4 não é reconstruído.
- **Sem validação automática do campo `paused`.** Como o campo é opcional (ausência = não pausada), tasks antigas continuam válidas sem nenhuma alteração no YAML.

---

## Passos da migração

### 1. Verificar pré-condições

- Confirmar que `GOD/VERSION` existe e contém `v3`
- Se não existir, abortar — o usuário deve rodar as migrações anteriores primeiro (`v1-to-v2`, `v2-to-v3`)

### 2. Atualizar VERSION

Sobrescrever o conteúdo de `GOD/VERSION` com:

```
v4
```

### 3. Relatório final

```
✅ Migração v3 → v4 concluída!

VERSION atualizado: v4

Novidades disponíveis:
  ⏸  pause            — pausa uma task em andamento e registra observação no changelog
  ▶  resume           — retoma task pausada e delega de volta à skill da fase ativa
  🌲 init-tree        — inicializa em lote a partir de uma árvore do Jira (Epic/Story + subtasks)
  📝 changelog.md     — documento de continuidade incremental da implementação (criado automaticamente pelo `implement` a partir da próxima execução)
  🔀 multi-project    — o `plan` detecta se você está num workspace (pasta sem .git contendo N repos). Nesse caso, `status.branch` vira lista `[{project, name, base}]` e o `implement` cria uma branch em cada projeto afetado

Mudanças de responsabilidade (init → plan → implement):
  - init       agora não toca no git e não lê patterns.md — só cria pastas e description bruto
  - plan       agora resolve branch (nome + base), escreve em status.md e numa seção "Branch de trabalho" do plan.md
  - implement  agora cria a branch no git ao iniciar (lendo branch e branch_base do status.md)

Tasks existentes não foram alteradas. A próxima execução de `plan` em tasks v3 resolverá/persistirá branch+branch_base. A próxima execução de `implement` criará a branch no git (se ainda não existir).

💡 Experimente: para uma Epic com subtasks no Jira, rode `init-tree PROJ-100` — ele cria pastas de contexto pro Epic/Stories e tasks reais pras subtasks, tudo em lote.
```

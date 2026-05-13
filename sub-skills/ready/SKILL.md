---
name: ready
description: |
  Step manual pós-pack-up (v12). Tira o PR de draft via `gh pr ready` e adiciona reviewers da lista configurada em `GOD/config.md` (seção `## reviewers`). Suporta dois modos: explícito (`ready {cod}`) ou recomendação (`ready` sem argumento) — varre tasks com PR draft cujas dependências de stack já mergearam e propõe a lista pro usuário aprovar em batch. Atualiza `status.md` com `ready: true` + timestamp. Use quando o usuário mencionar: "ready", "tirar PR de draft", "liberar PR", "adicionar reviewers", "PR pronto pra review", "marcar PR como pronto", ou após `pack-up` quando ele quiser sinalizar que o PR está pronto pra revisão humana.
tools: Read, Glob, Grep, Bash, Edit, Write
---

# Ready — Sub-skill de liberação de PR pra review (v12)

> Tira PR de draft + adiciona reviewers do config. Step **manual** pós-pack-up — nunca dispara automaticamente em `auto`. Roda no contexto local (lê `GOD/tasks/*/status.md`) e fala com GitHub via `gh` CLI.

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

## Posição no fluxo

```
init → spec → [publish-spec] → plan → implement → pack-up → ready
                                                              ^^^^^
                                                          você está aqui
```

> `ready` é opcional do ponto de vista do fluxo — você pode tirar o PR de draft manualmente pelo GitHub. A skill existe pra automatizar a adição de reviewers do time e pra dar **recomendação inteligente** em projetos com stack (quando uma task A mergeia, propõe ready das tasks B/C/D que dependiam dela).

## Modos de invocação

- **`ready {cod}`** — modo explícito. Tira o PR daquela task de draft, adiciona reviewers do config. Falha se a task não tem PR registrado ou não está em `phase: packed-up`.
- **`ready`** (sem argumento) — modo recomendação. Varre tasks com PR draft, identifica quais estão liberadas (sem stack_parent OU stack_parent já mergiado), propõe lista pro usuário aprovar.
- **`ready --auto`** — modo recomendação **sem confirmação**. Libera todas as elegíveis automaticamente. Use com cuidado em projetos com stack — `auto` mode da skill `init` **não** dispara `ready --auto`; ele é sempre invocado pelo humano.

## Pré-requisitos

- `gh` CLI instalado e autenticado (`gh auth status` retorna OK).
- `GOD/` existe na versão atual.
- `GOD/config.md` legível (a lista de reviewers pode estar vazia — neste caso a skill apenas tira de draft, sem reviewers).

## Flags

- `--dry-run` — mostra o que seria feito (lista de tasks elegíveis + reviewers que seriam adicionados) sem chamar `gh`. Útil pra inspecionar antes de aplicar.
- `--no-reviewers` — pula a adição de reviewers mesmo se config tem lista. Só tira de draft.
- `--debug` *(v10.6)* — registra passos em `debug.log` via `_lib/debug_log.py`. Ver SKILL raiz.

## Instruções

Quando o usuário invocar esta skill, execute os passos **na ordem**:

### 0. Verificar pré-requisitos

1. `command -v gh` — se ausente, abortar com mensagem: "ready precisa do `gh` CLI instalado. Veja https://cli.github.com/."
2. `gh auth status` — se erro de auth, abortar com mensagem orientando rodar `gh auth login`.

### 1. Detectar modo

- Se o usuário passou `{cod}` → **modo explícito** (ir pro passo 2).
- Se não passou nada → **modo recomendação** (ir pro passo 3).
- Se passou `--auto` → **modo recomendação sem confirmação** (ir pro passo 3, pular confirmação no passo 3.5).

### 2. Modo explícito — single task

1. Ler `GOD/tasks/{cod}/status.md`. Se ausente: abortar com "Task {cod} não tem status.md — não foi inicializada".
2. Verificar `phase`:
   - Se `phase: packed-up` → ok, prosseguir.
   - Se outro: abortar com "Task {cod} está em phase: {phase}. `ready` só roda em tasks com `phase: packed-up` (pack-up rodou e PR foi criado)."
3. Verificar `prs`:
   - Se lista vazia: abortar com "Task {cod} não tem PR registrado em status.md".
   - Se múltiplos PRs (multi-project): pegar todos — vai aplicar `ready` em cada.
4. Verificar se já está ready (campo opcional `ready: true` no status.md):
   - Se sim: avisar "Task {cod} já foi marcada como ready em {ready_at}. Re-aplicar reviewers? (sim/não)". Default sim.
5. Ir pro passo 4 (executar gh).

### 3. Modo recomendação — varrer tasks

1. Listar todos os `GOD/tasks/*/status.md` (exceto `.archived/`).
2. Pra cada status.md, extrair: `phase`, `prs`, `ready`, `stack_parent` (opcional, v12).
3. Filtrar candidatos:
   - `phase == packed-up`
   - `ready != true`
   - `prs` não vazio
4. Pra cada candidato, classificar:
   - **Sem `stack_parent`** → **elegível imediato** (task independente).
   - **Com `stack_parent`** → ler `GOD/tasks/{stack_parent}/status.md`. Se o `prs` do parent existe:
     - Consultar `gh pr view {url} --json state,mergedAt` no primeiro PR do parent.
     - Se `mergedAt` populado → **elegível** (parent já mergeou).
     - Se não → **bloqueado** (parent ainda não mergeou — listar mas marcar bloqueado).
   - Se parent não tem PR registrado → **bloqueado por erro de estado**.
5. Pra cada candidato elegível, ler `prs[0].url` e consultar `gh pr view {url} --json isDraft,state`:
   - Se `state != OPEN` (PR mergiado ou fechado) → **pular silenciosamente** (já não cabe ready).
   - Se `isDraft: false` → **pular** (já está fora de draft — registrar `ready: true` no status.md retroativamente).
   - Se `isDraft: true` → **listar pra confirmação**.

### 3.5. Apresentar recomendação

Se a lista de elegíveis está vazia: relatar "Nenhuma task com PR draft elegível pra ready agora." + se houver bloqueados, listar com motivo (ex: "PROJ-103 aguarda merge de PROJ-101"). Encerrar.

Caso contrário, montar bloco visual:

```
🚀 ready — Tasks elegíveis pra liberar review

  ✅ PROJ-102  PR #235  (independente, sem stack)
  ✅ PROJ-103  PR #236  (libera após PROJ-101 ✅ mergeada)
  ✅ PROJ-104  PR #237  (libera após PROJ-101 ✅ mergeada)

Reviewers a adicionar (de GOD/config.md):
  @alice, @bob

Aguardando merge upstream (não elegíveis agora):
  ⏸  PROJ-105  PR #238  (aguarda PROJ-104)

Liberar todas as elegíveis? (sim / só algumas / não)
```

- **sim** → aplicar pra todas (ir pro passo 4 por task).
- **só algumas** → perguntar quais (códigos separados por vírgula).
- **não** → encerrar sem ação.

> Se modo `--auto` foi passado, pular esta confirmação e ir direto pro passo 4 pra todas as elegíveis.

### 4. Executar gh pr ready + add reviewers

Pra cada PR a liberar:

1. **Tirar de draft:** `gh pr ready {url}`.
   - Se erro (PR não existe, sem permissão): registrar e seguir pra próximo. Não abortar.

2. **Ler reviewers do config:**
   - Ler `GOD/config.md`, localizar seção `## reviewers`.
   - Extrair handles: linhas não-vazias que não começam com `#`. Remover `@` se presente.
   - Se lista vazia OU `--no-reviewers` passado: pular adição.

3. **Adicionar reviewers:** `gh pr edit {url} --add-reviewer {handle1,handle2,...}`.
   - Se erro (handle inválido, sem permissão de pedir review): registrar warning, prosseguir.

4. **Atualizar status.md da task:**
   - Adicionar/atualizar campos:
     ```yaml
     ready: true
     ready_at: {timestamp-iso-8601-utc}
     ready_reviewers: [alice, bob]
     ```
   - Bumpa `updated_at` e `updated_by: ready`.
   - Delegar pra `python3 sub-skills/_lib/update_status.py` se disponível; fallback pro Edit manual.

> Em modo `--dry-run`, pular execução real — apenas imprimir o que seria feito.

### 5. Reportar resultado

```
✅ ready concluído!

Tirados de draft (2):
  PROJ-102 — PR #235 (reviewers: @alice, @bob)
  PROJ-103 — PR #236 (reviewers: @alice, @bob)

Falhas (se houver):
  ⚠️ PROJ-104 — gh pr ready falhou: {motivo}

💡 Próximos passos:
  • Reviewers foram notificados pelo GitHub
  • Quando os PRs mergearem, rode `ready` de novo pra liberar os bloqueados restantes
  • Pra arquivar tasks com PRs mergiados, rode `clean-up`
```

---

## Guard-rails

- **Esta skill não toca em código nem em git local.** Apenas chama `gh` CLI (read + write em PRs remotos) e edita `status.md`.
- **Esta skill não cria nem fecha PRs.** Apenas muda estado (draft → ready) e adiciona reviewers.
- **Esta skill não escreve em `GOD/knowledge.md`.** Apenas a skill `learn`.
- **Esta skill não dispara automaticamente.** É sempre invocada pelo humano. `init --auto` e `init-tree --auto` chegam até o pack-up e param — `ready` é decisão consciente.
- **Esta skill não filtra reviewers por domínio na v12.** Lista plana em `GOD/config.md` — mesma lista pra todos os PRs do projeto. Se a necessidade aparecer, vira `## reviewers.{dominio}` em versão futura.
- **Esta skill não merge PR.** Auto-merge fica fora do escopo — é decisão humana após review.
- **Falha em uma task não interrompe as outras.** Reporta e segue.

---

## Integração com stack mode (v12)

Quando uma task foi inicializada com `init --stack` ou `init-tree --stack`, seu `status.md` tem campo `stack_parent` apontando pra task da qual ela depende. `ready` usa esse campo:

- No modo recomendação, `ready` cruza `stack_parent` com o estado do PR do parent (via `gh pr view`).
- Tasks independentes (`stack_parent: null`) ficam imediatamente elegíveis após pack-up.
- Tasks com parent não mergiado ficam listadas como **bloqueadas** — usuário vê o estado mas não consegue liberar até o parent mergear.

Cenário típico:

```
1. usuario roda  init-tree PROJ-100 --stack --auto
2. spec-tree + loop → todos os PRs em draft contra main
3. usuario revisa PR de PROJ-101 (raiz do stack)
4. PROJ-101 mergeia em main
5. usuario roda  ready
   → recomendação: "PROJ-101 mergeou. Liberar PROJ-102, PROJ-103, PROJ-104?"
   → usuário confirma → 3 PRs saem de draft + reviewers adicionados
6. ciclo repete conforme cada PR mergeia
```

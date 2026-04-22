---
name: status
description: |
  Mostra o estado atual de todas as tasks do projeto lendo o `status.md` de cada uma. Somente leitura, sem inferências, sem consultar git. Use quando o usuário mencionar: "status", "dashboard", "status das tasks", "como estão as tasks", ou qualquer variação de consulta de progresso.
tools: Read, Glob
---

# Status — Sub-skill de Dashboard

> Mostra o estado atual das tasks lendo apenas o `status.md` de cada pasta em `GOD/tasks/`. Nenhuma inferência, nenhuma consulta ao git, nenhuma leitura de outros arquivos.

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos:

### 1. Verificar estrutura GOD

Verificar se `GOD/tasks/` existe. Se não existir, informar que o projeto não foi configurado e sugerir rodar `install`. Encerrar.

### 2. Ler o `status.md` de cada task

Listar pastas em `GOD/tasks/`, **ignorando pastas que começam com `.`** (ex: `.archived/` — tasks arquivadas pela skill `clean-up`).

Para cada pasta restante:
- Ler `GOD/tasks/{cod-da-task}/description.md` e olhar o frontmatter YAML:
  - Se o frontmatter contém `kind: context` → **ignorar esta pasta** (é pasta documental criada pelo `init-tree` para um Epic/Story/pai — não é task real, não tem plan/status)
  - Se o frontmatter contém `kind: task` ou está ausente → tratar como task real, seguir
- Ler `GOD/tasks/{cod-da-task}/status.md`
- Extrair o YAML frontmatter: `phase`, `paused` (opcional, ausência = `false`), `updated_at`, `updated_by`, `branch`, `branch_base` (opcional), `learned`, `prs`

Se a pasta **não tiver `status.md`** e **não** for `kind: context` (task legada sem migração), listar no dashboard com `phase: —` e marcador `(sem status.md)`, sugerindo rodar `upgrade` para gerar o arquivo.

Pastas com `kind: context` **não aparecem** no dashboard — elas são apenas referência documental da árvore do Jira. Se o usuário quiser navegar a árvore, pode ler os `description.md` dessas pastas diretamente (cada uma tem a lista de filhos no frontmatter).

### 3. Mapear `phase` para descrição e próximo passo

| `phase` | Descrição | Próximo passo sugerido |
|---------|-----------|-------------------------|
| `initialized` | init concluído | `plan` |
| `planned` | plan concluído | `implement` |
| `implementing` | implement em andamento | continuar `implement` ou `update-plan` |
| `implemented` | implement concluído | `pack-up` |
| `packed-up` | PR(s) criado(s), aguardando merge/limpeza | `clean-up` quando mergiado, `learn` se quiser registrar conhecimento |

**Se `paused: true`:** o próximo passo sugerido vira **`resume`**, independente da fase. A coluna Fase no dashboard recebe o indicador `⏸` ao lado do valor (ex: `implementing ⏸`) para sinalizar a pausa visualmente.

### 4. Apresentar dashboard

```
📊 **GOD Status**

| Task | Fase | Branch | Aprendida | PRs | Atualizado em | Próximo passo |
|------|------|--------|-----------|-----|----------------|----------------|
| `PROJ-123` | implementing | `task/PROJ-123/desc` | false | 0 | 2026-04-15T14:30Z | continuar `implement` |
| `PROJ-456` | planned | `task/PROJ-456/desc` | false | 0 | 2026-04-14T09:12Z | `implement` |
| `PROJ-500` | implementing ⏸ | `task/PROJ-500/desc` | false | 0 | 2026-04-22T16:00Z | `resume` |
| `PROJ-789` | packed-up | `task/PROJ-789/desc` | false | 1 | 2026-04-13T18:00Z | `clean-up` / `learn` |
| `PROJ-999` | packed-up | `task/PROJ-999/desc` | true | 2 | 2026-04-10T11:00Z | `clean-up` |
| `LEGACY-1` | — (sem status.md) | — | — | — | — | rodar `upgrade` |
```

- Coluna **Fase** mostra `⏸` ao lado do valor quando `paused: true` está no status.md.
- Coluna **Branch** mostra o nome da branch quando `branch` é string (single-project). Quando `branch` é lista (multi-project workspace), mostrar `multi ({N} projetos)` no lugar — ex: `multi (2 projetos)`. O usuário pode ler o `status.md` diretamente para ver os nomes completos por projeto.
- Coluna **Aprendida** reflete o campo `learned` do status.md (`true` / `false`). Permite ao usuário identificar tasks `packed-up` ainda não aprendidas.
- Coluna **PRs** mostra a contagem do array `prs`. URLs completas não aparecem no dashboard (ruído visual); o usuário pode ler o `status.md` diretamente se quiser os links.

---

## Guard-rails

- **Esta skill é somente-leitura.** Lê `status.md` (campos do frontmatter) e, para cada pasta, o frontmatter de `description.md` (apenas para decidir se é `kind: context` e pular). Não lê corpo de descrições, `plan.md`, `patterns.md`, `hooks.md`, `knowledge.md`. Não executa `git` nem `gh`. Não infere fases.
- **Não escreve em nenhum arquivo.**
- **Se uma task não tem `status.md`** e não é `kind: context`, apenas reporta a ausência — não tenta inferir a fase.
- **Ignora pastas com `kind: context`** — são documentação de árvore Jira, não tasks reais.
- **Ignora `GOD/tasks/.archived/`** e qualquer pasta que comece com `.`.

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
- Ler `GOD/tasks/{cod-da-task}/status.md`
- Extrair o YAML frontmatter: `phase`, `updated_at`, `updated_by`, `branch`, `learned`, `prs`

Se a pasta **não tiver `status.md`** (task legada sem migração), listar no dashboard com `phase: —` e marcador `(sem status.md)`, sugerindo rodar `upgrade` para gerar o arquivo.

### 3. Mapear `phase` para descrição e próximo passo

| `phase` | Descrição | Próximo passo sugerido |
|---------|-----------|-------------------------|
| `initialized` | init concluído | `plan` |
| `planned` | plan concluído | `implement` |
| `implementing` | implement em andamento | continuar `implement` ou `update-plan` |
| `implemented` | implement concluído | `pack-up` |
| `packed-up` | PR(s) criado(s), aguardando merge/limpeza | `clean-up` quando mergiado, `learn` se quiser registrar conhecimento |

### 4. Apresentar dashboard

```
📊 **GOD Status**

| Task | Fase | Branch | Aprendida | PRs | Atualizado em | Próximo passo |
|------|------|--------|-----------|-----|----------------|----------------|
| `PROJ-123` | implementing | `task/PROJ-123/desc` | false | 0 | 2026-04-15T14:30Z | continuar `implement` |
| `PROJ-456` | planned | `task/PROJ-456/desc` | false | 0 | 2026-04-14T09:12Z | `implement` |
| `PROJ-789` | packed-up | `task/PROJ-789/desc` | false | 1 | 2026-04-13T18:00Z | `clean-up` / `learn` |
| `PROJ-999` | packed-up | `task/PROJ-999/desc` | true | 2 | 2026-04-10T11:00Z | `clean-up` |
| `LEGACY-1` | — (sem status.md) | — | — | — | — | rodar `upgrade` |
```

- Coluna **Aprendida** reflete o campo `learned` do status.md (`true` / `false`). Permite ao usuário identificar tasks `packed-up` ainda não aprendidas.
- Coluna **PRs** mostra a contagem do array `prs`. URLs completas não aparecem no dashboard (ruído visual); o usuário pode ler o `status.md` diretamente se quiser os links.

---

## Guard-rails

- **Esta skill é estritamente somente-leitura do `status.md`.** Não lê `patterns.md`, `hooks.md`, `knowledge.md`, `description.md`, `plan.md`. Não executa comandos `git` nem `gh`. Não infere fases.
- **Não escreve em nenhum arquivo.** Nem em `knowledge.md`, nem em `status.md`, nem em qualquer outro.
- **Se uma task não tem `status.md`**, apenas reporta a ausência — não tenta inferir a fase.
- **Ignora `GOD/tasks/.archived/`** e qualquer pasta que comece com `.`.

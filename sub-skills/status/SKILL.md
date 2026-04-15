---
name: status
description: |
  Mostra o estado atual de todas as tasks do projeto: em qual fase cada uma está, branch atual e pendências. Use quando o usuário mencionar: "status", "dashboard", "status das tasks", "como estão as tasks", ou qualquer variação de consulta de progresso.
tools: Read, Glob, Grep, Bash
---

# Status — Sub-skill de Dashboard

> Mostra o estado atual de todas as tasks do projeto: em qual fase cada uma está, branch atual e pendências.

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos:

### 1. Verificar estrutura GDD

Verificar se `GDD/` existe. Se não existir, informar que o projeto não foi configurado e sugerir rodar `install`.

### 2. Listar todas as tasks

Ler o conteúdo de `GDD/tasks/` e, para cada pasta de task encontrada, **ler primeiro o `status.md`**.

### 3. Determinar fase de cada task

**Caminho principal — `status.md` existe:**

Ler o YAML frontmatter do `GDD/tasks/{cod-da-task}/status.md` e extrair `phase`, `updated_at`, `updated_by` e `branch`. Mapear o campo `phase` para a descrição apresentada no dashboard:

| `phase` | Descrição no dashboard | Próximo passo |
|---------|------------------------|----------------|
| `initialized` | init concluído | `plan` |
| `planned` | plan concluído | `implement` |
| `implementing` | implement em andamento | continuar `implement` ou `update-plan` |
| `implemented` | implement concluído | `pack-up` |
| `packed-up` | pack-up concluído | `learn` |
| `learned` | task finalizada | — |

**Fallback — `status.md` não existe (task criada antes desta convenção):**

Inferir a fase pelos arquivos e estado do git, conforme a lógica legada:

| Condição | Fase inferida |
|----------|---------------|
| Só `description.md` existe ou `plan.md` vazio | `init` concluído — aguardando `plan` |
| `plan.md` preenchido, sem branch da task | `plan` concluído — aguardando `implement` |
| `plan.md` preenchido, branch existe, alterações não commitadas | `implement` em andamento |
| `plan.md` preenchido, branch existe, commit feito, sem PR | `implement` concluído — aguardando `pack-up` |
| PR criado | `pack-up` concluído — task entregue |

Marcar essas tasks com um indicador `(legado)` no dashboard e sugerir ao usuário que rode um step do ciclo para gerar o `status.md`.

### 4. Coletar informações extras

- Branch atual do repositório (`git branch --show-current`)
- Branch inicial definido no `GDD/pack-up-instructions.md`
- Alterações pendentes no git (`git status`)

### 5. Apresentar dashboard

```
📊 **GDD Status — {nome do projeto}**

🌿 Branch atual: `{branch}`
🏠 Branch inicial: `{branch-inicial}`
{⚠️ Alterações pendentes no git} (se houver)

---

| Task | Fase | Branch | Atualizado em | Próximo passo |
|------|------|--------|----------------|----------------|
| `PROJ-123` | implementing | `task/PROJ-123/desc` | 2026-04-15T14:30Z | continuar `implement` |
| `PROJ-456` | planned | `task/PROJ-456/desc` | 2026-04-14T09:12Z | `implement` |
| `PROJ-789` | learned | `task/PROJ-789/desc` | 2026-04-10T18:00Z | — |
| `LEGACY-1` | implement em andamento (legado) | `task/LEGACY-1/desc` | — | continuar `implement` |

---

📝 Knowledge: {X} tasks registradas em `GDD/knowledge.md`
```

---

## Guard-rails

- **Esta skill é somente leitura.** Não escreve em `GDD/knowledge.md`, não altera `status.md`, não toca em arquivos do projeto.

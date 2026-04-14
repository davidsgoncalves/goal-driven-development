# Status — Sub-skill de Dashboard

> Mostra o estado atual de todas as tasks do projeto: em qual fase cada uma está, branch atual e pendências.

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos:

### 1. Verificar estrutura GDD

Verificar se `GDD/` existe. Se não existir, informar que o projeto não foi configurado e sugerir rodar `install`.

### 2. Listar todas as tasks

Ler o conteúdo de `GDD/tasks/` e para cada pasta de task encontrada:

1. Verificar se `description.md` existe e está preenchido
2. Verificar se `plan.md` existe e está preenchido
3. Verificar o estado do git para o branch da task (se existir)

### 3. Determinar fase de cada task

Para cada task, determinar a fase atual baseado nos arquivos e estado do git:

| Condição | Fase |
|----------|------|
| Só `description.md` existe ou `plan.md` vazio | `init` concluído — aguardando `plan` |
| `plan.md` preenchido, sem branch da task | `plan` concluído — aguardando `implement` |
| `plan.md` preenchido, branch existe, alterações não commitadas | `implement` em andamento |
| `plan.md` preenchido, branch existe, commit feito, sem PR | `implement` concluído — aguardando `pack-up` |
| PR criado | `pack-up` concluído — task entregue |

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

| Task | Fase | Branch | Próximo passo |
|------|------|--------|---------------|
| `PROJ-123` | implement em andamento | `task/PROJ-123/desc` | continuar implement ou pack-up |
| `PROJ-456` | plan concluído | `task/PROJ-456/desc` | implement |
| `PROJ-789` | entregue | `task/PROJ-789/desc` | — |

---

📝 Knowledge: {X} tasks registradas em `GDD/knowledge.md`
```

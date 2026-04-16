# Migração v2 → v3

## Objetivo

A v3 traz 1 mudança principal:

1. **Renomeia a pasta do framework de `GDD/` para `GOD/`** — o nome do framework mudou de "Goal Driven Development" (GDD) para "Goal Oriented Development" (GOD). Todos os arquivos internos permanecem iguais, apenas a pasta raiz muda de nome.

## Arquivos afetados

**Renomeado:**
- `GDD/` → `GOD/` (toda a árvore interna é preservada intacta)

**Atualizado:**
- `GOD/VERSION` — conteúdo muda de `v2` para `v3`

**Inalterados (nenhuma reescrita automática):**
- `GOD/knowledge.md`
- `GOD/patterns.md`
- `GOD/hooks.md`
- `GOD/tasks/` (todas as tasks, status.md, description.md, plan.md)
- `GOD/tasks/.archived/` (se existir)

## Riscos conhecidos

- Se o usuário tiver referências hardcoded a `GDD/` em outros arquivos do projeto (`.gitignore`, `CLAUDE.md`, scripts, CI), essas referências precisarão ser atualizadas manualmente. A migração deve listar as ocorrências encontradas no relatório final.
- Se o diretório `GOD/` já existir por qualquer motivo, a migração deve abortar e alertar o usuário.

---

## Passos da migração

### 1. Verificar pré-condições

- Confirmar que `GDD/` existe
- Confirmar que `GOD/` **não** existe (para evitar conflito)
- Se `GOD/` já existir, abortar com mensagem:
  > ⚠️ Já existe uma pasta `GOD/` no projeto. Não é possível renomear `GDD/` automaticamente. Resolva o conflito manualmente e rode `upgrade` novamente.

### 2. Renomear a pasta

```bash
mv GDD/ GOD/
```

### 3. Atualizar VERSION

Sobrescrever o conteúdo de `GOD/VERSION` com:

```
v3
```

### 4. Buscar referências residuais a `GDD/`

Executar uma busca no projeto por referências à pasta antiga:

```bash
grep -r "GDD/" . --include="*.md" --include="*.yml" --include="*.yaml" --include="*.json" --include="*.toml" --include=".gitignore" --exclude-dir="GOD" --exclude-dir=".git" --exclude-dir="node_modules"
```

Se encontrar referências:
- Listar cada ocorrência no relatório final
- Sugerir ao usuário que atualize manualmente (a migração **não** altera arquivos fora da pasta `GOD/`)

### 5. Relatório final

```
✅ Migração v2 → v3 concluída!

Pasta renomeada: GDD/ → GOD/
VERSION atualizado: v3

{Se referências residuais foram encontradas:}
⚠️ Referências a "GDD/" encontradas em outros arquivos do projeto:
  - .gitignore:3 — GDD/
  - CLAUDE.md:15 — GDD/knowledge.md
  
Atualize essas referências manualmente para apontar para "GOD/".

{Se nenhuma referência encontrada:}
✅ Nenhuma referência residual a "GDD/" encontrada no projeto.

🗑️ Se você ainda tem a skill GDD antiga instalada no Claude Code, remova-a:
  - Abra as configurações do Claude Code
  - Localize a skill "gdd" (apontando para o repo antigo `goal-driven-development`)
  - Remova-a — a skill GOD já substitui todas as funcionalidades
```

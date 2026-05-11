# Migração v8 → v9

> **Nota histórica (v11):** esta migration foi escrita retrospectivamente em v11 pra fechar o gap entre v8 e v10 — quando v9 foi entregue, o documento não foi criado. Ela descreve a mudança da v9 **como ela foi originalmente** (spec-first, `spec → init`). A v11 reverteu essa ordem (`init → spec`), então quem migra de v8 vai passar por v9 → v10 → v11 em cadeia e acabar no fluxo atual. Cada salto na cadeia preserva o trabalho existente.

## Objetivo

A v9 introduz **Spec-first + spec viva**:

- **Spec-first:** spec passa a ser o entry point do fluxo (antes era `init → spec`; v9 inverte pra `spec → init`). Spec rejeitada deixa de poluir o repo com branch órfã.
- **Spec viva:** mudança de escopo pós-init deixa de ser invisível. Skill nova `update-spec` aplica delta, bumpa `spec_version`, escreve em `<specs_path>/tasks/{cod}-changelog.md`. Próximo `implement` detecta drift via freshness check estendido.
- **3 perfis de task:** `trivial` (cosmético, pula spec via `init --type=trivial`), `normal` (default), `critical` (sugere `publish-spec` antes do init).
- **`description.md` morre em tasks novas:** input bruto vai direto pra seção `## Input bruto` da spec. Tasks legacy v8 com `description.md` continuam compatíveis — spec lê pra retrocompat.

Mudanças estruturais:

- **`spec` ganha modo `--review-feedback`** — incorpora feedback externo antes do init, bumpa `spec_version` sem precisar do `update-spec`.
- **`spec` ganha modo `batch`** — chamado por `init-tree` pra gerar spec rascunho por folha (sem Q&A interativa).
- **`init` muda de entry point pra fase pós-spec** — exige spec existir (exceto `--type=trivial`). Para de criar `description.md`. Status.md ganha campos `spec_path`, `spec_version_consumed`.
- **`init-tree` reescrito** — desce a árvore do Jira, cria pastas de contexto pra nós internos e gera specs rascunho pra cada folha (via spec batch).
- **`update-spec` (skill nova)** — única forma de mudar escopo após init. Mantém histórico em `{cod}-changelog.md`.
- **`implement` ganha freshness check estendido** — se a spec foi atualizada, lê o changelog, cruza ACs alterados com `coverage.md` e oferece reabrir passos.
- **`pack-up` carimba `spec_version_delivered`** no PR description + link do `{cod}-changelog.md` se houve mudança durante a task.

## Arquivos afetados

**Atualizado:**
- `GOD/VERSION` — conteúdo muda de `v8` para `v9`

**Inalterados (nenhuma reescrita automática):**
- `GOD/config.md`
- `GOD/knowledge.md`
- `GOD/patterns.md`
- `GOD/learned-patterns.md`
- `GOD/hooks.md`
- `GOD/tasks/` (todas as tasks v8 — `description.md`, `status.md`, `plan.md`, `coverage.md`)
- `GOD/tasks/.archived/` (se existir)
- `<specs_path>/` (specs existentes — geradas pela v6/v7/v8 — intactas)

**Mudanças de contrato (não de arquivos):**
- `spec` vira entry point do fluxo.
- `init` roda depois de spec (exceto `--type=trivial`).
- `update-spec` disponível.
- `init-tree` reescrito (delega ao spec em modo batch).
- `pack-up` carimba `spec_version_delivered` no PR.

## Riscos conhecidos

- **Tasks v8 ativas em qualquer fase pós-init** — continuam funcionando intactas. Status.md já tem os campos básicos (`phase`, `branch`, etc.). Campos novos (`spec_path`, `spec_version_consumed`) são opcionais — quando ausentes, o freshness check trata como "primeira execução do plan/implement" e prossegue silenciosamente.
- **Tasks v8 legacy com `description.md`** — quando o usuário rodar `spec {cod}` sobre uma task legacy, spec detecta o `description.md` e importa como `## Input bruto` (caso C do passo 0.5). Sem perda de informação.
- **Mudança de ordem é breaking conceitualmente** — usuários acostumados a `init {cod}` primeiro precisam aprender que agora `spec {cod}` é o entry point. Mensagens de erro do `init` orientam (sugere `spec` se não houver spec prévia).
- **`init-tree` gera spec rascunho em batch** — pode produzir specs rasas sem Q&A. Documentado como rascunho (`draft: true` no frontmatter); usuário refina cada uma com `spec {cod}` interativo depois.
- **Nenhum risco de perda de dados.** Migração só atualiza VERSION; nenhum arquivo é removido nem reescrito.

---

## Passos da migração

### 1. Verificar pré-condições

- Confirmar que `GOD/VERSION` existe e contém `v8`.
- Se não existir ou estiver em versão anterior, abortar — o usuário deve rodar as migrações anteriores primeiro.

### 2. Atualizar VERSION

Sobrescrever o conteúdo de `GOD/VERSION` com:

```
v9
```

### 3. Não tocar em tasks ativas

A migração **deliberadamente não modifica** nenhum arquivo dentro de `GOD/tasks/{cod}/` ou `<specs_path>/`. As mudanças (spec-first, update-spec, init reescrito, init-tree reescrito) só atuam em execuções futuras.

Tasks já em `phase ∈ {planned, implementing, implemented, packed-up}` continuam fluindo normalmente pelo caminho legado.

### 4. Relatório final

```
✅ Migração v8 → v9 concluída!

VERSION atualizado: v9

Nenhum arquivo modificado além do VERSION.

Novidades disponíveis:
  📐 spec                       — entry point do fluxo (antes era init)
  🔁 update-spec                — mudança de escopo pós-init com changelog
  🌲 init-tree                  — inicialização em lote via árvore Jira (specs rascunho)
  🏷️  3 perfis (trivial/normal/critical) — cerimônia proporcional ao risco
  🔍 implement freshness check  — detecta drift de spec via changelog
  📦 pack-up                    — carimba spec_version_delivered + link do changelog no PR

Tasks em andamento continuam compatíveis pelo caminho legado.

Próximos passos sugeridos:
  - Em tasks novas, comece com `spec {cod}` (não mais `init {cod}`).
  - Pra mudança trivial (typo, copy, dep upgrade): `init {cod} --type=trivial` pula spec.
  - Pra task em andamento com escopo que mudou: `update-spec {cod}`.
```

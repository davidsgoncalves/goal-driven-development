---
name: update-spec
description: |
  Aplica mudança de escopo na spec de uma task **depois** que `init` rodou (fase posterior a `specified`). Pergunta motivo, edita a spec, incrementa `spec_version`, registra delta em `<specs_path>/tasks/{cod}-changelog.md`. Diferente de `spec --review-feedback` que só roda antes do init. Use quando o usuário mencionar: "atualizar spec", "spec mudou", "PM mudou de ideia", "mudança de escopo", "update spec", ou quando o escopo de uma task em andamento for alterado.
tools: Read, Glob, Grep, Bash, Edit, Write, Agent
---

# Update Spec — Sub-skill de Atualização de Spec (pós-init)

> Aplica mudança de escopo na spec de uma task que **já passou por `init`**. Pergunta motivo, edita a spec, incrementa `spec_version`, registra delta em `<specs_path>/tasks/{cod}-changelog.md` e dispara propagação leve (alerta `implement` no próximo run via freshness check). É o mecanismo da v9 pra "spec viva" — mudança de escopo deixa de ser invisível.

## Quando usar (vs `spec --review-feedback`)

| Situação | Skill correta |
|----------|---------------|
| Spec ainda não foi consumida pelo `init` (não há `GOD/tasks/{cod}/status.md`) | `spec --review-feedback {cod}` |
| Spec já foi consumida pelo `init`, task está em `specified`, `planned`, `implementing` ou similar | **`update-spec`** (esta skill) |
| Task já está em `packed-up` (PR aberto) | Avalie se vale; geralmente é melhor abrir nova task |

## Otimização v10.2

- Update de frontmatter da spec (bumpa `spec_version`, atualiza `updated_at`, mexe `applicable_rules`) delega pra `sub-skills/_lib/update_status.py` (mesmo script, aceita qualquer arquivo com YAML frontmatter via `--god-root`).
- Update de `status.md` (passo 9 — `updated_by: update-spec`) idem.
- Fallback LLM/Edit mantido.

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos **na ordem**:

### 0. Sincronizar repo de specs (sync check)

Antes de qualquer leitura/escrita de spec, garantir paridade com remoto pra evitar update sobre versão antiga (ex: outro dev fez `update-spec` da mesma task e você não puxou ainda).

1. Resolver `specs_path` (`GOD/config.md` ou default `docs/specs/`).
2. Detectar se `<specs_path>` é git: `git -C <specs_path> rev-parse --git-dir` (silenciar erro). Se não for git, pular passo.
3. Fetch silencioso: `git -C <specs_path> fetch --quiet`. Se falhar (offline, etc.), avisar e perguntar se prossegue.
4. Comparar HEAD local vs upstream: `git -C <specs_path> rev-list --left-right --count HEAD...@{u}` → `A B`.
5. Se `B > 0` (remoto à frente):

   > ⚠️ Repo de specs tem **{B} commits remotos não puxados**.
   >
   > A spec de `{cod}` que você quer atualizar pode não estar na versão mais recente — outro dev pode ter feito `update-spec` antes.
   >
   > - (a) Puxar agora (`git pull --ff-only`) e seguir — recomendado.
   > - (b) Prosseguir mesmo assim (risco real de update sobre versão obsoleta + conflito de merge).
   > - (c) Abortar.

   Aplicar escolha. (a) = `git -C <specs_path> pull --ff-only`; falha de FF aborta com orientação manual.

6. Se `B == 0`: prosseguir.

### 1. Identificar a task

- Se o contexto da conversa contém o código da task, usar.
- Caso contrário, perguntar: "Qual o código da task que teve mudança de escopo? (ex: PROJ-123)"

### 2. Validar pré-requisitos

Verificar:
- `GOD/tasks/{cod}/status.md` existe (init rodou). Se não existe, abortar e orientar:

  > ⚠️ Não encontrei `GOD/tasks/{cod}/status.md`. Esta task ainda não passou por `init`.
  >
  > Use `spec --review-feedback {cod}` em vez de `update-spec` — é o fluxo certo pra mudança de escopo antes do init.

- Ler `status.md` e checar `phase`. Se `packed-up`, alertar:

  > ⚠️ Task `{cod}` está em `packed-up` (PR já aberto/mergiado). Mudança de escopo aqui geralmente vira nova task — `update-spec` ainda funciona, mas considere se faz mais sentido criar `{cod}-followup`. Quer (a) seguir mesmo assim, (b) abortar?

- Ler `spec_path` do `status.md`. Resolver e verificar que `<spec_path>` aponta pra arquivo existente. Se não, abortar.

### 3. Ler estado atual

Carregar em memória:
- A spec atual (`<spec_path>`)
- `spec_version` atual (do frontmatter)
- `phase` atual (do `status.md`)
- `spec_version_consumed` atual (do `status.md`)
- Lista de ACs e REQs vigentes (parseando a spec)
- Existência de `<specs_path>/tasks/{cod}-changelog.md` (criar se não existir, ver passo 6)

### 4. Entender a mudança

Perguntar ao usuário, agrupado:

> 📝 Vamos registrar a mudança de escopo na spec de `{cod}`.
>
> 1. **Motivo:** o que disparou a mudança? (ex: PM mudou de ideia, descoberta técnica, feedback de stakeholder, bug descoberto durante implement, etc.)
> 2. **Origem:** onde veio? (Jira comment, Slack, conversa, decisão própria, etc.)
> 3. **Resumo da mudança:** em 1-2 linhas, o que muda no comportamento?
> 4. **REQs/ACs afetados:** quais? (pode listar IDs específicos ou descrever; eu identifico os IDs no passo seguinte)
> 5. **Afeta BRs aplicáveis?** (apenas se v10 ativa: spec tem `applicable_rules` e `domains_path` configurado) — a mudança adiciona ou remove BRs aplicáveis a esta task?

Aguardar respostas. Se o usuário não souber identificar IDs afetados, prosseguir — o passo 5 cruza descrição com a spec pra identificar.

### 5. Identificar deltas

Ler a spec atual e identificar, com base no resumo do usuário:
- **REQs/ACs a alterar** (mudança de comportamento, ampliação, restrição)
- **REQs/ACs a remover** (deprecated)
- **REQs/ACs a adicionar** (novos)
- **Cenários afetados** (happy path, edge cases, erros)
- **NFRs afetados**

Apresentar diff proposto pro usuário **antes de aplicar**:

> Mudanças propostas:
>
> **Alterar:**
> - AC-001.2: ampliar pra aceitar telefone fixo (8 dígitos)
> - REQ-002 cenário "edge cases": adicionar caso "número internacional"
>
> **Adicionar:**
> - REQ-004: exportação CSV de telefones no admin
>   - AC-004.1: ...
>   - AC-004.2: ...
>
> **Remover:**
> - AC-002.1: deprecated pelo PM
>
> Aplicar tudo? (s) ou ajustar antes? (a)

Se o usuário pedir ajuste, iterar até alinhar. Não aplicar nada na spec até o usuário confirmar.

### 6. Aplicar mudanças e bumpar versão

Editar `<spec_path>`:
- Aplicar mudanças aprovadas (alterar/adicionar/remover REQs e ACs).
- Incrementar `spec_version` (ex: 1 → 2). **Não usar semver** — inteiro monotônico simples.
- Atualizar `updated_at` no frontmatter.
- Não tocar em `created_at`, `task`, `profile`.
- **(v10)** Se há mudança em `applicable_rules`, atualizar a lista no frontmatter. Caso a v10 não esteja ativa (sem `domains_path`), pular.
- Se a spec tinha `feedback_cycles`, **remover** o campo (esse ciclo é diferente, registrado no changelog separado).

### 7. Escrever entrada no changelog

Caminho: `<specs_path>/tasks/{cod}-changelog.md`. Se não existir, criar com cabeçalho:

```markdown
# Changelog — SPEC-{cod}

> Histórico de mudanças aplicadas via `update-spec` (pós-init). Mudanças aplicadas via `spec --review-feedback` (pré-init) ficam registradas como "Histórico de feedback" dentro da própria spec.
```

Anexar ao final (ordem cronológica, mais novo embaixo OU em cima — escolher mais novo embaixo, igual git log reverso):

```markdown
## v{N} — {timestamp ISO 8601 UTC}

**Motivo:** {motivo dado pelo usuário}
**Origem:** {Jira comment | Slack | conversa | decisão técnica | outro}
**Resumo:** {1-2 linhas do que mudou no comportamento}

### Deltas

**Alterado:**
- AC-001.2: {antes → depois}
- REQ-002 cenário "edge cases": {antes → depois}

**Adicionado:**
- REQ-004 (com AC-004.1, AC-004.2): {descrição curta}

**Removido:**
- AC-002.1 (deprecated)

**BRs aplicáveis (v10, se aplicável):**
- Adicionado: BR-PAYMENTS-012
- Removido: BR-AUTH-003 (não mais relevante após mudança de escopo)

### Impacto na execução

- Phase atual da task: `{phase}`
- spec_version_consumed antes: v{X}
- Próximo `implement` vai detectar drift e oferecer reabrir passos relacionados a: AC-001.2, AC-002.1, REQ-004
```

A seção "Impacto na execução" é importante — ela é o ponteiro pro freshness check do `implement` saber o que reabrir.

### 8. Re-rodar review

Chamar `review --spec {cod}` (sem `--quick`) pra validar que a spec atualizada continua consistente:
- Cobertura input→spec ainda OK?
- Sem contradição entre REQs?
- Sem vazamento de implementação?
- ACs novos são testáveis?

Se reprovar, iterar com o usuário. Se aprovar com ajustes, aplicar e prosseguir.

### 9. Atualizar status.md

Editar `GOD/tasks/{cod}/status.md`:
- `phase`: **preservar valor atual** — `update-spec` não muda fase. A task continua onde estava (planejando, implementando, etc.).
- `updated_at`: novo timestamp ISO 8601 UTC.
- `updated_by`: `update-spec`.
- `spec_version_consumed`: **NÃO atualizar aqui**. A próxima execução de `implement` (ou `plan`) detecta drift e atualiza após o usuário decidir como prosseguir.
- Demais campos: preservar.

### 10. Reportar resultado

> ✅ Spec de `{cod}` atualizada!
>
> 📐 spec_version: v{N-1} → v{N}
> 📝 Resumo: {resumo da mudança}
> 📜 Changelog: `<specs_path>/tasks/{cod}-changelog.md` (entrada v{N})
>
> 🔔 **Próximo `implement` ou `plan` desta task vai detectar a mudança** (freshness check) e oferecer reabrir passos relacionados aos ACs alterados:
> - {lista de IDs alterados}
>
> 💡 Se a mudança requer republicar pro stakeholder (perfil critical), rode `publish-spec {cod}` agora.

---

## Guard-rails

- **Esta skill é a única dona de mudança de spec pós-init.** O `spec --review-feedback` cobre só pré-init. Não tente editar a spec manualmente sem registrar no changelog — isso vaza rastreabilidade.
- **Esta skill não muda `phase` da task.** A task continua onde estava. Phase só muda via skills do fluxo principal (`plan`, `implement`, `pack-up`).
- **Esta skill não atualiza `spec_version_consumed`.** Esse campo é responsabilidade do consumidor (`plan`/`implement`) decidir quando "consumiu" a nova versão. Update-spec só publica a mudança.
- **Esta skill não toca em git.** Não comita a spec, não comita o changelog. Commit é responsabilidade do `pack-up` (que pega tudo no final) ou do usuário manual entre fases.
- **Esta skill não escreve em `GOD/knowledge.md` nem em `GOD/learned-patterns.md`.**
- **Esta skill não publica automaticamente.** Não chama hooks. Republicação manual via `publish-spec` se necessário (sugerido no relatório).
- **Mudança que invalida AC já implementado:** se o `coverage.md` (v8) registra teste/validação amarrada a um AC removido, esse teste vira órfão. A skill **não remove** o teste — só sinaliza no changelog. Decisão de manter/remover o teste fica do dev no próximo `implement`.
- **Não há limite de versões** — pode subir indefinidamente. Se a task acumular muitas mudanças (ex: v8+), considere se faz mais sentido cancelar e abrir tasks separadas. Esta skill não enforça, só sinaliza.

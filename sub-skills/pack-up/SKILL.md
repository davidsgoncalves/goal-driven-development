---
name: pack-up
description: |
  Executa o fluxo de finalização da task: commit, push, criação de PR e ações finais — tudo conforme definido no patterns.md. Processos customizados (testes, linter, etc.) ficam nos hooks `before pack-up`/`after pack-up`. Use quando o usuário mencionar: "pack up", "finalizar task", "fechar task", "empacotar", ou quando a fase de finalização for ativada pelo GOD.
tools: Read, Glob, Grep, Bash, Edit, Write, Agent
---

# Pack-up — Sub-skill de Finalização

> Executa o fluxo de finalização da task: commit, push, criação de PR e ações finais — tudo conforme definido no `patterns.md`. Processos customizados (rodar testes, linter, notificações, etc.) são configurados pelo usuário nos hooks `before pack-up`/`after pack-up` em `GOD/hooks.md`.

## Flags

- `--debug` *(v10.6)* — quando presente, registra cada passo em `GOD/tasks/{cod}/debug.log` via `_lib/debug_log.py`. Opt-in por invocação. Sem flag, zero overhead. Ver "Debug log opt-in" no SKILL.md raiz pra padrão de chamada.

## Pontos de log (quando `--debug` ativo)

Pra cada passo abaixo, chamar `python3 sub-skills/_lib/debug_log.py` com:

| Passo | step | action | details típico |
|-------|------|--------|----------------|
| 0 hook before | `"0 before pack-up"` | `skipped` ou `executed` | `{"hook_present": false}` |
| 2.5 batch | `"2.5 batch validate"` | `batch_consumed` ou `fallback_llm` | `{"python3": "3.13", "ok": true, "acs": 4, "diff_files": 12}` |
| 4 review | `"4 review --execution"` | `delegated` | `{"mode": "inline", "from_config": true}` |
| 4.5 coverage | `"4.5 coverage"` | `batch_consumed` ou `script_delegated` ou `fallback_llm` | `{"orphans": 1}` |
| 4.6 rules | `"4.6 rules"` | `skipped` ou `batch_consumed` | `{"applicable_rules_count": 0}` |
| 5 commit | `"5 commit"` | `completed` | `{"files_committed": 12}` |
| 6 push | `"6 push"` | `completed` | `{}` |
| 7 PR | `"7 pr create"` | `delegated` ou `fallback_llm` | `{"description_size_bytes": 1450}` |
| 8 status update | `"8 status update"` | `script_delegated` ou `fallback_llm` | `{"phase": "packed-up"}` |

Sem `--debug`, **pular todas essas chamadas**. Skill funciona idêntica.

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos **na ordem**:

### 0. Executar hook `before pack-up`

Ler `GOD/hooks.md` e localizar a seção `# before pack-up`.

- Se o conteúdo for `skip-hook`: pular e seguir para o passo 1.
- Se houver instruções em linguagem natural: executá-las integralmente antes de prosseguir. Exemplos comuns são rodar testes, linter, type-check.
- **Se o hook falhar** (ex: testes vermelhos, lint com erro):
  - Informar o usuário sobre a falha
  - Tentar corrigir automaticamente se for algo simples (ex: auto-fix de lint)
  - Se não conseguir corrigir, pausar o pack-up e perguntar ao usuário como prosseguir

### 1. Ler convenções do projeto

Ler o arquivo `GOD/patterns.md` para obter as convenções de formatação:
- Padrão de mensagem de commit
- Padrão de mensagem de PR (título e corpo)

A **branch de destino do PR** (base target) e o **nome da branch da task** não são lidos de `patterns.md` nesta skill — já estão persistidos em `GOD/tasks/{cod-da-task}/status.md` (`branch_base` e `branch`, respectivamente, populados pelo `plan`).

**Multi-project workspace:** se `status.branch` for uma **lista** `[{project, name, base}, ...]` em vez de string, a task afeta múltiplos projetos. Nesse caso, a pack-up itera pelos projetos: para cada entrada, faz `cd` no projeto, commita e abre PR individualmente com a base correspondente. Cada PR é adicionado ao array `prs` do `status.md`.

> Observação: `patterns.md` contém **apenas padrões**. Ações executáveis (criar PR em draft, não atribuir reviewers, adicionar labels, notificar canais, atualizar tickets) ficam no hook `after pack-up` em `GOD/hooks.md`.

### 2. Identificar a task

- Se o contexto da conversa já contém o código da task, usar esse código
- Caso contrário, perguntar ao usuário o código da task (ex: `PROJ-123`)
- Ler `GOD/tasks/{cod-da-task}/description.md` para obter título e descrição da task

### 2.5. Carregar context blob + batch validação (v10.4 + v10.5)

Carrega **uma vez** todos os artefatos relevantes e roda validação consolidada. Eliminou ~5 invocações sequenciais (coverage + parse_rules + freshness + lint + montagem PR data) por **1 chamada Python**.

**Caminho preferido (v10.5):** delegar pra `sub-skills/_lib/pack_up_validate.py`:

```bash
python3 sub-skills/_lib/pack_up_validate.py \
  --task {cod} \
  --branch-base {branch_base} \
  --specs-path {specs_path} \
  --god-root {god_root} \
  --source-root {source_root}
```

Capturar JSON único contendo:
- `spec` (path, version, applicable_rules, lista de REQs com contagem de ACs)
- `coverage` (matriz AC × validação completa + markdown pronto)
- `rules` (BRs aplicáveis × anotadas + markdown pronto)
- `freshness` (drift booleano, current/consumed)
- `lint` (blockers + warnings estruturais)
- `pr_description_data` (pronto pra `gen_pr_description.py`)

Esse JSON é o **context blob** dos passos seguintes:
- Passo 4 (review --execution) consome direto — não re-roda coverage/rules.
- Passo 4.5 (coverage) → já tem `coverage.markdown` pronto, pula chamada.
- Passo 4.6 (rules) → já tem `rules.markdown`, pula chamada.
- Passo 7 (PR description) → passa `pr_description_data` direto pra `gen_pr_description.py`.

**Arquivos adicionais a carregar separadamente** (não cabem no batch — são contextuais):
- `GOD/tasks/{cod}/plan.md` (alimenta review --execution).
- `GOD/patterns.md` (convenções pro commit/PR).
- `GOD/hooks.md` (lido uma vez pra todos os hooks da skill).

**Fallback (LLM)** se python3 ausente ou batch falhou: cada passo (4.5, 4.6, etc.) executa caminho LLM individualmente como na v10.2.

### 3. Verificar estado do git

Verificar o estado atual do repositório:
- Branch atual (`git branch --show-current`)
- Alterações staged e unstaged (`git status`, `git diff`)
- Confirmar que existe trabalho para commitar

Se não houver alterações, informar o usuário e encerrar.

### 4. Revisão plano vs execução

Chamar a sub-skill `review --execution` passando o código da task **e o context blob carregado no passo 2.5** (v10.4). Review usa context inline em vez de re-ler arquivos.

- Se o relatório retornar **Aprovado**: prosseguir com o commit
- Se o relatório retornar **Ajustes necessários**: apresentar o relatório ao usuário e perguntar se deseja corrigir antes de continuar ou prosseguir mesmo assim
- Se o relatório retornar **Reprovado**: apresentar o relatório ao usuário e pausar o pack-up até que as correções sejam feitas

### 4.5. Matriz de cobertura (v8 — consumida do batch v10.5)

**Caminho preferido (v10.5):** se passo 2.5 rodou `pack_up_validate.py`, o JSON já contém `coverage.markdown` pronto. **Não re-rodar nada** — apenas extrair do JSON e usar no passo 7.

**Fallback (v10.2):** se passo 2.5 caiu pro fallback LLM, delegar pra `sub-skills/_lib/parse_coverage.py --task {cod} --format markdown` via Bash. Capturar stdout markdown.

**Fallback v2 (LLM puro):** chamar a sub-skill `coverage --task {cod} --format markdown` (caminho original, mais caro).

Em qualquer caminho:
- Markdown vai pro passo 7 (PR description).
- Se ACs órfãos detectados (campo `coverage.summary.orphaned > 0` no batch JSON, ou alerta da skill), avisar:

  > ⚠️ {N} ACs sem cobertura registrada. Quer (a) voltar pro implement pra anotar, (b) editar `coverage.md` agora, (c) prosseguir mesmo assim?

- Task sem spec → no-op silencioso (sem tabela).

### 4.6. Tabela de BRs (v10 — consumida do batch v10.5)

Se a spec tem `applicable_rules` populado e `domains_path` configurado em `GOD/config.md`:

**Caminho preferido (v10.5):** o JSON do passo 2.5 já contém `rules.markdown` pronto + `rules.summary` (total, anotadas, órfãs). Extrair direto.

**Fallback (v10.2):** se batch falhou, delegar pra `sub-skills/_lib/parse_rules.py --task {cod} --branch-base {branch_base} --format markdown`.

**Fallback v2 (LLM puro):** parsear `git diff {branch_base}...HEAD` procurando `// rule: BR-X`, cruzar com `applicable_rules`, montar tabela.

Tabela vai pro PR description (passo 7). Se houver BRs órfãs (declaradas mas não anotadas):

> ⚠️ {N} BRs aplicáveis sem anotação no código. Possíveis razões:
> - A invariante já está enforced em código existente (não tocado por esta task) → adicionar nota em `coverage.md`.
> - A invariante não cabe nesta task → considerar remover de `applicable_rules`.
> - Faltou anotar `// rule:` no implement → voltar e anotar.
>
> Quer (a) voltar pro implement, (b) editar `coverage.md`, (c) prosseguir?

Default tolerante — não bloqueia. Tasks sem `applicable_rules` ou com `domains_path` desativado pulam este passo silenciosamente.

### 5. Commit

Criar o commit seguindo o **padrão de mensagem de commit** definido no `patterns.md`:
- Fazer stage das alterações relevantes (`git add` dos arquivos modificados)
- Criar o commit com a mensagem no padrão configurado
- Se o padrão não estiver definido, usar: `{cod-da-task}: {descrição breve da mudança}`

### 6. Push

Fazer push do branch para o remote:
- `git push -u origin {branch-atual}`
- Se o push falhar, informar o usuário

### 7. Criar PR (otimizado v10.2)

**Caminho preferido:** montar JSON com `{task, summary, spec_path, spec_version_delivered, reqs_covered, coverage_markdown, rules_markdown, changelog_path}` e delegar pra `sub-skills/_lib/gen_pr_description.py --input -` (stdin). Capturar markdown final, passar pra `gh pr create --body "$body"`.

**Fallback:** LLM monta o markdown linha por linha (caminho original — mantido pra retrocompat).

Em ambos:
Criar o Pull Request seguindo o **padrão de mensagem de PR** definido no `patterns.md`:
- Usar `gh pr create` com título e corpo no padrão configurado, apontando para a **branch de destino** = `branch_base` lido de `status.md` (ex: `--base main`). Se `branch_base` estiver ausente (task pré-v4 que não passou pelo novo plan), fallback para o default do repo detectado por `gh`.
- Se o padrão não estiver definido, usar:
  - **Título:** `{cod-da-task}: {título da task}`
  - **Corpo:** descrição da task + resumo das alterações
- **Anexar referência à spec** (a partir da v6, ampliado na v9): se `spec_path` estiver presente em `status.md`, adicionar ao final do corpo do PR um bloco:

  ```markdown
  ---

  📐 **Spec:** `{spec_path}` (entregue em v{spec_version_delivered})

  REQs cobertos: {lista lida do plan.md ou da spec}

  {se houve mudança de spec durante a task, ou seja, existe `<specs_path>/tasks/{cod}-changelog.md`:}
  📜 **Mudanças de escopo durante a task:** `{specs_path}/tasks/{cod}-changelog.md`
  ```

  - `spec_version_delivered` é a `spec_version` atual da spec lida agora pelo pack-up. Carimbar isso no PR cria registro do que foi efetivamente entregue — útil quando aparecer bug em produção e a spec já estiver em outra versão.
  - O link do changelog só é injetado se o arquivo existir (significa que `update-spec` foi usado). Em tasks sem mudança de escopo durante o trabalho, omitir.

  Esse bloco existe pra que quem revisa o PR saiba qual contrato a implementação cumpre — sem precisar abrir 3 arquivos. Se a spec usa path relativo, manter como está. Em multi-project, o bloco de referência é repetido em cada PR (a spec é a mesma; o que muda é o repo).

- **Anexar matriz de cobertura** (a partir da v8): logo após o bloco da spec, injetar a saída markdown da `coverage` capturada no passo 4.5:

  ```markdown
  📊 **Cobertura de ACs**

  | AC | Status | Validação |
  |----|--------|-----------|
  | AC-001.1 | ✅ | tests/phone-validator.test.ts:42 |
  | AC-001.2 | ✅ | tests/phone-validator.test.ts:55 |
  | AC-001.3 | 👁 | manual: validação visual em staging por PM |
  | AC-002.1 | ⚠️ | (sem cobertura) |

  **Resumo:** 4 ACs · 2 testes · 1 manual · 1 órfão
  ```

  Tasks sem spec não geram este bloco.
- **Anexar tabela de BRs** (a partir da v10, se `applicable_rules` populado e `domains_path` configurado): logo após a matriz de cobertura, injetar a saída do passo 4.6:

  ```markdown
  📜 **BRs aplicáveis × anotadas**

  | BR | Status | Anotações no código |
  |----|--------|---------------------|
  | BR-PAYMENTS-001 | ✅ | src/vakinha.service.ts:42 |
  | BR-PAYMENTS-007 | ✅ | src/vakinha.service.ts:55, src/meta.guard.ts:18 |
  | BR-AUTH-003 | ⚠️ | (declarada aplicável mas sem anotação no diff) |

  **Resumo:** 3 BRs aplicáveis · 2 anotadas · 1 órfã
  ```

  Tasks sem `applicable_rules` ou com `domains_path` desativado não geram este bloco.
- Capturar a URL do PR retornada por `gh pr create` — será salva no `status.md` no próximo passo

### 8. Atualizar status para `packed-up` (otimizado v10.2)

**Caminho preferido:** delegar pra `sub-skills/_lib/update_status.py`:

```bash
python3 sub-skills/_lib/update_status.py --task {cod} \
  --set phase=packed-up \
  --set updated_by=pack-up \
  --set-now updated_at \
  --append prs={url_do_pr} \
  --set spec_version_delivered={spec_version}
```

O script preserva campos não tocados (branch, branch_base, learned). Não sobrescreve `prs` — só faz append.

**Fallback** (LLM): edita o YAML manualmente garantindo:
- `phase`: `packed-up`
- `updated_at`: timestamp ISO 8601 UTC
- `updated_by`: `pack-up`
- `prs`: **append** da URL (não sobrescrever array)
- `spec_version_delivered` (v9): int, omitir em task trivial/pré-v6
- Demais campos: preservar

Exemplo antes:
```yaml
prs: []
```
Após o primeiro pack-up:
```yaml
prs:
  - https://github.com/org/myorg-api/pull/123
```
Após um segundo pack-up no mesmo cod-da-task (outro projeto no mesmo monorepo):
```yaml
prs:
  - https://github.com/org/myorg-api/pull/123
  - https://github.com/org/myorg-web/pull/456
```

### 9. Executar hook `after pack-up`

Ler `GOD/hooks.md` e localizar a seção `# after pack-up`.

- Se o conteúdo for `skip-hook`: pular e seguir para o passo 10.
- Se houver instruções em linguagem natural: executá-las integralmente antes do relatório final.

Este hook é o lugar para todas as ações pós-PR: marcar o PR como draft, remover reviewers, adicionar labels, notificar canais do Slack, atualizar status no Jira, postar update num board, etc.

### 10. Reportar resultado

> ✅ Pack-up concluído para `{cod-da-task}`!
>
> 📝 Commit: `{hash}` — {mensagem do commit}
> 🔀 Branch: `{nome-do-branch}`
> 🔗 PR: {url-do-pr}
>
> [Se hooks before/after foram executados, listar resumidamente o que rodou]

---

## Guard-rails

- **Esta skill não escreve em `GOD/knowledge.md`.** O registro no knowledge é responsabilidade exclusiva da skill `learn`, invocada pelo usuário após o pack-up.

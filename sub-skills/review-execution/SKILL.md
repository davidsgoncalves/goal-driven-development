---
name: review-execution
description: |
  Revisa execução vs plano + cobertura AC × validação (v8) + BRs aplicáveis × anotadas (v10). Verifica se passos do plano foram executados, alterações não-planejadas, ACs órfãos, BRs declaradas sem anotação no diff. Chamada pela skill `pack-up` ou diretamente como `review --execution`. Use quando o usuário mencionar: "review execution", "revisar execução", "validar implementação".
tools: Read, Glob, Grep, Bash, Agent
---

# Review-Execution — Revisão de plano vs execução

> Sub-skill focada em revisar **só** a execução final antes do pack-up. Ver "Padrão de review" e "Padrão de context blob" no SKILL.md raiz pra modo de execução, peer_review_default, context inline. Esta skill descreve apenas verificações do modo --execution.

## Flags

- `--subagent` / `--inline` / `--skip` — override pontual da config `peer_review_default`.

## Passos

1. Carregar `plan.md` e `status.md` (do context blob v10.4 ou ler do disco).
2. **(v10.5)** Se a skill chamadora passou `validation_data` (JSON do `pack_up_validate.py`): consumir direto — pula passos 4-6 abaixo. Foco do review vira **julgamento semântico** (efeitos colaterais, convenções quebradas, qualidade do código).
3. Rodar `git diff {branch_base}...{branch}` pra ver alterações.
4. Comparar planejado × executado.
5. **(v8)** Chamar `coverage --task {cod} --format json` (ou consumir do context blob) — **só se não veio `validation_data`**.
6. **(v10)** Parsear `// rule: BR-X` no diff via `_lib/parse_rules.py` — **só se não veio `validation_data`**.

## Critérios

- Todos os passos do plano foram executados?
- Há arquivos alterados fora do plano? (mudanças não-planejadas)
- Há passos do plano não implementados? (trabalho incompleto)
- As alterações seguem convenções do projeto (`patterns.md`, `learned-patterns.md`)?
- Implementação introduziu efeitos colaterais não-previstos?
- **(v8)** Todos os ACs da spec têm cobertura registrada (teste ou manual)?
- **(v8)** ACs órfãos viram alerta — não bloqueia.
- **(v10)** Todas as BRs em `applicable_rules` aparecem anotadas em pelo menos 1 lugar do diff?
- **(v10)** BRs declaradas sem anotação viram alerta — não bloqueia.

## Formato do relatório

```markdown
## Review: Plano vs Execução — {cod}

### Passos executados
- [x] {passo 1} — em `arquivo.ts`
- [x] {passo 2}
- [ ] {passo 3} — **NÃO implementado**

### Alterações não-planejadas
- {arquivo fora do plano, se houver}

### Cobertura de ACs (v8)
- ✅ AC-001.1 — `tests/foo.test.ts:42`
- 👁 AC-001.3 — manual: validação em staging por PM
- ⚠️ AC-002.1 — **órfão** (sem cobertura)

**Resumo:** {N} ACs · {X} testes · {Y} manuais · {Z} órfãos

### BRs aplicáveis (v10, se applicable_rules populado)
- ✅ BR-PAYMENTS-001 — anotada em `src/foo.ts:42`
- ⚠️ BR-AUTH-003 — **declarada aplicável mas sem anotação no diff**

**Resumo:** {N} BRs · {X} anotadas · {Y} órfãs

### Problemas encontrados
- {efeitos colaterais, convenções quebradas, etc}

### Veredito
- ✅ **Aprovado** — execução alinhada, cobertura completa, BRs anotadas
- ⚠️ **Ajustes necessários** — passos faltantes, ACs órfãos, ou BRs sem anotação
- ❌ **Reprovado** — passos críticos faltando ou efeitos colaterais
```

## Regra de veredicto

- Passos críticos não-implementados → **Reprovado**.
- Efeitos colaterais não-previstos → **Reprovado**.
- ACs/BRs órfãos sozinhos → **Ajustes necessários**, nunca **Reprovado**. Pode ser legítimo (validação externa, BR enforced em código existente fora do diff).
- Alterações não-planejadas → **Ajustes necessários** com sugestão de documentar no plan retroativamente ou rodar `update-plan`.

## Pré-requisitos

- `plan.md` e `status.md` existem em `GOD/tasks/{cod}/`.
- `branch` e `branch_base` populados em status.md.
- Em modo `subagent`: `Agent` tool com `general-purpose` (precisa Bash pra git diff).
- Context blob (v10.4) opcional.

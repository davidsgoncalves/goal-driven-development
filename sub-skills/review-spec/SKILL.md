---
name: review-spec
description: |
  Revisa a qualidade da spec recém-escrita (contrato de escopo). Verifica estrutura (ACs com IDs estáveis, REQ tem AC, seções obrigatórias), lint (vagueness, vazamento de implementação, contradição) e — fora de --quick — semântica profunda (cobertura description→spec, ACs cobertos por cenários, NFRs adequados, ortogonalidade, edge cases óbvios). Chamada pela skill `spec` ou diretamente como `review --spec`. Use quando o usuário mencionar: "review da spec", "revisar spec", "validar spec".
tools: Read, Glob, Grep, Bash, Agent
---

# Review-Spec — Revisão de qualidade da spec

> Sub-skill focada em revisar **só** a spec. Ver "Padrão de review" e "Padrão de context blob" no SKILL.md raiz pra modo de execução (subagent/inline/skip), peer_review_default, context inline. Esta skill descreve apenas as **verificações específicas do modo --spec**.

## Flags

- `--quick` — pula verificações semânticas profundas (passo C abaixo). Roda só estrutura + lint.
- `--subagent` / `--inline` / `--skip` — override pontual da config `peer_review_default` (ver SKILL raiz).

## Verificações

### A. Estrutura (sempre)

- Cada REQ tem ao menos 1 critério de aceitação.
- ACs têm IDs estáveis no formato `AC-NNN.N`.
- Spec tem todas as seções obrigatórias: `Objetivo`, `Não-objetivos`, `Requisitos`, `Cenários`, `NFRs`.
- Frontmatter contém `spec_version`, `task`, `created_at`, `updated_at`.

### B. Qualidade / lint (sempre)

- Nenhum AC vago — palavras-tabu sem métrica: "rápido", "fácil", "intuitivo", "performático", "escalável", "simples", "robusto".
- Nenhum REQ/AC vaza implementação — palavras-flag: nomes de framework (React, Rails, Django, Laravel, Vue, Angular, Express, FastAPI), banco (Postgres, MySQL, Mongo), libs específicas (Redux, RxJS, jQuery), hooks específicos (useState, useEffect, ActiveRecord).
- Sem contradição literal entre REQs.

### C. Semântica profunda (pulado em `--quick`)

- **Cobertura `## Input bruto` → spec:** cada ponto do input bruto cobre um REQ/AC.
- **Cenários cobrem ACs:** cada AC aparece em ao menos 1 cenário (happy/edge/erro).
- **NFRs adequados ao tipo:** features financeiras → NFR de auditoria/segurança/LGPD; UI → acessibilidade. Heurística, não bloqueia.
- **ACs ortogonais:** detectar pares redundantes (mesma coisa com palavras diferentes).
- **Edge cases óbvios:** dado o tipo de campo/comportamento, há edge cases conhecidos que provavelmente faltam (email duplicado, telefone com prefixo, valor zero, etc).

## Formato do relatório

```markdown
## Review: Spec — {cod}{[--quick] se aplicável}

### A. Estrutura
- [✓/✗] {check} — {detalhe se ✗}

### B. Qualidade / lint
- [✓/✗] Vagueness — {ACs com palavra-tabu}
- [✓/✗] Vazamento de implementação — {ACs/REQs com framework}
- [✓/✗] Contradições — {pares em conflito}

### C. Semântica (pulado em --quick)
- [✓/⚠] Cobertura input → spec
- [✓/⚠] Cenários cobrem ACs
- [✓/⚠] NFRs adequados ao tipo
- [✓/⚠] ACs ortogonais
- [✓/⚠] Edge cases óbvios

### Veredito
- ✅ **Aprovado** — spec pronta pra próximo passo
- ⚠️ **Ajustes necessários** — sugestões a aplicar
- ❌ **Reprovado** — spec precisa ser reescrita
```

## Regra de veredicto

- Falhas em A (estrutura) → **Reprovado**.
- Falhas em B (lint) → **Ajustes necessários** se isoladas; **Reprovado** se sistêmicas.
- Sinalizações em C → **Ajustes necessários** com tom de sugestão. Nunca **Reprovado** (heurísticas, podem ter falsos positivos).

## Pré-requisitos

- Spec deve existir em `<specs_path>/tasks/{cod}.md` (resolvido via `status.md` `spec_path` ou config).
- Em modo `subagent`: `Agent` tool disponível.
- Context blob (v10.4) opcional — se passado, evita re-leitura.

---
name: review-plan
description: |
  Revisa o plano técnico contra a spec — verifica cobertura de ACs (cada AC tem passo), scope creep (passos sem AC associado), viabilidade dos passos, ambiguidades e contradições. Chamada pela skill `plan` ou diretamente como `review --plan`. Use quando o usuário mencionar: "review do plano", "revisar plano", "validar plano".
tools: Read, Glob, Grep, Bash, Agent
---

# Review-Plan — Revisão de qualidade do plano

> Sub-skill focada em revisar **só** o plano técnico. Ver "Padrão de review" e "Padrão de context blob" no SKILL.md raiz pra modo de execução, peer_review_default, context inline. Esta skill descreve apenas verificações do modo --plan.

## Flags

- `--subagent` / `--inline` / `--skip` — override pontual da config `peer_review_default`.

## Critérios

- **Cobertura ACs → plano:** todos os ACs da spec estão cobertos por algum passo do plano?
- **Scope creep:** o plano inclui passos que não correspondem a nenhum AC? Pode ser legítimo (refator, limpeza), mas precisa ser explícito (separar bloco "Considerações técnicas" ou marcar como "fora de escopo").
- **Viabilidade:** passos são executáveis e na ordem correta? Há passo que depende de outro não listado?
- **Ambiguidades / contradições:** spec diz X, plano diz Y conflitante.
- **Figma:** se a spec tem links Figma, o plano considera elementos visuais?
- **Knowledge:** se há commits de referência em `knowledge.md`, o plano considera padrões dessas implementações?
- **(v10) Considerações arquiteturais:** se `principles_path` ou `architecture_path` configurados, o plano gerou o bloco "Considerações arquiteturais"? Sinalizou desvios sem bloquear?

## Formato do relatório

```markdown
## Review: Plano — {cod}

### Cobertura de ACs (spec → plano)
- [✓/✗] AC-001.1 — coberto no passo {N}
- [✓/✗] AC-001.2 — **NÃO coberto**

### Scope creep
- {passo sem AC, se houver — avaliar se é refator legítimo}

### Considerações arquiteturais (v10, se aplicável)
- [✓/⚠] Bloco gerado / desvios sinalizados

### Problemas encontrados
- {ambiguidades, contradições, ordem incorreta}

### Veredito
- ✅ **Aprovado** — plano cobre a spec sem lacunas relevantes
- ⚠️ **Ajustes necessários** — correções sugeridas
- ❌ **Reprovado** — plano precisa ser reescrito
```

## Regra de veredicto

- ACs sem cobertura → **Reprovado** (plano incompleto).
- Scope creep significativo sem justificativa → **Ajustes necessários**.
- Ambiguidades menores → **Ajustes necessários**.

## Pré-requisitos

- Spec existe em `<spec_path>` (do status.md).
- `plan.md` preenchido em `GOD/tasks/{cod}/plan.md`.
- Context blob (v10.4) opcional.

---
name: review
description: |
  Wrapper de roteamento (v10.4) que delega pra `review-spec`, `review-plan` ou `review-execution` conforme a flag passada. Mantém invocação `review --modo` retrocompatível com versões anteriores. Use quando o usuário mencionar: "revisar", "review", "checar qualidade".
tools: Read, Glob, Grep, Bash, Agent
---

# Review — Wrapper de roteamento (v10.4)

> A partir da v10.4, esta skill **delega** pras 3 sub-skills focadas. Não tem lógica de verificação aqui — só roteamento. Ver `review-spec`, `review-plan`, `review-execution` pra critérios e relatórios.

## Roteamento

| Flag | Delega pra |
|------|-----------|
| `--spec` (com ou sem `--quick`) | `review-spec` |
| `--plan` | `review-plan` |
| `--execution` | `review-execution` |

Pré-requisito comum: `peer_review_default` resolvido (default `subagent`). Ver "Padrão de review" no SKILL.md raiz pra modo de execução, flags de override (`--subagent`/`--inline`/`--skip`) e padrão de context blob (v10.4).

## Por que existe

Retrocompat. Skills chamadoras (`spec`, `plan`, `pack-up`) e devs costumam invocar `review --modo`. Em vez de quebrar, esta skill fina apenas redireciona.

A divisão em 3 sub-skills (v10.4) economiza tokens: cada invocação carrega só o conteúdo do modo usado, não os 3.

## Comportamento

1. Identifica modo pela flag.
2. Verifica `peer_review_default` (config + flag CLI override).
3. Se modo `skip`, retorna mensagem direto sem delegar.
4. Senão, delega pra sub-skill correspondente passando:
   - Código da task
   - Modo de execução resolvido (subagent/inline)
   - Context blob (se a skill chamadora passou)
   - Flags adicionais aplicáveis (`--quick` em --spec, etc.)

## Sem flag de modo?

Se `review` é invocada sem `--spec`/`--plan`/`--execution`, perguntar ao usuário qual modo usar baseado na fase atual da task:

- `phase: specified` → sugerir `--spec`
- `phase: planned` → sugerir `--plan`
- `phase: implementing` ou `implemented` → sugerir `--execution`

## Pré-requisitos

- Sub-skills `review-spec`, `review-plan`, `review-execution` existem em `sub-skills/`.
- Doctor pode validar a presença das 3.

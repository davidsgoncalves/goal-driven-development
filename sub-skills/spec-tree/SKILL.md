---
name: spec-tree
description: |
  Q&A unificada em batch pra gerar specs de múltiplas folhas de uma árvore inicializada por `init-tree`. Substitui a sessão `spec {cod}` × N por **uma única sessão consolidada**, agrupando perguntas por tema (auth, payments, UI, infra) via heurística do `spec` v10.1. Roda como parte do `init-tree --auto` (v12) — não é invocada diretamente pelo usuário no fluxo normal. Use quando o usuário mencionar: "spec-tree", "specs em batch", "Q&A unificada", ou quando `init-tree --auto` precisar gerar specs de várias folhas antes do loop de implement.
tools: Read, Glob, Grep, Bash, Edit, Write, Agent
---

# Spec-tree — Sub-skill de Q&A unificada em batch (v12)

> Gera specs pra um conjunto de folhas em **uma única sessão de Q&A consolidada**. Roda chamada por `init-tree --auto` após criação das estruturas, antes do loop `plan → implement → pack-up`. Não é entry point manual no fluxo padrão — pra escrever spec de uma folha só, use `spec {cod}` (Q&A focada por task).

## Banner

Ao iniciar esta skill, **antes de qualquer outra ação**, exiba exatamente este bloco no terminal:

```
  ██████   ██████  ██████  
 ██       ██    ██ ██   ██ 
 ██   ███ ██    ██ ██   ██ 
 ██    ██ ██    ██ ██   ██ 
  ██████   ██████  ██████  
  Goal Oriented Development
```

## Por que existe

`init-tree --auto` precisa rodar `spec` em N folhas sem que cada uma trave o loop pedindo Q&A interativa. Sem spec-tree, o usuário seria interrompido N vezes — uma por task — perdendo o ganho do modo automático.

Spec-tree resolve isso **antes** do loop, fazendo Q&A **uma vez** cobrindo as perguntas comuns a múltiplas folhas. Depois disso o loop roda sem fricção.

> **Comparação:**
> - `spec {cod}` × N folhas: N sessões interativas, contexto recarregado a cada vez, perguntas repetidas se folhas têm tema comum.
> - `spec-tree {raiz}`: 1 sessão, perguntas agrupadas por tema, contexto compartilhado, gera N specs.

## Modos de invocação

- **Programático** (caso de uso primário): `init-tree --auto` chama passando lista de folhas e o root code.
- **Manual** (caso opt-in): usuário roda `spec-tree {raiz}` em uma árvore já inicializada por `init-tree` (sem `--auto`) pra ganhar a Q&A batch. Útil quando o usuário quer escrever todas as specs juntas antes de começar a codar, mesmo sem rodar o ciclo full.

## Pré-requisitos

- `GOD/` na versão atual.
- `init-tree {raiz}` já rodou (existem folhas em `GOD/tasks/{cod}/` com `phase: initialized`).
- MCP Atlassian autenticado (pra ler descrição/Jira de cada folha).
- `specs_path` configurado em `GOD/config.md`.

## Flags

- `--target jira/slack/file/stdout/clipboard` *(opcional)* — após escrever cada spec canônica, publica adicionalmente no destino (delega pra `publish-spec`).
- `--debug` *(v10.6)* — log opt-in.

## Instruções

Quando esta skill é invocada, execute os passos **na ordem**:

### 1. Receber input

- **Modo programático** (de `init-tree --auto`): recebe `{root_code, leaves: [cod1, cod2, ...]}`.
- **Modo manual**: receber `{raiz}` (Epic/Story). Resolver `leaves` lendo `GOD/tasks/*/status.md` filtrando por descendentes da raiz e `phase: initialized`. Se nenhuma folha qualifica → encerrar com "Nenhuma folha em `phase: initialized` descendente de {raiz} — rode `init-tree {raiz}` primeiro ou veja `status`".

### 2. Carregar contexto de cada folha

Pra cada `cod` em `leaves`:

1. Ler `GOD/tasks/{cod}/status.md` (extrair `profile`, garantir `phase: initialized`).
2. **Buscar dados do Jira** via `getJiraIssue({cod})`: título, descrição, tipo, status, labels, links.
3. **Detectar input visual (Figma)** — se a descrição tem link de Figma, anotar pra análise posterior.
4. Guardar em memória: `leaf_context[cod] = {jira_data, profile, input_bruto}`.

> Pulando folhas com `profile: trivial` — trivial não precisa de spec (init label só, segue direto pro implement). Anotar como "skipped: trivial" no relatório final.

### 3. Análise heurística em batch

Pra cada folha não-trivial, rodar a heurística do `spec` v10.1 (carregar `sub-skills/spec/heuristics.md`):

- Detectar **excessos** (HOW dentro do WHAT — pseudo-código, framework leak, schema técnico).
- Detectar **gaps** (NFRs ausentes, ator não nomeado, cenários de erro).

Armazenar resultado por folha: `heuristics[cod] = {excesses: [...], gaps: [...]}`.

### 4. Agrupar perguntas por tema

A partir dos gaps detectados, classificar cada folha em **temas** com heurística simples:

- **auth** — folhas cujo título/descrição mencionam login, sessão, JWT, OAuth, role, permission.
- **payments** — pagamento, billing, boleto, cartão, PIX, refund, settle.
- **ui** — tela, componente, modal, layout, design, Figma.
- **data** — schema, migration, ETL, ingest, query, índice.
- **integration** — webhook, API externa, MCP, Slack/Jira/etc.
- **infra** — deploy, CI, env, secret, infra-as-code.
- **outros** — fallback.

Uma folha pode estar em múltiplos temas. Gerar lista de perguntas agrupadas:

```
{
  "auth": {
    "leaves": ["PROJ-101", "PROJ-104"],
    "common_questions": ["Quem é o ator? SLA de autenticação? Cenários de senha errada?"],
    "per_leaf_questions": {"PROJ-101": [...], "PROJ-104": [...]}
  },
  "payments": {...},
  ...
}
```

> **Heurística de agrupamento**: se 2+ folhas batem no mesmo tema, gerar 1 bloco de perguntas comuns + perguntas específicas só pra folhas individuais. Se só 1 folha bate no tema, ainda criar bloco — mas reconhecer que é só 1.

### 5. Sessão de Q&A unificada

Apresentar em ordem de tema:

```
🌲 spec-tree {raiz} — Q&A unificada (4 folhas, 3 temas)

━━━ AUTH (afeta PROJ-101, PROJ-104) ━━━

Perguntas comuns:
1. Quem é o ator humano? (login: usuário final; admin: admin do painel)
2. SLA esperado de resposta?

Perguntas específicas:
PROJ-101 — Cenário de "primeiro login após reset"?
PROJ-104 — A/B test ativo? Qual variante usar como spec?

[usuário responde inline]

━━━ PAYMENTS (afeta PROJ-102) ━━━
...
```

Coletar respostas estruturadas: `answers[cod][question_id] = resposta`.

**Critério pra chamar humano vs proceder com default:**
- **Sempre perguntar:** ator humano, NFRs com unidade (SLA, throughput, capacidade), cenários de erro críticos, ACs ambíguos.
- **Pode assumir default + marcar pra confirmação no PR:** convenções de naming, formato de mensagem de erro, label de UI.

### 5.5. Feature split inline (opcional)

Se durante o Q&A o usuário perceber que uma folha é uma feature inteira (não uma task), oferecer split: "PROJ-103 parece feature — quebrar em N subtasks?". Aceita ou recusa. Aceito → criar pastas adicionais em `GOD/tasks/` + voltar à fase de Q&A pra novas subtasks. (Manter simples na v12 — split pesado vira `init-tree` separado.)

### 6. Gerar cada spec individual

Pra cada folha (em paralelo onde fizer sentido, ou sequencial pra reduzir contexto):

1. Construir input rico: `jira_data + heuristics + answers_aplicáveis`.
2. Aplicar template idêntico ao de `spec` (v10.1) — `## Input bruto`, `## Objetivo`, `## Não-objetivos`, `## REQs`, `## ACs`, `## NFRs`, `## Cenários`, `## Notas técnicas`, frontmatter completo (`profile`, `applicable_rules` se aplicável).
3. Escrever em `<specs_path>/tasks/{cod}.md` com `spec_version: 1`.
4. Atualizar `status.md` da folha: `phase: specified`, `spec_path: <specs_path>/tasks/{cod}.md`, `spec_version_consumed: null` (ainda não consumida por plan).

### 7. Self-validação + review

Pra cada spec gerada:

1. Rodar `sub-skills/_lib/validate_spec.py` — lint estrutural (REQ tem AC, IDs estáveis, palavras-tabu). Corrigir trivial inline (auto-numerar IDs, mover framework leak pra "Notas técnicas").
2. Delegar pra `review --spec --subagent` em batch (uma chamada Agent por spec, paralelizadas).
3. Se review reprovar com `must_fix`: tentar corrigir uma vez baseado no feedback. Se ainda reprovar → marcar folha como "spec rejeitada" e listar no relatório final pra usuário rever manualmente. **Não interromper o batch inteiro** por uma spec ruim.

### 8. Reportar

```
✅ spec-tree {raiz} concluído!

Specs geradas (4):
  PROJ-101 → <specs_path>/tasks/PROJ-101.md (phase: specified) ✅ review OK
  PROJ-102 → <specs_path>/tasks/PROJ-102.md (phase: specified) ✅ review OK
  PROJ-103 → <specs_path>/tasks/PROJ-103.md (phase: specified) ⚠️ review com 1 warning
  PROJ-104 → <specs_path>/tasks/PROJ-104.md (phase: specified) ❌ review reprovou — revisar manual

Trivial puladas: nenhuma
Tema com mais perguntas: auth (4 perguntas)

💡 Próximos passos:
  • Se chamado por init-tree --auto: loop plan → implement → pack-up vai começar agora.
  • Se modo manual: rode `plan {cod}` por folha (ou re-rode `init-tree {raiz} --auto` pra encadear o ciclo completo).
```

### 9. Devolver controle ao chamador

Se invocada programaticamente por `init-tree --auto`, retornar JSON com:

```json
{
  "ok": true,
  "specs_generated": ["PROJ-101", "PROJ-102", "PROJ-103"],
  "specs_rejected": ["PROJ-104"],
  "specs_skipped_trivial": [],
  "next_action": "implement_loop"  // ou "halt_for_manual_review" se algum rejected
}
```

`init-tree --auto` decide: se houver `specs_rejected`, **parar o loop** e chamar humano (decisão da IA — quality gate). Se tudo OK, prosseguir pro loop de implement.

---

## Guard-rails

- **Esta skill não toca em git.** Igual a `spec` single — escreve só arquivos `.md`.
- **Esta skill não chama `plan`/`implement`/`pack-up`.** Apenas gera specs + atualiza status.
- **Esta skill não escreve em `GOD/knowledge.md`.**
- **Esta skill não substitui a `spec` single-task.** Pra uma folha só, sempre use `spec {cod}` (Q&A focada).
- **Esta skill não força o usuário a responder tudo.** Se o usuário abandona o Q&A no meio, salvar progresso parcial (specs geradas até aquele ponto) e retornar erro pro `init-tree --auto` — que vai chamar humano.
- **Esta skill respeita perfil trivial.** Folhas com `profile: trivial` são puladas silenciosamente — não precisam de spec.
- **Falha em uma spec não interrompe o batch.** Reporta no final, decide-se no chamador se segue ou para.

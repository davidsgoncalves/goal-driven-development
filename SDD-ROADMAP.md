# SDD Roadmap — Evolução do GOD para Spec-Driven Development

> Plano técnico de evolução do framework GOD, do estado atual até virar **SDD de verdade**, dentro do escopo da realidade onde ele é usado: time pequeno, releases diários, escopo que muda, arquitetura assistida (não imposta), spec é lei quando chega ao dev.

> **Status:** Fases 1 (v6), 2 (v7) e 3 (v8) entregues. Patch v8.1: peer-review via subagent isolado nos 3 modos do `review`.
>
> **Resumo das fases:**
> - v6: spec extraída em path configurável.
> - v7: hooks de propagação ativa, review semântico profundo, freshness check, `spec --review-feedback`, `publish-spec`.
> - v8: rastreabilidade AC × validação via comentário `// covers: AC-X` + `coverage.md`; `coverage` skill nova; `pack-up` injeta tabela no PR; `review --execution` ganha eixo de cobertura.
> - **v8.1 (patch retrocompatível):** os 3 modos do `review` (`--spec`, `--plan`, `--execution`) passam a executar via subagent (`Explore` pra spec/plan; `general-purpose` pra execution). Elimina viés de auto-validação ("eu escrevi isso, parece bom"). Sem migration — VERSION continua `v8`.
>
> Próxima: Fase 4 (v9) — Spec viva (versionamento de mudança de escopo, feature spec eterna + delta + propagação).

## Como ler este documento

Cada fase é uma **versão entregável** do GOD. Você pode parar em qualquer ponto — todas as fases entregam valor por si só. As fases 1–4 são executáveis solo, sem depender de adoção organizacional. As fases 5–6 dependem de decisões externas (princípios documentados, equipe co-autorando spec) e só fazem sentido se houver mandato.

Não execute fases fora de ordem. Cada uma assume os artefatos das anteriores como pré-requisito.

## Premissas do plano

- **Spec é lei** quando chega ao dev. O foco do GOD é produzir e consumir spec com qualidade — não enforçar spec sobre código já escrito.
- **Arquitetura é assistida**, não imposta. Não há constitution rígida; há advisor que sugere, dev decide.
- **Adoção solo é o caso primário**. Cada fase precisa entregar valor pro dev sozinho. Multi-autor é capacidade opcional.
- **Releases diários, escopo muda**. Spec é viva e versionada, não congelada. Mudança de escopo é primeira-classe, não acidente.
- **Contexto BE forte em testes unitários, FE sem testes automatizados**. Rastreabilidade AC↔teste é leve onde dá automação; AC visual pode ser "validação manual em staging" sem virar mentira.

## Mapa das fases

| Fase | Versão | Nome | Status | Dependência organizacional |
|------|--------|------|--------|---------------------------|
| 0 | v5 | Goal-oriented | superado | — |
| 1 | v6 | Spec extraída | **entregue** | Nenhuma |
| 2 | v7 | Spec validável | **entregue** | Nenhuma |
| 3 | v8 | AC rastreável | **entregue** | Nenhuma |
| 4 | v9 | Spec viva | a fazer | Nenhuma |
| 5 | v10 | Architecture advisor | a fazer | Baixa (preencher principles) |
| 6 | v11 | Multi-autor | a fazer | Alta (mandato + equipe) |

---

## Fase 0 — Estado atual (v5)

Para ancorar o ponto de partida:

- `description.md` carrega input bruto + enriquecimento + Q&A misturados
- `plan.md` carrega branch + arquivos + passos + critérios de aceitação misturados
- Não existe spec separada
- Não existe rastreabilidade AC↔teste
- `learned-patterns.md` é o mais próximo de "constitution", mas é regra de código, não princípio de produto

**Diagnóstico:** o framework atual é **goal-oriented**, não spec-driven. A spec existe na cabeça do dev e em pedaços do plan, mas não tem forma própria.

---

## Fase 1 — Spec extraída (v6) — ENTREGUE

### O que entrega
- Novo artefato `<specs_path>/{cod}.md` como documento próprio (FORA de `GOD/`, configurável)
- Novo arquivo `GOD/config.md` com `specs_path` (default `docs/specs/`, perguntado no install)
- Nova sub-skill `spec`, posicionada **entre `init` e `plan`** no fluxo
- `description.md` volta a ser só input bruto do usuário (sem enriquecimento)
- `plan.md` perde "Critérios de aceitação"; passa a referenciar a spec como entrada
- `review` ganha modo `--spec` com verificações estruturais e de conteúdo
- `pack-up` anexa link da spec no PR description automaticamente
- Nova fase `specified` no enum de `phase` (status.md)
- Novo campo `spec_path` em `status.md`

### Decisões tomadas durante a implementação

1. **Spec mora FORA do GOD/.** A spec é artefato canônico do produto, não workflow individual. Fica em `<specs_path>/` (configurável via `GOD/config.md`). Permite que dev solo committe a spec sem committar o GOD/. Em multi-project, basta apontar `specs_path` pra um repo dedicado de specs.
2. **`specs_path` é root do repo de specs**, não pasta direto. GOD escreve em `<specs_path>/tasks/<cod>.md`. Subpastas `domains/` e `flows/` ficam reservadas pra skills futuras (feature specs eternas, fluxos cross-feature) — não populadas pela v6.
3. **Setup interativo do repo de specs no install** apresenta 4 cenários calibrados pelo contexto (single-project vs workspace multi-project): pasta no repo, repo dedicado ao lado, path absoluto livre, ou outro relativo. Detecta se a pasta existe, oferece criar; se não é git, oferece `git init` pra repo separado. Cria README mínimo do repo de specs explicando estrutura e convenções.
4. **v6 só implementa task spec autocontida.** Cada task tem sua própria spec descritiva em `tasks/<cod>.md`. A distinção feature spec eterna ↔ task spec descartável (delta + propagação) entra na v9 (Fase 4). Tentar trazer já na v6 introduziria mecânica de propagação sem suporte.
5. **Migração v5→v6 não toca tasks ativas.** Tasks com `phase: planned` ou posterior continuam no fluxo v5 até `packed-up`. Apenas novas tasks (init pós-migração) usam o fluxo v6.

### Estrutura do `spec.md`

```markdown
---
spec_version: 1
created_at: ...
updated_at: ...
---

# SPEC-{cod} — {título}

## Objetivo
Uma frase do problema que se está resolvendo.

## Não-objetivos
O que está fora de escopo (explícito).

## Requisitos

### REQ-001: {nome}
**WHEN** {contexto} **THEN** o sistema **SHALL** {comportamento}.

#### Critérios de aceitação
- AC-001.1: ...
- AC-001.2: ...

### REQ-002: {nome}
...

## Cenários
- Happy path: ...
- Edge cases: ...
- Erros: ...

## NFRs
- Performance: ...
- Segurança: ...
- Acessibilidade: ...
- Observabilidade: ...
```

### Formato dos ACs
- **EARS leve** ("WHEN [contexto] THEN o sistema SHALL [comportamento]")
- **Não Gherkin** — Gherkin pede ferramental Cucumber/BDD, custo organizacional sem retorno na realidade atual
- Gherkin entra apenas se vocês adotarem testes de aceitação BDD futuramente

### Modificações nas sub-skills

| Skill | Mudança |
|-------|---------|
| `init` | Sem mudança — continua só salvando input bruto |
| `spec` (NOVA) | Faz Q&A focada em **escopo, ACs, cenários, NFRs**. Proibido falar de implementação. Roda `review --spec` antes de finalizar |
| `plan` | Perde Q&A de escopo (já feito na spec). Foca em arquitetura, arquivos, passos. Lê `spec.md` como input |
| `implement` | Consulta `spec.md` durante o código (leitura constante dos ACs) |
| `pack-up` | Anexa link do `spec.md` no PR description automaticamente |

### Pré-requisitos
- **Técnicos:** v5 instalado. Migração v5→v6 (extrair ACs do `plan.md` das tasks ativas, mover pra `spec.md`).
- **Organizacionais:** zero. Uso solo, ninguém precisa adotar nada.

### Esforço de build
~2-3 dias de trabalho focado no framework.

### Ganho
- Disciplina mental forçada: WHAT vs HOW separados em arquivos
- Spec consumível por humano externo (mesmo que ninguém leia hoje)
- Base pronta pras fases seguintes
- "É SDD de verdade" no sentido literal: spec é artefato, não pedaço de doc

### Risco
Baixo. Dev é o usuário primário e decide.

---

## Fase 2 — Spec validável (v7) — ENTREGUE

### O que entrega
- **`review --spec` profundo** — verificações semânticas além do lint da v6: cobertura description→spec profunda, cenários cobrem ACs, NFRs adequados ao tipo de feature, ortogonalidade de ACs, edge cases óbvios. Flag `--quick` skipa semântica e roda só lint
- **Hooks `before spec` e `after spec`** — adicionados ao `hooks.md`. `after spec` é caso de uso típico pra publicar a spec recém-criada em Jira/Slack
- **Frontmatter da spec** ganha `last_published_at`, `published_to`, `feedback_cycles` (todos opcionais)
- **`status.md` da task** ganha `spec_version_consumed` — usado pra freshness check
- **Modo `spec --review-feedback`** — opt-in. Incorpora feedback do stakeholder (Jira/Slack/conversa) à spec, incrementa `spec_version`. Limite de 2 ciclos automáticos consecutivos antes de exigir conversa síncrona
- **Sub-skill nova `publish-spec`** — publicação manual da spec em targets configuráveis (`jira`, `slack`, `stdout`, custom). Aceita `--target` (repetível) e `--dry-run`
- **Freshness check em `plan` e `implement`** — comparam `spec_version` atual vs `spec_version_consumed`. Se diferentes, alertam o usuário antes de prosseguir

### Decisões tomadas durante a implementação

1. **`spec --review-feedback` só em `phase: specified`.** Tasks que já passaram pro `plan`/`implement` exigem mecanismo diferente (v9: `update-spec` com propagação delta).
2. **Contador `feedback_cycles` reseta quando `plan` ou `implement` rodam.** Evita ping-pong eterno mantendo o histórico de ciclos por sessão de iteração.
3. **`publish-spec` não roda hook `after spec`.** Pra evitar dupla publicação. Hook só dispara via `spec`/`spec --review-feedback`.
4. **Freshness check nunca bloqueia, sempre pergunta.** Apresenta opções (rodar update-plan, prosseguir mesmo assim, abortar). Bloqueio rígido seria fricção sem ganho.
5. **Verificações semânticas do review nunca causam Reprovado.** São heurísticas sujeitas a falsos positivos — viram "Ajustes necessários" no máximo. Apenas falhas estruturais ou lint sistêmico causam Reprovado.

### Modificações nas sub-skills

| Skill | Mudança |
|-------|---------|
| `review` | Ganha 3º modo. Atuais: `--plan` (description vs plan) e `--execution` (plan vs código). Novo: `--spec` (description vs spec) |
| `spec` | Integra `review --spec` antes de finalizar |
| Hook `after spec` | (opcional) formata spec curta + publica no canal escolhido (Jira comment, Slack, Notion) |

### Verificações do `review --spec`
- Cobertura de escopo (a spec cobre tudo o que a description pede?)
- Ausência de contradição entre requisitos
- **Não-vazamento de implementação** (ex: "essa AC menciona React, isso é HOW, mover pro plan")
- ACs testáveis (não vagos como "deve ser rápido" → exigir métrica)

### Pré-requisitos
- **Técnicos:** Fase 1 (v6).
- **Organizacionais:** zero pra valor solo. Pra valor de validação externa, alguém (PM/UX) precisa estar disposto a ler ~1 página em 5 minutos. Pedido **muito menor** que "PM escreve spec".

### Esforço de build
~1-2 dias. O modo novo do review é o trabalho real; hook é trivial.

### Ganho
- Catch de ambiguidade automático (lint da spec)
- Loop de validação leve com PM/UX **sem custo organizacional**
- Quando PM/UX engajarem, ferramenta já existe

### Risco
Zero internamente. Externo depende de PM/UX, mas tolera silêncio.

---

## Fase 3 — AC rastreável (v8) — ENTREGUE

### O que entrega
- **Sub-skill `coverage`** — parseia comentários `// covers: AC-X` em testes (regex unificada cobrindo TS/JS/Ruby/Python/Go/Java/C#) + lê `coverage.md` (validações manuais) → gera matriz AC × validação. Formatos `markdown`, `terminal`, `json`. Tolerante por design — ACs órfãos viram alerta visual, nunca falha de processo.
- **`implement` ganha passo 5.5** — após escrever testes, anota `// covers: AC-X` no comentário acima. Pra ACs sem teste (FE), oferece registrar em `coverage.md` como validação manual. Honesto: nunca finge cobertura.
- **`pack-up` ganha passo 4.5** — chama `coverage` antes do PR, alerta sobre ACs órfãos (não bloqueia), injeta tabela markdown no PR description.
- **`review --execution` ganha eixo de cobertura** — cruza ACs da spec com matriz da `coverage`. ACs órfãos viram "Ajustes necessários", nunca "Reprovado".
- **Arquivo opcional `GOD/tasks/{cod}/coverage.md`** — criado sob demanda. Contém validações manuais (input do usuário) + seção "Matriz" regenerada pela skill (cache).

### Decisões tomadas durante a implementação

1. **Cobertura é só o que está explicitamente anotado.** Inferir cobertura por nome de teste (`it("rejects empty phone")` sem comentário) é proibido — leva a falsos positivos. Ausência de comentário = AC não rastreado.
2. **Comentário inline (não arquivo separado de mapeamento).** Mantém amarra perto do código, sobrevive a refator que move teste de pasta, baixa fricção pra dev.
3. **`coverage.md` mistura input humano e cache automático.** Seção `## Validações manuais` é input (o dev escreve); seção `## Matriz` é regenerada pela skill a cada execução. Limites claros impedem conflito.
4. **`pack-up` alerta mas não bloqueia.** Default tolerante. ACs órfãos aparecem como ⚠️ no PR description; decisão de prosseguir fica do dev/revisor. Não há mecanismo de bloqueio rígido — seria fricção sem ganho proporcional, e o GOD é skill local do dev (não roda em CI), então enforcement automático fora desse contexto não faz parte do escopo.
5. **AC órfão nunca causa Reprovado no review.** Vira "Ajustes necessários" — pode ser legítimo (validação externa, pendente de manual). Decisão é do dev/revisor com informação visível.

### Modificações nas sub-skills

| Skill | Mudança |
|-------|---------|
| `spec` | Schema do `spec.md` exige IDs estáveis (já existe na Fase 1, agora vira **enforced**) |
| `implement` | Ao escrever teste, **anota qual AC ele cobre** (comentário leve no teste OU registro em `GOD/tasks/{cod}/coverage.md`) |
| `pack-up` | Roda `coverage` antes do PR. Se AC sem nenhuma validação, **alerta** (não bloqueia). Decisão fica do dev |
| `review --execution` | Ganha eixo extra: além de "plan foi cumprido?", "todos os ACs estão cobertos por algum tipo de validação?" |

### Tipos de validação aceitos
- **BE:** link AC → teste unitário/integração (comentário no teste estilo `// covers: AC-001.2, AC-001.3`)
- **FE:** link AC → "validação manual em staging por [PM/UX/dev]" — registrado explicitamente, não fingido como automatizado

### Pré-requisitos
- **Técnicos:** Fase 1 (v6).
- **Organizacionais:** zero. Validação manual em staging é honesta, não simulada.

### Esforço de build
~2-3 dias. Parte difícil é o link leve teste↔AC sem virar burocracia. Sugestão: comentário parseado por regex.

### Ganho
- "Esqueci de testar isso" deixa de acontecer
- PR description gerado pelo `pack-up` ganha tabela de cobertura — alavanca pra PR review e histórico
- Quando QA contratar (se contratar), a infra já existe

### Risco
Baixo se o link AC↔teste for **leve** (comentário). Se virar formulário, vira burocracia e morre.

---

## Fase 4 — Spec viva (v9)

### Por que é crítico
Em ambiente de releases diários e escopo que muda, a mudança hoje é **invisível**: PM muda de ideia, dev refaz, ninguém registra. Em SDD canônico isso é catastrófico (spec congelada vira mentira). Em SDD adaptado, **mudança de spec é primeira-classe**.

### O que entrega
- Spec versionada: cada mudança na `spec.md` gera entrada em `spec-changelog.md`
- Skill `update-spec` (paralela do `update-plan`): formaliza mudança de escopo
- `pack-up` registra qual **versão da spec** foi entregue (hash ou número)

### Modificações nas sub-skills

| Skill | Mudança |
|-------|---------|
| `spec.md` | Ganha frontmatter com versão (v1, v2, ...) e timestamp |
| `update-spec` (NOVA) | Pergunta motivo da mudança, edita spec, registra delta no changelog |
| `implement` | Checa se spec mudou desde o último consumo. Se sim, reabre código que tocava nos ACs alterados |
| `pack-up` | Carimba versão da spec entregue no PR |

### Pré-requisitos
- **Técnicos:** Fase 1 (v6). Idealmente Fase 3 (v8), pra mudança de AC saber qual teste invalida.
- **Organizacionais:** zero. É controle interno.

### Esforço de build
~2 dias. Maior parte é o `update-spec` e o link com `update-plan` existente.

### Ganho
- "Mudou no meio" vira evento consciente, não acidente
- Histórico de mudanças por feature — alavanca de retrospectiva
- Argumento concreto: **"SDD não engessa, torna mudança visível"** vira fato, não promessa

### Risco
Baixíssimo. Usado só quando precisa.

---

## Fase 5 — Architecture advisor (v10)

### Adaptação ao cenário
Arquitetura é negociável, praticamente assistida. Então:
- Arquitetura **NÃO** é gate. É advisor.
- `plan` lê `architecture.md` e diz: "essa solução desvia do padrão atual em X. Você quer (a) refatorar, (b) preservar o desvio, (c) preservar o padrão?"
- Decisão fica do dev. GOD nunca trava.

### O que entrega
- `GOD/principles.md` — princípios mínimos do projeto (curtos, 5-10 bullets)
- `GOD/architecture.md` — padrões arquiteturais "preferidos" mas negociáveis
- `plan` consulta ambos e **sinaliza desvios sem bloquear**
- Modos `--refactor` / `--preserve` no `plan` modulam tom da sugestão

### Modificações nas sub-skills

| Skill | Mudança |
|-------|---------|
| `install` | Cria `principles.md` e `architecture.md` (templates vazios) |
| `plan` | Ganha passo: ler principles + architecture, consultar contra a feature, gerar bloco "Considerações arquiteturais" com sugestões |
| `plan` | Aceita flag `--refactor` ou `--preserve` |
| `learned-patterns.md` | Continua escopo de **código**; principles/architecture cobrem **estrutura** |

### Pré-requisitos
- **Técnicos:** Fase 1 (v6). Idealmente Fase 4 (v9) — porque mudança arquitetural é mudança de spec ampliada.
- **Organizacionais:** baixo. Preencher `principles.md` com 5-10 princípios e `architecture.md` com 3-5 padrões. Trabalho de uma tarde.

### Esforço de build
~2 dias. Templates + integração no `plan`.

### Ganho
- Decisões arquiteturais ficam **explícitas e auditáveis** mesmo sendo flexíveis
- Onboarding de novo dev fica trivial (lê principles + architecture)
- Quando refatoração entra em pauta, GOD ajuda a decidir o que preservar e o que descartar

### Risco
Baixo se principles for curto (10 bullets, não 10 páginas).

---

## Fase 6 — Multi-autor (v11)

### Quando faz sentido
**Apenas** se a empresa decidir entrar no jogo. Solo, esta fase é overhead. Faça quando o mandato chegar — não antes.

### O que entrega
- Workflow de spec colaborativa: PM/UX/dev podem todos contribuir
- Sub-skills: `draft-spec` (input = briefing PM), `refine-spec` (input = draft), `validate-spec` (output = approval log)
- Spec assinada por múltiplos autores

### Modificações nas sub-skills

| Skill | Mudança |
|-------|---------|
| `spec` | Vira orquestradora das 3 sub-skills |
| `draft-spec` (NOVA) | Aceita briefing oral/curto do PM e estrutura como spec rascunho |
| `refine-spec` (NOVA) | Dev passa pelo rascunho, identifica gaps técnicos |
| `validate-spec` (NOVA) | Gera link de validação (Jira/Slack/Notion), registra aprovações |
| `status.md` | Ganha campo `approvals: { product: yes, ux: yes, eng: yes }` |

### Pré-requisitos
- **Técnicos:** Fases 1, 2, 3 no mínimo.
- **Organizacionais:** altos.
  - PM topando dar briefing estruturado (mesmo oral, transcrito)
  - UX topando validar ACs visuais
  - Talvez QA contratado pra validar ACs em staging
  - Tempo de equipe alocado pro processo

### Esforço de build
~1 sprint inteiro (5-7 dias). Fase mais complexa.

### Ganho
- SDD verdadeiramente cross-funcional
- Spec como contrato entre time de produto e engenharia
- Auditoria de "quem disse o quê" pra cada feature

### Risco
Alto. Esta fase **morre** se a empresa não comprar antes.

---

## Como decidir até onde ir

### Rota A — SDD solo robusto (sem mandato)
**v6 + v7 + v8 + v9.** Pare. SDD adaptado e funcional, sem dependência de ninguém. Esforço total: ~2 semanas distribuídas em 4 releases.

### Rota B — SDD solo + advisor arquitetural
**v6 + v7 + v8 + v9 + v10.** Adiciona principles e architecture. +2-3 dias.

### Rota C — SDD integral cross-funcional
**Tudo até v11.** Só comece v11 com mandato real, não com promessa.

### Recomendação prática
Comece pela **v6** independentemente do que rolar nas conversas organizacionais. É a fase de maior ROI por esforço. Sem ela, nenhuma das outras é possível, e ela vale por si só. Faça **v7** logo em seguida pela alavanca de "publicar spec no Jira" — vira argumento concreto pra qualquer conversa futura.

---

## Melhorias transversais (não são fases)

Capacidades aplicadas a múltiplas skills sem precisar de versão própria. Aparecem como patches retrocompatíveis (sem migration).

| Patch | O que faz | Aplicado em |
|-------|-----------|-------------|
| **v8.1 — peer-review via subagent** | `review --spec/--plan/--execution` delegam pra subagent isolado (`Explore` ou `general-purpose`). Elimina viés de auto-validação | `sub-skills/review/SKILL.md` |

---

## O que deliberadamente NÃO está incluído

| Excluído | Motivo |
|----------|--------|
| Constitution rígida com gate | Arquitetura é negociável; constitution canônica é incompatível |
| Traceability formal AC↔task↔teste com IDs hierárquicos | Overhead que a realidade não justifica. Comentário em teste resolve 90% pelo custo de 5% |
| Multi-agent personas (PM agent, Architect agent, QA agent) | Sem QA na empresa, e PM não vai virar agente. Adicionar pré-tempo é teatro |
| Spec como contrato legal/contratual | Produto B2C sem cliente B2B com SLA. Spec é interna, não jurídica |
| Compliance gate / auditoria automatizada | Produto não regulado pesado |
| Geração automática de testes a partir da spec | Prematuro. Qualidade ainda mediana, introduz risco de teste-fantasma |

Esses itens podem entrar como v12+ se algum dia forem relevantes. Não devem pesar na decisão atual.

---

## Resumo executivo

Para o GOD virar SDD de verdade no escopo atual, o caminho mínimo é 4 fases incrementais:

1. **v6 — Extrair spec** (`spec.md` separada, EARS leve, sub-skill nova)
2. **v7 — Validar spec** (review --spec, publicação opcional)
3. **v8 — Rastrear ACs** (ID estável, cobertura por teste ou validação manual)
4. **v9 — Versionar spec** (mudança de escopo como evento de primeira-classe)

Tudo solo, sem dependência organizacional. Architecture advisor (v10) e multi-autor (v11) são extensões que dependem de decisões da empresa e devem ser implementadas apenas com sinal claro.

A primeira fase concreta a iniciar é a v6. As demais derivam dela.

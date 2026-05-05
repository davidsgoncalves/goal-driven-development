# SDD Roadmap — Evolução do GOD para Spec-Driven Development

> Plano técnico de evolução do framework GOD, do estado atual até virar **SDD de verdade**, dentro do escopo da realidade onde ele é usado: time pequeno, releases diários, escopo que muda, arquitetura assistida (não imposta), spec é lei quando chega ao dev.

> **Status:** Fases 1 (v6), 2 (v7), 3 (v8), 4 (v9) e 5 (v10) entregues. Patches transversais: v8.1 (peer-review via subagent), v8.2 (default target do publish-spec configurável), v10.1 (spec absorve qualidades da god-spec — unificação), v10.2 (scripts Python pra processos robóticos + skill `doctor` + lazy templates + compactação), v10.3 (peer-review opt-out via config), v10.4 (context blob + quebrar review em 3), v10.5 (batch consolidado no pack-up + README reescrito).
>
> **Resumo das fases:**
> - v6: spec extraída em path configurável.
> - v7: hooks de propagação ativa, review semântico profundo, freshness check, `spec --review-feedback`, `publish-spec`.
> - v8: rastreabilidade AC × validação via comentário `// covers: AC-X` + `coverage.md`; `coverage` skill nova; `pack-up` injeta tabela no PR; `review --execution` ganha eixo de cobertura.
> - **v8.1 (patch retrocompatível):** os 3 modos do `review` (`--spec`, `--plan`, `--execution`) passam a executar via subagent. Elimina viés de auto-validação.
> - **v8.2 (patch retrocompatível):** `publish-spec` aceita default em `GOD/config.md`.
> - v9: spec-first (inverte ordem `init→spec` para `spec→init`) + spec viva (`update-spec` + changelog).
> - v10: Architecture advisor (principles/architecture configuráveis) + Domain rules (`<dominio>.md` com BRs em IDs derivados do frontmatter, agnóstico ao projeto). `spec` sugere `applicable_rules`, `implement` sugere `// rule: BR-X`, `pack-up` injeta tabela de BRs no PR.
>
> Próxima: v10.5 — skills `rules` (criação interativa de BR) e `audit-rules` (varredura de BRs órfãs / código apontando pra BR removida). Ou Fase 6 (v11) — Multi-autor (depende de mandato organizacional).

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
| 4 | v9 | Spec-first + spec viva | **entregue** | Nenhuma |
| 5 | v10 | Architecture advisor + Domain rules | **entregue** | Baixa (preencher principles + domains opcionais) |
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

## Fase 4 — Spec-first + spec viva (v9) — ENTREGUE

### Por que reformular

Duas mudanças entram juntas porque são facetas do mesmo princípio: **spec é o artefato canônico do trabalho, não rascunho paralelo**.

1. **Inversão da ordem (`init→spec` vira `spec→init`).** Hoje `init` precede `spec` — resíduo da v5 goal-oriented, antes da spec virar artefato próprio na v6. Em SDD canônico, spec é gate: precede branch e setup de execução. Spec rejeitada não deveria deixar branch órfã no repo.
2. **Spec viva.** Em ambiente de releases diários e escopo que muda, mudança hoje é invisível — PM muda de ideia, dev refaz, ninguém registra. Em SDD canônico isso é catastrófico (spec congelada vira mentira). Em SDD adaptado, mudança de spec é primeira-classe.

Combinadas, fazem da spec o gate de entrada (precede commit) e de saída (versão entregue carimbada no PR).

### O que entrega

**Inversão da ordem:**
- `spec` precede tudo. Lê Jira/input bruto, gera `<specs_path>/tasks/{cod}.md` direto, sem precisar de branch. Captura o input bruto que antes morava em `init` (`description.md`).
- `init` se reposiciona: roda **depois** de `spec`. Cria branch + `status.md` (`phase: planned`) apontando pra spec já existente.
- 3 perfis de task com fluxos calibrados (evitam cerimônia injustificada):
  - **Trivial** (copy, typo, dep upgrade): `init --type=trivial` pula `spec` inteira.
  - **Normal**: `spec --quick` (sem publish-spec) seguido de `init`.
  - **Crítica**: `spec` → `publish-spec` → aguarda validação stakeholder → `init`.
- Detecção heurística de perfil (description curta + sem stakeholder = trivial; longa + Jira rico = crítica), com flag de override.
- `init-tree` adapta-se: roda specs em batch, pausa pra aprovação, depois cria branches.

**Spec viva:**
- `<specs_path>/tasks/{cod}.md` ganha `spec_version: N` (já parcial da v6, agora consolidado) e timestamps de criação/atualização.
- Sub-skill `update-spec` (paralela do `update-plan`): formaliza mudança de escopo pós-`init`. Q&A do motivo, edita spec, bumpa `spec_version`, escreve delta em `<specs_path>/tasks/{cod}-changelog.md`.
- `implement` ganha freshness check estendido: se `spec_version` mudou desde último consumo, lista ACs alterados, cruza com `coverage.md` (v8) pra apontar arquivos/testes afetados, oferece reabrir passos.
- `pack-up` carimba `spec_version_delivered` em `status.md` e injeta no PR description.

### Decisões tomadas durante a implementação

1. **`init` mantido com mesmo nome.** Cabeça muscular do usuário continua, só o escopo muda (de "criar pasta + capturar input" para "criar estrutura de execução pós-spec"). Renomear pra `start` foi avaliado e rejeitado — quebra docs e gera ruído sem ganho real.
2. **Changelog em arquivo separado:** `<specs_path>/tasks/{cod}-changelog.md`. Diff fica limpo, spec não cresce indefinidamente, fácil de listar histórico.
3. **Detecção de perfil sempre confirma.** Heurística sempre roda (mesmo sem ambiguidade aparente) e propõe ao usuário, custo baixo evita pular publish-spec em task crítica detectada como normal. Flag `--type=normal|critical` força sem heurística.
4. **`--type=trivial` é exclusivo do `init`.** A skill `spec` não aceita `--type=trivial` — tentar gerar "spec mínima" pra typo polui o repo de specs. Trivial pula spec inteira.
5. **Migração v8→v9 sem migrator automático.** Tasks com `phase: planned` ou posterior continuam fluxo v8 até `packed-up`. Apenas tasks novas (spec pós-v9) entram no fluxo invertido. Spec da v9 detecta `GOD/tasks/{cod}/description.md` legacy e lê de lá pra retrocompat.
6. **`description.md` deixa de existir em tasks v9.** Input bruto vira seção `## Input bruto` da própria spec. Tasks legacy mantêm o arquivo intacto.
7. **Hook `after spec` continua sempre disparando** (independente do perfil). Perfil afeta apenas a sugestão final ao usuário sobre rodar `publish-spec` manual. Mudar comportamento do hook por perfil quebraria expectativa de quem já configurou.
8. **`init-tree` chama `spec` em modo `batch`** (não chama mais `init` direto). Modo batch pula Q&A interativa, pula review, pula hook `after spec`, marca spec com `draft: true`. Usuário refina cada spec individualmente (`spec {cod}` interativo) e roda `init {cod}` quando aprovada.
9. **`update-spec` não muda `phase` da task nem `spec_version_consumed`.** Apenas publica a mudança no changelog. O consumidor (`implement` no próximo run) decide quando "consumiu" a nova versão.
10. **Freshness check estendido cruza com `coverage.md`** quando existe (v8). Se changelog ausente (mudança feita sem `update-spec`), trata todos os ACs como potencialmente afetados — degradação consciente.

### Modificações nas sub-skills

| Skill | Mudança |
|-------|---------|
| `spec` | Roda **antes** de `init`. Não depende de branch. Escreve direto em `<specs_path>/tasks/{cod}.md`. Captura input bruto (Jira/texto livre). Ganha `--quick` (skip publish-spec) |
| `init` | Roda **depois** de `spec`. Cria branch + `status.md` apontando pra spec existente. Aceita `--type=trivial` (pula spec) e `--type=normal/critical` (override do perfil) |
| `init-tree` | Adapta pra fluxo em duas fases: gera specs em batch, pausa, depois cria branches em batch |
| `update-spec` (NOVA) | Q&A motivo, edita spec, bumpa `spec_version`, escreve no changelog. Roda em qualquer fase pós-`planned` |
| `implement` | Freshness check estendido: cruza ACs alterados com `coverage.md` (v8), oferece reabrir passos |
| `pack-up` | Carimba `spec_version_delivered`, injeta no PR description |

### Pré-requisitos
- **Técnicos:** Fase 1 (v6). Idealmente Fase 3 (v8), pra freshness check usar matriz de cobertura.
- **Organizacionais:** zero. Inversão é interna; spec viva é controle interno.

### Esforço de build
~3-4 dias. Inversão da ordem mexe em mais skills do que a "spec viva" original entregava sozinha.

### Ganho
- **Spec vira gate, não rascunho.** Spec rejeitada não polui repo com branch órfã.
- **Validação externa fica natural.** PM viajou? Spec espera. Hoje, dev é tentado a "começar codando" e descartar trabalho quando resposta muda escopo.
- **Spec compartilhável sem branch.** Tech lead revisa em main, sem checkout.
- **v11 (multi-autor) deixa de precisar gambiarra.** Se PM/UX co-escrevem spec, ela tem que preceder branch — invertido, é natural.
- **Match com SDD canônico** (Specify Kit, spec-kit). Adaptação peculiar continua, alinhamento conceitual melhora.
- **"Mudou no meio" vira evento consciente.** Histórico por feature, alavanca de retrospectiva.
- **3 perfis evitam cerimônia em task trivial.** Typo não passa por publish-spec.

### Risco
- **Quebra retrocompat.** Migration pra tasks novas; ativas continuam no v8 até `packed-up`.
- **Heurística de perfil pode errar.** Mitigação: confirmação rápida quando inferência incerta, em vez de pular silenciosamente.
- **Custo de aprender ordem nova.** Mitigado por mensagem do `init` quando rodado sem spec prévia ("rode `spec` primeiro ou use `init --type=trivial` se for mudança cosmética").

---

## Fase 5 — Architecture advisor + Domain rules (v10) — ENTREGUE

### Adaptação ao cenário
Duas dimensões "preferidas mas negociáveis" entram juntas. **Nenhuma é gate** — GOD sinaliza, dev decide.

1. **Arquitetura** é negociável, assistida. `plan` lê princípios e padrões, sinaliza desvios.
2. **Regra de negócio** é invariante do domínio. Vive em `domains/<dominio>.md`. `spec` sugere quais BRs aplicáveis; `implement` ajuda a anotar `// rule: BR-X` onde a regra é enforced; `pack-up` injeta tabela no PR.

Os 3 artefatos (`principles.md`, `architecture.md`, `domains/`) são **opcionais e configuráveis** via `GOD/config.md`. Quem ativar, ganha o advisor; quem não ativar, fluxo passa silenciosamente.

### O que entrega

**Configuração:**
- 3 chaves novas em `GOD/config.md`:
  - `principles_path` (default: `GOD/principles.md`)
  - `architecture_path` (default: `GOD/architecture.md`)
  - `domains_path` (default: `<specs_path>/domains/`)
- `install` pergunta se ativa cada um e cria templates vazios sob demanda.

**Architecture advisor:**
- `principles.md` — bullets curtos, projeto-específicos
- `architecture.md` — 3-5 padrões "preferidos mas negociáveis"
- `plan` lê ambos, gera bloco "Considerações arquiteturais" sinalizando desvios. Sempre roda quando os arquivos existem; flag `--skip-architecture` desliga
- Flags `--refactor` / `--preserve` no `plan` modulam tom da sugestão

**Domain rules:**
- `domains/<dominio>.md` — frontmatter `domain: <nome>` + BRs numeradas (`BR-<DOMINIO_UPPER>-NNN`). IDs derivados do `domain` do frontmatter — agnóstico ao projeto
- Cada BR tem **`INVARIANT` + `Why`** (motivo, incidente, regulação)
- `spec` lê `domains/`, sugere `applicable_rules` no frontmatter da spec (heurística + confirmação)
- `implement` ao escrever código sugere comentário `// rule: BR-<DOMINIO>-<N>` onde a invariante é enforced
- `pack-up` injeta tabela "BRs aplicáveis × anotadas" no PR description (similar à matriz de cobertura da v8)
- `review --execution` ganha eixo BR (BRs declaradas anotadas em algum lugar?)

### Decisões tomadas durante a implementação

1. **IDs derivados do `domain:` do frontmatter.** `domain: payments` → `BR-PAYMENTS-007`. Evita colisão entre domínios, fica auto-documentável. GOD nunca prescreve nome de domínio. Templates do install são neutros — sem hardcode de "vakinha", "payments" ou qualquer projeto.
2. **Escopo enxuto pra v10.** Skills `rules` (criação interativa de BR) e `audit-rules` (varredura) ficam pra v10.5 ou patches transversais. v10 entregou só modificações no fluxo principal + templates + parser de `// rule:` no pack-up. Reduziu esforço de ~5 dias estimados pra ~3.
3. **`plan` lê architecture/principles** quando os arquivos existem. Flag `--skip-architecture` desliga. Bloco "Considerações arquiteturais" aparece sempre que pelo menos um arquivo existe (mesmo que vazio: "sem desvios identificados"). Quando ambos paths estão desativados em `config.md`, bloco é omitido silenciosamente.
4. **`pack-up` faz parsing inline de `// rule: BR-X`** sem mexer na skill `coverage` (que segue só pra ACs). Reusa a regex unificada da v8 (compatível com TS/JS/Ruby/Python/Go/Java/C#).
5. **3 chaves novas em `config.md`:** `principles_path`, `architecture_path`, `domains_path`. Defaults razoáveis (`GOD/principles.md`, `GOD/architecture.md`, `<specs_path>/domains/`). Vazias = desativado.
6. **Install pergunta opcionalmente** se ativa cada um dos 3 artefatos. Default = pular. Quem ativa, GOD cria template vazio neutro. Quem não ativa, fluxo segue silencioso (retrocompat com v9).
7. **`spec` sugere `applicable_rules` com confirmação.** Heurística conservadora — quando em dúvida, não sugere. Pulado silenciosamente se `domains_path` está desativado.
8. **`implement` orienta densidade baixa de anotações.** Diretriz explícita: anotar só onde a regra é *enforced*, não em cada toque. ~1 anotação por arquivo de domínio é o esperado. BR-órfã na task vai pra `coverage.md` como nota (sem anotação no código).
9. **`update-spec` permite atualizar `applicable_rules`** quando muda escopo. Inclui adições/remoções no changelog.
10. **`review --execution` cruza `applicable_rules` × diff** (igual cruza ACs × cobertura). BRs órfãs viram "Ajustes necessários", nunca "Reprovado".

### Modificações nas sub-skills

| Skill | Mudança |
|-------|---------|
| `install` | VERSION → v10. Pergunta se ativa principles/architecture/domains. Adiciona 3 chaves no `config.md`. Cria templates vazios neutros (sem hardcode de projeto) |
| `spec` | Lê `domains_path`, sugere `applicable_rules` baseado em description. Adiciona campo `applicable_rules` no frontmatter da spec |
| `plan` | Lê `principles_path` + `architecture_path`. Gera bloco "Considerações arquiteturais" no plan.md. Lista `applicable_rules` da spec no topo. Flags `--skip-architecture`, `--refactor`, `--preserve` |
| `implement` | Ao escrever código que enforça BR aplicável, sugere `// rule: BR-<DOMINIO>-<N> — descrição` (passo similar ao 5.5 da v8 pra ACs) |
| `pack-up` | Parse de `// rule: BR-X` no diff. Tabela "BRs aplicáveis × anotadas" no PR. Alerta BRs sem anotação (não bloqueia) |
| `update-spec` | Oferece atualizar `applicable_rules` quando muda escopo. Inclui no changelog |
| `review --execution` | Eixo extra: BRs em `applicable_rules` anotadas em algum arquivo? Não bloqueia, vira "Ajustes necessários" |

### Pré-requisitos
- **Técnicos:** Fase 4 (v9) entregue ✅.
- **Organizacionais:** baixo. Quem usar precisa preencher os 3 arquivos do projeto (1 tarde de trabalho). Quem não usar, fluxo segue silencioso.

### Esforço de build
~3 dias. Modificações no fluxo + templates + parser de `// rule:` no pack-up.

### Ganho
- **Decisões arquiteturais explícitas e auditáveis** mesmo sendo flexíveis
- **Regra de negócio sai da cabeça das pessoas** — vira artefato versionado e citável em comentário inline (`// rule: BR-X`)
- **Onboarding de novo dev** fica trivial (lê principles + architecture + domains)
- **Refator com alavanca** — GOD ajuda a decidir o que preservar e o que descartar
- **PR com rastreabilidade dupla** — AC × validação (v8) + BR × anotação (v10)
- **Audit-rules futura** (v10.5) terá infra pronta — pra detectar BRs órfãs e código apontando pra BR removida

### Risco
- **Inflação de regras vira ruído.** Mitigação: limitar BRs a invariantes do domínio, não validações de campo. Heurística de sugestão deve ser conservadora — falso positivo treina dev a ignorar.
- **Comentário `// rule:` em todo lugar polui código.** Mitigação: anotar só onde a regra é *enforced*, não em cada toque. Documentado no `implement` como diretriz.
- **Manutenção de domains exige dono.** Sem dono, fica desatualizado. v10.5 entregará `audit-rules` que sinaliza divergências.

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
**v6 + v7 + v8 + v9.** Pare. SDD adaptado e funcional, sem dependência de ninguém. Esforço total: ~2-3 semanas distribuídas em 4 releases (v9 maior por incluir inversão da ordem).

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
| **v8.2 — default target do publish-spec configurável** | `publish-spec` aceita default em `GOD/config.md` seção `## publish_spec_default_target` (single ou comma-separated). Sem default → `stdout` (retrocompat). Tasks novas instaladas via v8.2 já trazem a seção vazia no template | `sub-skills/publish-spec/SKILL.md`, `sub-skills/install/SKILL.md` |
| **v10.1 — spec absorve qualidades da god-spec (unificação)** | Skill `spec` ganha: análise heurística pré-Q&A (detecção de excessos/gaps), Q&A focada apenas em gaps detectados, seção `## Notas técnicas (input pro plan)` no template, self-validação inline antes do review, feature/subtask split inline (alternativa ao init-tree), flag `--target jira/slack/file/stdout/clipboard` (delega pra publish-spec), apresentação ASCII no relatório final. Heurísticas extraídas pra `sub-skills/spec/heuristics.md` (mantém SKILL.md gerenciável). Resolve duplicação com a skill global `god-spec` — agora há uma fonte única de "escrever bem WHAT". `god-spec` continua existindo apenas como wrapper offline pra projetos sem GOD instalado | `sub-skills/spec/SKILL.md`, `sub-skills/spec/heuristics.md` (novo) |
| **v10.2 — scripts Python pra processos robóticos, skill `doctor`, lazy templates, compactação** | Mudança grande de tokens-por-execução. Componentes: **(1) Pasta `sub-skills/_lib/`** com 7 scripts Python 3.8+ stdlib only (cross-platform macOS/Linux/WSL) que substituem trabalho determinístico antes feito pelo LLM: `parse_coverage.py`, `parse_rules.py`, `parse_spec.py`, `validate_spec.py`, `freshness_check.py`, `update_status.py`, `gen_pr_description.py`. **(2) Skills delegam via Bash** seguindo padrão único documentado no SKILL.md raiz (seção "Delegação pra `_lib/`"): detecta python3 ≥ 3.8, roda script, captura JSON; falha de script SEMPRE cai pro fallback LLM com aviso (nunca interrompe processo). **(3) Skill nova `doctor`** faz diagnóstico do ambiente (python3, git, gh, MCPs, GOD/ consistência, scripts em `_lib/`, tasks ativas) e reporta ✅/⚠️/❌ com ação concreta. **(4) Templates do install** (config, knowledge, patterns, learned-patterns, hooks, principles, architecture) extraídos pra `sub-skills/install/templates/*.tmpl` — install/SKILL.md cai de 553 pra 440 linhas. **(5) Compactação cirúrgica** das skills longas (cortes de histórico inline, exemplos duplicados, prose redundante): spec 705→585, implement 426→374. **Economia esperada:** 8-15k tokens em scripts + 3-5k em compactação = 11-20k tokens em pack-up típico. **Garantia:** falha de script nunca interrompe — todas as skills mantêm caminho fallback LLM funcional. | `sub-skills/_lib/*.py`, `sub-skills/doctor/SKILL.md`, `sub-skills/install/templates/*.tmpl`, todas as skills do fluxo principal |
| **v10.3 — peer-review opt-out via config** | Adiciona chave `peer_review_default` em `GOD/config.md` (valores: `subagent` default, `inline`, `skip`). Default mantém comportamento v8.1 (subagent isolado pra fresh eyes anti-viés). `inline` reaproveita contexto do agent principal — economiza ~5k tokens por review, perde fresh eyes (use em projeto pequeno/solo). `skip` desativa review automático. Flags CLI `--subagent`/`--inline`/`--skip` overridem pontualmente. `doctor` mostra config atual e alerta tradeoff se `inline` ou `skip` ativos. **Por que default subagent:** pit of success — quem nunca configurou tem peer-review ativo; quem precisa de economia decide consciente. | `sub-skills/review/SKILL.md`, `sub-skills/install/SKILL.md`, `sub-skills/doctor/SKILL.md` |
| **v10.4 — context blob + quebrar review em 3** | **Item 5 (cache de leituras):** skill chamadora (pack-up, spec, plan) lê artefatos uma vez no início e passa adiante via "context blob" (JSON). Sub-skills/subagents consomem o blob inline em vez de invocar Read pra mesmo arquivo várias vezes. Threshold de 8000 chars: arquivo grande vai por path, não inline. Padrão documentado em "Padrão de context blob (v10.4)" no SKILL.md raiz. Retrocompat: sem blob, sub-skill lê do disco como antes. **Item 7 (quebrar review):** `review/SKILL.md` (264 linhas) virou wrapper fino de roteamento (50 linhas) que delega pra `review-spec/SKILL.md` (76 linhas), `review-plan/SKILL.md` (60 linhas), `review-execution/SKILL.md` (84 linhas). Cada invocação carrega só o conteúdo do modo usado, não os 3 — economia ~2-3k tokens por chamada. Padrão comum (peer_review_default, modo execução, context blob) sobe pro SKILL.md raiz. Retrocompat: invocações `review --modo` continuam funcionando via wrapper. **Economia esperada combinada:** 5-8k tokens em pack-up típico (3-5k cache + 2-3k quebra do review). Doctor valida presença das 3 sub-skills review-*. | `SKILL.md` raiz, `sub-skills/review/SKILL.md`, `sub-skills/review-{spec,plan,execution}/SKILL.md` (novos), `sub-skills/pack-up/SKILL.md`, `sub-skills/coverage/SKILL.md`, `sub-skills/doctor/SKILL.md` |
| **v10.5 — batch consolidado no pack-up** | Cria `sub-skills/_lib/pack_up_validate.py` que **importa e orquestra** `parse_coverage`, `parse_rules`, `parse_spec`, `validate_spec`, `freshness_check` numa única chamada Python. Retorna JSON consolidado contendo: spec metadata, matriz de cobertura + markdown pronto, BRs aplicáveis × anotadas + markdown pronto, freshness check, lint estrutural, e `pr_description_data` pronto pra `gen_pr_description.py`. Pack-up passo 2.5 invoca o batch UMA vez no início; passos 4 (review --execution), 4.5 (coverage), 4.6 (rules) e 7 (PR description) **consomem do JSON** em vez de re-rodar. Subagent de review-execution recebe o JSON pronto e foca em julgamento semântico (efeitos colaterais, convenções) — não re-parseia. **Economia esperada:** 5-8k tokens em pack-up típico (elimina 4 invocações sequenciais). Fallback: cada passo cai pro caminho v10.2 individual se batch falhar. README do projeto reescrito explicando todo o framework do zero. | `sub-skills/_lib/pack_up_validate.py` (novo), `sub-skills/pack-up/SKILL.md`, `sub-skills/review-execution/SKILL.md`, `README.md` |

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
4. **v9 — Spec-first + versionar spec** (inverte ordem `init→spec` para `spec→init`; mudança de escopo como evento de primeira-classe)

Tudo solo, sem dependência organizacional. Architecture advisor (v10) e multi-autor (v11) são extensões que dependem de decisões da empresa e devem ser implementadas apenas com sinal claro.

A primeira fase concreta a iniciar é a v6. As demais derivam dela.

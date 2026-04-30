---
name: god
description: |
  GOD (Goal Oriented Development) — Meta framework que orquestra o ciclo de vida completo de uma task: install, init, spec, plan, implement, pack-up. Inclui variantes (init-tree para lote via árvore Jira) e ferramentas auxiliares (review, status, update-plan, pause, resume, learn, code-like-me, upgrade) e integração com Jira/Figma. Use quando o usuário mencionar: "god", "nova task", "iniciar task", "init em lote", "iniciar epic", "iniciar várias tasks", "subtasks do jira", "spec da task", "criar spec", "planejar task", "implementar task", "pack up", "pause", "resume", "pausar", "retomar", "learn", "conhecimento", "status das tasks", "upgrade god", "help", ou qualquer variação do ciclo de desenvolvimento orientado a objetivos.
tools: Read, Glob, Grep, Bash, Edit, Write, Agent
---

# GOD — Skill Orquestradora

> Skill principal do framework GOD. Orquestra o ciclo de vida de uma task: da inicialização até a entrega. Tem awareness de todas as sub-skills e roteia o usuário para a skill correta.

## Ciclo de vida de uma task

```
install → init → spec → plan → implement → pack-up
                  ↑       ↑        ↑           ↑
               review  review   review      review
               (spec)  (plan)  (update)  (execution)
```

1. **install** — Configura o projeto (executar apenas uma vez). Pergunta `specs_path` (onde a spec da task vai morar) e cria `GOD/config.md`.
2. **init** — Inicializa uma nova task (só cria pastas e description bruta; zero git, zero fetch externo)
3. **spec** — Produz a spec canônica em `<specs_path>/{cod}.md`. Busca dados em Jira/Figma, faz Q&A focada em escopo (proibido falar de implementação), escreve REQs em EARS, ACs com IDs estáveis, cenários e NFRs. Roda `review --spec`.
4. **plan** — Lê a spec pronta. Detecta single vs multi-project, resolve branch+base, escreve o plano focado em **HOW** (arquitetura, arquivos, passos), referenciando ACs. Não toca em escopo nem em git.
5. **implement** — Cria a(s) branch(es) da task no git, executa o plano (subagents para tasks complexas; `code-like-me` aplicado por padrão, use `--skip-code-like-me` para desativar). Consulta a spec durante a escrita pra validar comportamento. Após escrever código, roda verificação contra `GOD/learned-patterns.md` e ajusta pequenos desvios (use `--skip-patterns-check` para desativar)
6. **pack-up** — Finaliza a task (review, commit, push, PR — com link da spec no PR description)

**Variante de entrada:**
- **init-tree** — variante do `init` para lote: recebe um nó-raiz do Jira (Epic, Story, Task com subtasks), desce a árvore toda, cria pastas de contexto para nós internos e chama `init` para cada folha (subtask real)

**Ferramentas auxiliares (não são parte do fluxo linear):**
- **review** — Revisa qualidade em 3 modos: spec (`--spec` com semântica profunda; `--quick` pra só lint), descrição+spec vs plano (`--plan`), plano vs execução com cobertura de ACs (`--execution`). A partir da v8.1, cada modo delega pra **subagent isolado** com contexto fresco — fresh eyes sem viés de auto-validação
- **publish-spec** — Publica/republica a spec em destinos configuráveis (Jira, Slack, stdout, custom). Auxiliar manual ao hook `after spec`.
- **coverage** — Gera matriz "AC × validação" pra uma task dentro do fluxo do GOD. Parseia `// covers: AC-X` em testes + lê `coverage.md` (validações manuais). Usado pelo `pack-up` e `review --execution`, ou manual a qualquer momento. Tolerante por design — ACs órfãos viram alerta visual, decisão fica do dev.
- **status** — Dashboard de tasks em andamento e suas fases
- **update-plan** — Atualiza o plano durante a implementação quando surgem mudanças
- **pause** — Pausa uma task em andamento, registra observação opcional no `changelog.md` e marca `paused: true` no status. Pode ser invocada pelo usuário ou por `implement`/`plan` quando detectam barreira
- **resume** — Retoma uma task pausada, carrega contexto do changelog, remove `paused` do status e delega de volta à skill da fase ativa
- **learn** — Transforma uma task executada em conhecimento reutilizável (ativação explícita pelo usuário). Numa mesma invocação executa duas ações em sequência: (1) escreve entrada da task em `GOD/knowledge.md`; (2) pergunta ao usuário por regras generalizáveis e as anexa em `GOD/learned-patterns.md`. Marca `learned: true` no `status.md` sem alterar `phase`
- **clean-up** — Arquiva tasks em `packed-up` cujos PRs já foram mergiados (move para `GOD/tasks/.archived/`). Oferece rodar `learn` antes de arquivar tasks ainda não aprendidas
- **code-like-me** — Implementação cirúrgica que segue padrões do projeto (usada como flag do implement)
- **upgrade** — Migra instalações do GOD de uma versão para outra (expansível por versão)

## Hooks do fluxo

Cada step do fluxo principal (`init`, `spec`, `plan`, `implement`, `pack-up`) executa hooks opcionais antes e depois de sua lógica principal, lidos de `GOD/hooks.md`. Se o slot estiver com `skip-hook`, pula. Se tiver instruções em linguagem natural, a skill executa.

> **A partir da v7:** a skill `spec` ganhou hooks dedicados (`before spec` e `after spec`). Caso de uso típico do `after spec`: publicar a spec recém-criada como comentário no Jira ou mensagem no Slack pra que PM/UX/CTO fiquem sabendo automaticamente, sem depender de eles abrirem o repo.

Ferramentas auxiliares (learn, update-plan, review, status, pause, resume, code-like-me, publish-spec, upgrade) **não** têm hooks.

## Mapa de sub-skills

| Skill | Localização | Quando usar |
|-------|-------------|-------------|
| `install` | `sub-skills/install/SKILL.md` | Primeira vez no projeto — configura GOD |
| `init` | `sub-skills/init/SKILL.md` | Começar uma nova task (uma de cada vez) |
| `init-tree` | `sub-skills/init-tree/SKILL.md` | Começar em lote via árvore do Jira (Epic/Story + subtasks) |
| `spec` | `sub-skills/spec/SKILL.md` | Produzir a spec canônica da task (escopo + ACs). Modo `--review-feedback` incorpora feedback do stakeholder. |
| `publish-spec` | `sub-skills/publish-spec/SKILL.md` | Publicar/republicar a spec em targets externos (Jira, Slack, stdout) — manual |
| `coverage` | `sub-skills/coverage/SKILL.md` | Gerar matriz AC × validação pra uma task. Manual ou via pack-up/review |
| `plan` | `sub-skills/plan/SKILL.md` | Planejar a implementação técnica (HOW) |
| `implement` | `sub-skills/implement/SKILL.md` | Executar o plano |
| `pack-up` | `sub-skills/pack-up/SKILL.md` | Finalizar e entregar a task |
| `review` | `sub-skills/review/SKILL.md` | Revisão automática (chamada por plan e pack-up) |
| `status` | `sub-skills/status/SKILL.md` | Ver estado das tasks |
| `update-plan` | `sub-skills/update-plan/SKILL.md` | Alterar plano durante implementação |
| `pause` | `sub-skills/pause/SKILL.md` | Pausar task em andamento e registrar observação |
| `resume` | `sub-skills/resume/SKILL.md` | Retomar task pausada e continuar |
| `learn` | `sub-skills/learn/SKILL.md` | Transformar task executada em conhecimento |
| `clean-up` | `sub-skills/clean-up/SKILL.md` | Arquivar tasks em `packed-up` com PRs mergiados |
| `code-like-me` | `sub-skills/code-like-me/SKILL.md` | Flag do implement para código cirúrgico |
| `upgrade` | `sub-skills/upgrade/SKILL.md` | Migrar instalação entre versões do GOD |

## Roteamento inteligente

Quando o usuário interagir, identifique a intenção e delegue para a sub-skill correta:

| Intenção do usuário | Sub-skill |
|---------------------|-----------|
| "instalar", "configurar", "setup" | `install` |
| "nova task", "iniciar task", código do Jira, link do Jira | `init` |
| "init em lote", "iniciar epic", "iniciar várias tasks", "subtasks do jira", "criar tasks da árvore" | `init-tree` |
| "criar spec", "spec da task", "escrever spec", "escopo", "requisitos da task", "critérios de aceitação" | `spec` |
| "feedback do PM", "stakeholder respondeu", "incorporar feedback", "atualizar spec com feedback" | `spec --review-feedback` |
| "publicar spec", "republicar spec", "compartilhar spec", "publish spec" | `publish-spec` |
| "cobertura", "coverage", "que ACs estão testados", "matriz de cobertura", "AC sem teste" | `coverage` |
| "planejar", "criar plano", "como implementar" | `plan` |
| "implementar", "executar", "codar", "desenvolver" | `implement` |
| "finalizar", "entregar", "pack up", "commitar e subir PR" | `pack-up` |
| "status", "como estão as tasks", "dashboard" | `status` |
| "mudar o plano", "atualizar plano", "o plano mudou" | `update-plan` |
| "pause", "pausar", "pausar task", "tô travado", "parar aqui", "retomo depois" | `pause` |
| "resume", "retomar", "continuar task", "voltar na task", "destravei" | `resume` |
| "registrar aprendizado", "learn", "o que aprendi", "transformar em conhecimento" | `learn` |
| "clean-up", "limpar tasks", "arquivar tasks", "remover tasks concluídas", "arrumar a casa" | `clean-up` |
| "upgrade", "atualizar god", "migrar god", "v1 para v2" | `upgrade` |
| "migrate", "migrar do gdd", "migrar gdd para god", "tenho o gdd instalado" | `upgrade` |

## Verificação de versão instalada

Antes de delegar para **qualquer** sub-skill exceto `install` e `upgrade`, verificar:

1. **Existe `GOD/VERSION`?**
   - Se não existe e `GDD/` existe (pasta da skill antiga) → instalação legada da skill GDD. Alertar o usuário e sugerir `upgrade` (ou `migrate`) para migrar de GDD para GOD. Não executar a skill solicitada até a migração rodar.
   - Se não existe e `GOD/` existe (sem VERSION) → instalação v1. Alertar o usuário e sugerir `upgrade` antes de prosseguir. Não executar a skill solicitada até o upgrade rodar.
   - Se não existe e nem `GOD/` nem `GDD/` existem → sugerir `install`.
   - Se existe → ler o valor.

2. **Valor de `GOD/VERSION` corresponde à versão atual do GOD (`v8`)?**
   - Sim → prosseguir com a skill solicitada.
   - Não → alertar o usuário e sugerir `upgrade`.

## Verificação de pré-requisitos

Antes de delegar para uma sub-skill, verifique se os pré-requisitos foram cumpridos:

| Sub-skill | Pré-requisitos |
|-----------|----------------|
| `install` | Nenhum (se `GOD/` já existe, sugerir `upgrade` em vez de reinstalar) |
| `init` | `GOD/` deve existir e estar na versão atual. Se não existir, sugerir `install` |
| `init-tree` | `GOD/` deve existir na versão atual; MCP Atlassian disponível e autenticado (sem isso não há como fetchar a árvore do Jira) |
| `spec` | `GOD/tasks/{cod}/description.md` deve existir (init executado). Se não existir, sugerir rodar `init` primeiro. Precisa ler `GOD/config.md` para resolver `specs_path` — se ausente, usar default `docs/specs/`. Modo `--review-feedback` exige `spec_path` populado em `status.md` e `phase: specified` |
| `publish-spec` | `GOD/tasks/{cod}/status.md` deve ter `spec_path` populado e o arquivo da spec deve existir. Targets desconhecidos exigem definição em `hooks.md` como `# publish-spec target: <nome>` |
| `coverage` | `GOD/tasks/{cod}/status.md` deve ter `spec_path` populado (spec criada). Se ausente, retorna "não aplicável" silenciosamente |
| `plan` | `GOD/tasks/{cod}/status.md` deve ter `spec_path` populado (spec executado). Se ausente, sugerir rodar `spec` primeiro. Precisa ler `GOD/patterns.md` para resolver branch — se a seção "Branch inicial" estiver ausente/vazia, orientar o usuário a preencher |
| `implement` | `GOD/tasks/{cod}/plan.md` deve estar preenchido e `status.md` deve ter `branch` e `branch_base` populados (plan executado). Se algum estiver vazio, sugerir rodar `plan` primeiro |
| `pack-up` | Deve haver alterações no git para commitar (implement executado). Se não houver, informar o usuário |
| `update-plan` | `GOD/tasks/{cod}/plan.md` deve existir e estar preenchido |
| `pause` | `GOD/tasks/{cod}/status.md` deve existir e `phase ≠ packed-up`; não deve estar já pausada |
| `resume` | `GOD/tasks/{cod}/status.md` deve existir com `paused: true` |
| `learn` | Task deve ter pelo menos um commit registrado (pack-up executado) |
| `clean-up` | `GOD/tasks/` deve existir; `gh` CLI instalado e autenticado |
| `status` | `GOD/` deve existir |
| `upgrade` | `GOD/` deve existir (skill detecta versão automaticamente) |

## Recuperação e continuação

Se o usuário retorna após uma interrupção:

1. **Verificar estado atual** — Rodar `status` internamente para entender onde parou
2. **Checar pausa antes de qualquer coisa** — Ler `GOD/tasks/{cod}/status.md` (campo `paused`):
   - Se `paused: true` → sugerir `resume` antes de qualquer outra skill. O contexto da pausa está em `changelog.md` e `resume` cuida da retomada
3. **Identificar fase** — Se a task não está pausada, ler o campo `phase` e sugerir o próximo passo:
   - `initialized` → sugerir `spec`
   - `specified` → sugerir `plan`
   - `planned` → sugerir `implement`
   - `implementing` → sugerir continuar o `implement` ou rodar `update-plan` se o escopo mudou
   - `implemented` → sugerir `pack-up`
   - `packed-up`:
     - Se `learned: false` → sugerir `learn` (opcional) e depois `clean-up` quando os PRs forem mergiados
     - Se `learned: true` → sugerir `clean-up` quando os PRs forem mergiados
4. **Fallback** — Se `status.md` não existir (task criada antes desta convenção), inferir a fase pelos arquivos existentes:
   - Só `description.md` existe → parou após `init`, sugerir `spec`
   - `spec` em `<specs_path>/{cod}.md` existe mas `plan.md` vazio → parou após `spec`, sugerir `plan`
   - `plan.md` preenchido mas sem alterações no git → parou antes do `implement`, sugerir `implement`
   - Alterações no git não commitadas → parou durante ou após `implement`, sugerir `pack-up`
   - PR já criado → task finalizada
5. **Sugerir próximo passo** — Informar o usuário onde parou e qual skill rodar

## Comando: `help`

Quando o usuário pedir ajuda, disser "help", "o que posso fazer?", "como funciona?" ou qualquer variação:

1. **Verificar se o projeto já foi instalado** — checar se `GOD/` existe
2. **Verificar versão** — checar `GOD/VERSION`; se desatualizada, sugerir `upgrade` antes de tudo
3. **Verificar se há tasks em andamento** — checar `GOD/tasks/`
4. **Montar resposta contextual:**

**Se o projeto NÃO foi instalado:**

```
👋 **Bem-vindo ao GOD — Goal Oriented Development!**

O GOD orquestra o ciclo completo de uma task: da spec à entrega do PR.

🚀 **Para começar, rode `install`** — isso vai configurar o projeto criando a pasta GOD/ com:
  • VERSION — versão instalada (atualmente v8)
  • config.md — configuração local (specs_path: onde a spec da task vai morar)
  • knowledge.md — registro de tasks finalizadas (escrito apenas pelo `learn`)
  • patterns.md — convenções do projeto (branch, commit, PR, ações finais)
  • learned-patterns.md — regras generalizáveis escopadas (geral/linguagem/projeto), escritas pelo `learn` após revisão de PR e aplicadas pelo `implement` após a escrita de código
  • hooks.md — pontos de extensão por step (before/after de init, plan, implement, pack-up)
  • tasks/ — pasta onde cada task terá description, plan e status

A v8 entrega **SDD com rastreabilidade AC × validação**: cada AC declarado na spec é amarrado
a um teste automatizado (via comentário `// covers: AC-X` parseado) ou validação manual
(em `coverage.md`). A matriz é injetada no PR description automaticamente e alerta sobre
ACs órfãos. A v7 já trazia hooks de propagação, review semântico, freshness check e
publish-spec — tudo segue funcionando em conjunto.

Após instalar, preencha o `patterns.md` com as convenções do seu projeto. Os hooks são opcionais.

Integrações opcionais (não obrigatórias):
  • Jira (Atlassian MCP) — busca automática de tasks
  • Figma (Figma MCP) — análise de design durante planejamento
```

**Se a instalação está em versão antiga:**

```
⚠️ **GOD detectado em versão anterior**

A versão atual é v8 mas sua instalação está em {versão-detectada}.

Rode `upgrade` para migrar sua estrutura automaticamente — seus valores (patterns, tasks, knowledge) são preservados.
```

**Se o projeto JÁ foi instalado, está na versão atual e NÃO há tasks:**

```
📋 **GOD — Pronto para começar!**

Seu projeto está configurado. Para iniciar sua primeira task:

1. `init` — Passe o link/código do Jira ou descreva a task manualmente
   → Cria a pasta e a description bruta. Não toca em git nem fetcha Jira.
   → Para iniciar em lote a partir de um Epic/Story com subtasks, use `init-tree` (fetcha a árvore do Jira e cria contextos + tasks reais)

2. `spec` — Produz a spec canônica da task
   → Busca dados em Jira/Figma, faz Q&A focada em escopo (sem falar de implementação)
   → Escreve REQs em EARS, ACs com IDs estáveis, cenários e NFRs
   → Spec mora em <specs_path>/tasks/{cod}.md — fora da pasta GOD/, committável por todos
   → Roda review --spec (estrutural + lint + semântico) antes de finalizar
   → Hook `after spec` opcional: publica automaticamente em Jira/Slack
   → Modo `spec --review-feedback`: incorpora feedback do stakeholder (incrementa spec_version)

3. `plan` — Lê a spec pronta e produz o plano técnico
   → Consulta knowledge por padrões, lê CLAUDE.md/ARCHITECTURE.md, resolve branch
   → Foca exclusivamente em HOW (arquitetura, arquivos, passos)
   → Cada passo do plano referencia ACs específicos da spec

4. `implement` — Cria a(s) branch(es) no git e executa o plano
   → Por padrão aplica `code-like-me` (código cirúrgico que imita os devs do projeto). Use `--skip-code-like-me` para desativar.
   → Consulta a spec durante a escrita pra validar comportamento contra ACs.
   → Anota `// covers: AC-X` nos testes escritos (v8 — alimenta a matriz de cobertura).
   → Após escrever código, roda verificação contra `learned-patterns.md` e ajusta pequenos desvios. Use `--skip-patterns-check` para desativar.

5. `pack-up` — Finaliza e entrega
   → Review (com cobertura de ACs em v8), commit, push, PR — com link da spec e tabela de cobertura no PR description

Ferramentas auxiliares (quando precisar):
  • `publish-spec` — Publicar/republicar spec em targets externos (Jira/Slack/stdout)
  • `coverage` — Matriz AC × validação pra uma task (manual ou via pack-up)
  • `status` — Ver dashboard de tasks (ignora pastas de contexto do init-tree)
  • `update-plan` — Alterar plano durante implementação
  • `pause` / `resume` — Pausar e retomar uma task em andamento (registra observação no changelog)
  • `learn` — Transformar task em conhecimento (ativação explícita)
  • `clean-up` — Arquivar tasks em `packed-up` cujos PRs já foram mergiados
  • `upgrade` — Migrar para versão mais nova do GOD
```

**Se há tasks em andamento:**

Rodar `status` internamente e apresentar o dashboard junto com a sugestão do próximo passo:

```
📋 **GOD — Você tem tasks em andamento!**

{dashboard do status}

💡 Sugestão: {próximo passo baseado na fase da task mais recente}

Steps do fluxo:
  • `init`         — Iniciar nova task
  • `init-tree`    — Iniciar em lote via árvore Jira (Epic/Story + subtasks)
  • `spec`         — Produzir a spec canônica (escopo, ACs, cenários, NFRs)
  • `plan`         — Criar plano técnico (arquitetura, arquivos, passos — referencia ACs)
  • `implement`    — Executar o plano (cria a branch no git)
  • `pack-up`      — Finalizar e entregar (commit + PR com link da spec)

Ferramentas auxiliares:
  • `publish-spec` — Publicar/republicar spec em targets (Jira/Slack/stdout)
  • `coverage`     — Matriz AC × validação pra uma task
  • `learn`        — Transformar task em conhecimento (ativação explícita)
  • `clean-up`     — Arquivar tasks em `packed-up` cujos PRs já foram mergiados
  • `status`       — Ver dashboard completo
  • `update-plan`  — Alterar plano durante implementação
  • `pause`        — Pausar task em andamento e registrar observação no changelog
  • `resume`       — Retomar task pausada
  • `upgrade`      — Migrar para versão mais nova do GOD
```

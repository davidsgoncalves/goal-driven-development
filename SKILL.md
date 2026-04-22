---
name: god
description: |
  GOD (Goal Oriented Development) — Meta framework que orquestra o ciclo de vida completo de uma task: install, init, plan, implement, pack-up. Inclui variantes (init-tree para lote via árvore Jira) e ferramentas auxiliares (review, status, update-plan, pause, resume, learn, code-like-me, upgrade) e integração com Jira/Figma. Use quando o usuário mencionar: "god", "nova task", "iniciar task", "init em lote", "iniciar epic", "iniciar várias tasks", "subtasks do jira", "planejar task", "implementar task", "pack up", "pause", "resume", "pausar", "retomar", "learn", "conhecimento", "status das tasks", "upgrade god", "help", ou qualquer variação do ciclo de desenvolvimento orientado a objetivos.
tools: Read, Glob, Grep, Bash, Edit, Write, Agent
---

# GOD — Skill Orquestradora

> Skill principal do framework GOD. Orquestra o ciclo de vida de uma task: da inicialização até a entrega. Tem awareness de todas as sub-skills e roteia o usuário para a skill correta.

## Ciclo de vida de uma task

```
install → init → plan → implement → pack-up
                   ↑        ↑           ↑
                review   review      review
                (plan)   (update)   (execution)
```

1. **install** — Configura o projeto (executar apenas uma vez)
2. **init** — Inicializa uma nova task (só cria pastas e descrição; zero git, zero fetch externo)
3. **plan** — Enriquece a descrição (Jira/Figma/knowledge/Q&A), detecta single vs multi-project, resolve branch+base da task (nome planejado, sem criar) e escreve o plano
4. **implement** — Cria a(s) branch(es) da task no git, executa o plano (subagents para tasks complexas; `code-like-me` aplicado por padrão, use `--skip-code-like-me` para desativar). Após escrever código, roda verificação contra `GOD/learned-patterns.md` e ajusta pequenos desvios (use `--skip-patterns-check` para desativar)
5. **pack-up** — Finaliza a task (review, commit, push, PR)

**Variante de entrada:**
- **init-tree** — variante do `init` para lote: recebe um nó-raiz do Jira (Epic, Story, Task com subtasks), desce a árvore toda, cria pastas de contexto para nós internos e chama `init` para cada folha (subtask real)

**Ferramentas auxiliares (não são parte do fluxo linear):**
- **review** — Revisa qualidade em 2 modos: descrição vs plano (`--plan`) e plano vs execução (`--execution`)
- **status** — Dashboard de tasks em andamento e suas fases
- **update-plan** — Atualiza o plano durante a implementação quando surgem mudanças
- **pause** — Pausa uma task em andamento, registra observação opcional no `changelog.md` e marca `paused: true` no status. Pode ser invocada pelo usuário ou por `implement`/`plan` quando detectam barreira
- **resume** — Retoma uma task pausada, carrega contexto do changelog, remove `paused` do status e delega de volta à skill da fase ativa
- **learn** — Transforma uma task executada em conhecimento reutilizável (ativação explícita pelo usuário). Numa mesma invocação executa duas ações em sequência: (1) escreve entrada da task em `GOD/knowledge.md`; (2) pergunta ao usuário por regras generalizáveis e as anexa em `GOD/learned-patterns.md`. Marca `learned: true` no `status.md` sem alterar `phase`
- **clean-up** — Arquiva tasks em `packed-up` cujos PRs já foram mergiados (move para `GOD/tasks/.archived/`). Oferece rodar `learn` antes de arquivar tasks ainda não aprendidas
- **code-like-me** — Implementação cirúrgica que segue padrões do projeto (usada como flag do implement)
- **upgrade** — Migra instalações do GOD de uma versão para outra (expansível por versão)

## Hooks do fluxo

Cada step do fluxo principal (`init`, `plan`, `implement`, `pack-up`) executa hooks opcionais antes e depois de sua lógica principal, lidos de `GOD/hooks.md`. Se o slot estiver com `skip-hook`, pula. Se tiver instruções em linguagem natural, a skill executa.

Ferramentas auxiliares (learn, update-plan, review, status, pause, resume, code-like-me, upgrade) **não** têm hooks.

## Mapa de sub-skills

| Skill | Localização | Quando usar |
|-------|-------------|-------------|
| `install` | `sub-skills/install/SKILL.md` | Primeira vez no projeto — configura GOD |
| `init` | `sub-skills/init/SKILL.md` | Começar uma nova task (uma de cada vez) |
| `init-tree` | `sub-skills/init-tree/SKILL.md` | Começar em lote via árvore do Jira (Epic/Story + subtasks) |
| `plan` | `sub-skills/plan/SKILL.md` | Planejar a implementação |
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

2. **Valor de `GOD/VERSION` corresponde à versão atual do GOD (`v5`)?**
   - Sim → prosseguir com a skill solicitada.
   - Não → alertar o usuário e sugerir `upgrade`.

## Verificação de pré-requisitos

Antes de delegar para uma sub-skill, verifique se os pré-requisitos foram cumpridos:

| Sub-skill | Pré-requisitos |
|-----------|----------------|
| `install` | Nenhum (se `GOD/` já existe, sugerir `upgrade` em vez de reinstalar) |
| `init` | `GOD/` deve existir e estar na versão atual. Se não existir, sugerir `install` |
| `init-tree` | `GOD/` deve existir na versão atual; MCP Atlassian disponível e autenticado (sem isso não há como fetchar a árvore do Jira) |
| `plan` | `GOD/tasks/{cod}/description.md` deve existir (init executado). Se não existir, sugerir rodar `init` primeiro. Precisa ler `GOD/patterns.md` para resolver branch — se a seção "Branch inicial" estiver ausente/vazia, orientar o usuário a preencher |
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
   - `initialized` → sugerir `plan`
   - `planned` → sugerir `implement`
   - `implementing` → sugerir continuar o `implement` ou rodar `update-plan` se o escopo mudou
   - `implemented` → sugerir `pack-up`
   - `packed-up`:
     - Se `learned: false` → sugerir `learn` (opcional) e depois `clean-up` quando os PRs forem mergiados
     - Se `learned: true` → sugerir `clean-up` quando os PRs forem mergiados
4. **Fallback** — Se `status.md` não existir (task criada antes desta convenção), inferir a fase pelos arquivos existentes:
   - Só `description.md` existe → parou após `init`, sugerir `plan`
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

O GOD orquestra o ciclo completo de uma task: da coleta de requisitos até a entrega do PR.

🚀 **Para começar, rode `install`** — isso vai configurar o projeto criando a pasta GOD/ com:
  • VERSION — versão instalada (atualmente v5)
  • knowledge.md — registro de tasks finalizadas (escrito apenas pelo `learn`)
  • patterns.md — convenções do projeto (branch, commit, PR, ações finais)
  • learned-patterns.md — regras generalizáveis escopadas (geral/linguagem/projeto), escritas pelo `learn` após revisão de PR e aplicadas pelo `implement` após a escrita de código
  • hooks.md — pontos de extensão por step (before/after de init, plan, implement, pack-up)
  • tasks/ — pasta onde cada task terá sua descrição, plano e status

Após instalar, preencha o `patterns.md` com as convenções do seu projeto. Os hooks são opcionais.

Integrações opcionais (não obrigatórias):
  • Jira (Atlassian MCP) — busca automática de tasks
  • Figma (Figma MCP) — análise de design durante planejamento
```

**Se a instalação está em versão antiga:**

```
⚠️ **GOD detectado em versão anterior**

A versão atual é v5 mas sua instalação está em {versão-detectada}.

Rode `upgrade` para migrar sua estrutura automaticamente — seus valores (patterns, tasks, knowledge) são preservados.
```

**Se o projeto JÁ foi instalado, está na versão atual e NÃO há tasks:**

```
📋 **GOD — Pronto para começar!**

Seu projeto está configurado. Para iniciar sua primeira task:

1. `init` — Passe o link/código do Jira ou descreva a task manualmente
   → Cria a pasta e o description bruto. Não toca em git nem fetcha Jira.
   → Para iniciar em lote a partir de um Epic/Story com subtasks, use `init-tree` (fetcha a árvore do Jira e cria contextos + tasks reais)

2. `plan` — Enriquece descrição (Jira/Figma/knowledge/Q&A), resolve a branch da task
   → Consulta Figma, commits anteriores, arquitetura do projeto
   → Escreve "Branch de trabalho" (base + nome) no plan.md e persiste em status.md

3. `implement` — Cria a(s) branch(es) no git e executa o plano
   → Por padrão aplica `code-like-me` (código cirúrgico que imita os devs do projeto). Use `--skip-code-like-me` para desativar.
   → Após escrever código, roda verificação contra `learned-patterns.md` (regras aprendidas em PRs anteriores) e ajusta pequenos desvios. Use `--skip-patterns-check` para desativar.

4. `pack-up` — Finaliza e entrega
   → Review, commit, push, PR — tudo automático

Ferramentas auxiliares (quando precisar):
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
  • `plan`         — Criar plano de implementação (resolve branch da task)
  • `implement`    — Executar o plano (cria a branch no git)
  • `pack-up`      — Finalizar e entregar (commit + PR)

Ferramentas auxiliares:
  • `learn`        — Transformar task em conhecimento (ativação explícita)
  • `clean-up`     — Arquivar tasks em `packed-up` cujos PRs já foram mergiados
  • `status`       — Ver dashboard completo
  • `update-plan`  — Alterar plano durante implementação
  • `pause`        — Pausar task em andamento e registrar observação no changelog
  • `resume`       — Retomar task pausada
  • `upgrade`      — Migrar para versão mais nova do GOD
```

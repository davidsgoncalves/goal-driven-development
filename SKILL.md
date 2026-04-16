---
name: god
description: |
  GOD (Goal Oriented Development) — Meta framework que orquestra o ciclo de vida completo de uma task: install, init, plan, implement, pack-up. Inclui ferramentas auxiliares (review, status, update-plan, learn, code-like-me, upgrade) e integração com Jira/Figma. Use quando o usuário mencionar: "god", "nova task", "iniciar task", "planejar task", "implementar task", "pack up", "learn", "conhecimento", "status das tasks", "upgrade god", "help", ou qualquer variação do ciclo de desenvolvimento orientado a objetivos.
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
2. **init** — Inicializa uma nova task (cria estrutura, coleta dados do Jira/Figma, Q&A com usuário)
3. **plan** — Cria o plano de implementação (analisa contexto, tira dúvidas, escreve plano, revisa)
4. **implement** — Executa o plano (subagents para tasks complexas; `code-like-me` aplicado por padrão, use `--skip-code-like-me` para desativar)
5. **pack-up** — Finaliza a task (review, commit, push, PR)

**Ferramentas auxiliares (não são parte do fluxo linear):**
- **review** — Revisa qualidade em 2 modos: descrição vs plano (`--plan`) e plano vs execução (`--execution`)
- **status** — Dashboard de tasks em andamento e suas fases
- **update-plan** — Atualiza o plano durante a implementação quando surgem mudanças
- **learn** — Transforma uma task executada em conhecimento reutilizável (ativação explícita pelo usuário). Marca `learned: true` no `status.md` sem alterar `phase`
- **clean-up** — Arquiva tasks em `packed-up` cujos PRs já foram mergiados (move para `GOD/tasks/.archived/`). Oferece rodar `learn` antes de arquivar tasks ainda não aprendidas
- **code-like-me** — Implementação cirúrgica que segue padrões do projeto (usada como flag do implement)
- **upgrade** — Migra instalações do GOD de uma versão para outra (expansível por versão)

## Hooks do fluxo

Cada step do fluxo principal (`init`, `plan`, `implement`, `pack-up`) executa hooks opcionais antes e depois de sua lógica principal, lidos de `GOD/hooks.md`. Se o slot estiver com `skip-hook`, pula. Se tiver instruções em linguagem natural, a skill executa.

Ferramentas auxiliares (learn, update-plan, review, status, code-like-me, upgrade) **não** têm hooks.

## Mapa de sub-skills

| Skill | Localização | Quando usar |
|-------|-------------|-------------|
| `install` | `sub-skills/install/SKILL.md` | Primeira vez no projeto — configura GOD |
| `init` | `sub-skills/init/SKILL.md` | Começar uma nova task |
| `plan` | `sub-skills/plan/SKILL.md` | Planejar a implementação |
| `implement` | `sub-skills/implement/SKILL.md` | Executar o plano |
| `pack-up` | `sub-skills/pack-up/SKILL.md` | Finalizar e entregar a task |
| `review` | `sub-skills/review/SKILL.md` | Revisão automática (chamada por plan e pack-up) |
| `status` | `sub-skills/status/SKILL.md` | Ver estado das tasks |
| `update-plan` | `sub-skills/update-plan/SKILL.md` | Alterar plano durante implementação |
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
| "planejar", "criar plano", "como implementar" | `plan` |
| "implementar", "executar", "codar", "desenvolver" | `implement` |
| "finalizar", "entregar", "pack up", "commitar e subir PR" | `pack-up` |
| "status", "como estão as tasks", "dashboard" | `status` |
| "mudar o plano", "atualizar plano", "o plano mudou" | `update-plan` |
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

2. **Valor de `GOD/VERSION` corresponde à versão atual do GOD (`v3`)?**
   - Sim → prosseguir com a skill solicitada.
   - Não → alertar o usuário e sugerir `upgrade`.

## Verificação de pré-requisitos

Antes de delegar para uma sub-skill, verifique se os pré-requisitos foram cumpridos:

| Sub-skill | Pré-requisitos |
|-----------|----------------|
| `install` | Nenhum (se `GOD/` já existe, sugerir `upgrade` em vez de reinstalar) |
| `init` | `GOD/` deve existir e estar na versão atual. Se não existir, sugerir `install` |
| `plan` | `GOD/tasks/{cod}/description.md` deve existir (init executado). Se não existir, sugerir rodar `init` primeiro |
| `implement` | `GOD/tasks/{cod}/plan.md` deve estar preenchido (plan executado). Se estiver vazio, sugerir rodar `plan` primeiro |
| `pack-up` | Deve haver alterações no git para commitar (implement executado). Se não houver, informar o usuário |
| `update-plan` | `GOD/tasks/{cod}/plan.md` deve existir e estar preenchido |
| `learn` | Task deve ter pelo menos um commit registrado (pack-up executado) |
| `clean-up` | `GOD/tasks/` deve existir; `gh` CLI instalado e autenticado |
| `status` | `GOD/` deve existir |
| `upgrade` | `GOD/` deve existir (skill detecta versão automaticamente) |

## Recuperação e continuação

Se o usuário retorna após uma interrupção:

1. **Verificar estado atual** — Rodar `status` internamente para entender onde parou
2. **Identificar fase** — Ler `GOD/tasks/{cod}/status.md` (campo `phase`) e sugerir o próximo passo:
   - `initialized` → sugerir `plan`
   - `planned` → sugerir `implement`
   - `implementing` → sugerir continuar o `implement` ou rodar `update-plan` se o escopo mudou
   - `implemented` → sugerir `pack-up`
   - `packed-up`:
     - Se `learned: false` → sugerir `learn` (opcional) e depois `clean-up` quando os PRs forem mergiados
     - Se `learned: true` → sugerir `clean-up` quando os PRs forem mergiados
3. **Fallback** — Se `status.md` não existir (task criada antes desta convenção), inferir a fase pelos arquivos existentes:
   - Só `description.md` existe → parou após `init`, sugerir `plan`
   - `plan.md` preenchido mas sem alterações no git → parou antes do `implement`, sugerir `implement`
   - Alterações no git não commitadas → parou durante ou após `implement`, sugerir `pack-up`
   - PR já criado → task finalizada
4. **Sugerir próximo passo** — Informar o usuário onde parou e qual skill rodar

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
  • VERSION — versão instalada (atualmente v3)
  • knowledge.md — registro de tasks finalizadas (escrito apenas pelo `learn`)
  • patterns.md — convenções do projeto (branch, commit, PR, ações finais)
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

A versão atual é v3 mas sua instalação está em {versão-detectada}.

Rode `upgrade` para migrar sua estrutura automaticamente — seus valores (patterns, tasks, knowledge) são preservados.
```

**Se o projeto JÁ foi instalado, está na versão atual e NÃO há tasks:**

```
📋 **GOD — Pronto para começar!**

Seu projeto está configurado. Para iniciar sua primeira task:

1. `init` — Passe o link/código do Jira ou descreva a task manualmente
   → Cria a descrição, coleta contexto, faz Q&A com você

2. `plan` — Analisa a task e cria o plano de implementação
   → Consulta Figma, commits anteriores, arquitetura do projeto

3. `implement` — Executa o plano
   → Por padrão aplica `code-like-me` (código cirúrgico que imita os devs do projeto). Use `--skip-code-like-me` para desativar.

4. `pack-up` — Finaliza e entrega
   → Review, commit, push, PR — tudo automático

Ferramentas auxiliares (quando precisar):
  • `status` — Ver dashboard de tasks
  • `update-plan` — Alterar plano durante implementação
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
  • `plan`         — Criar plano de implementação
  • `implement`    — Executar o plano
  • `pack-up`      — Finalizar e entregar (commit + PR)

Ferramentas auxiliares:
  • `learn`        — Transformar task em conhecimento (ativação explícita)
  • `clean-up`     — Arquivar tasks em `packed-up` cujos PRs já foram mergiados
  • `status`       — Ver dashboard completo
  • `update-plan`  — Alterar plano durante implementação
  • `upgrade`      — Migrar para versão mais nova do GOD
```

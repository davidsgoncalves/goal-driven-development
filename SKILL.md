---
name: gdd
description: |
  GDD (Goal Driven Development) — Meta framework que orquestra o ciclo de vida completo de uma task: install, init, plan, implement, pack-up, learn. Inclui review automática, status dashboard, update-plan, learn (knowledge) e integração com Jira/Figma. Use quando o usuário mencionar: "gdd", "nova task", "iniciar task", "planejar task", "implementar task", "pack up", "learn", "conhecimento", "status das tasks", "help", ou qualquer variação do ciclo de desenvolvimento orientado a objetivos.
tools: Read, Glob, Grep, Bash, Edit, Write, Agent
---

# GDD — Skill Orquestradora

> Skill principal do framework GDD. Orquestra o ciclo de vida completo de uma task: da inicialização até a entrega. Tem awareness de todas as sub-skills e roteia o usuário para a skill correta.

## Ciclo de vida de uma task

```
install → init → plan → implement → pack-up → learn
                   ↑        ↑           ↑
                review   review      review
                (plan)   (update)   (execution)
```

1. **install** — Configura o projeto (executar apenas uma vez)
2. **init** — Inicializa uma nova task (cria estrutura, coleta dados do Jira/Figma, Q&A com usuário)
3. **plan** — Cria o plano de implementação (analisa contexto, tira dúvidas, escreve plano, revisa)
4. **implement** — Executa o plano (subagents para tasks complexas, flag `--code-like-me` para código cirúrgico)
5. **pack-up** — Finaliza a task (review, commit, testes, push, PR)
6. **learn** — Transforma a task executada em conhecimento reutilizável (extrai aprendizados, registra no knowledge)

**Skills auxiliares:**
- **review** — Revisa qualidade em 2 modos: descrição vs plano (`--plan`) e plano vs execução (`--execution`)
- **status** — Dashboard de tasks em andamento e suas fases
- **update-plan** — Atualiza o plano durante a implementação quando surgem mudanças
- **code-like-me** — Implementação cirúrgica que segue padrões do projeto (usada como flag do implement)

## Mapa de sub-skills

| Skill | Localização | Quando usar |
|-------|-------------|-------------|
| `install` | `sub-skills/install/skill.md` | Primeira vez no projeto — configura GDD |
| `init` | `sub-skills/init/skill.md` | Começar uma nova task |
| `plan` | `sub-skills/plan/skill.md` | Planejar a implementação |
| `implement` | `sub-skills/implement/skill.md` | Executar o plano |
| `pack-up` | `sub-skills/pack-up/skill.md` | Finalizar e entregar a task |
| `review` | `sub-skills/review/skill.md` | Revisão automática (chamada por plan e pack-up) |
| `status` | `sub-skills/status/skill.md` | Ver estado das tasks |
| `update-plan` | `sub-skills/update-plan/skill.md` | Alterar plano durante implementação |
| `learn` | `sub-skills/learn/skill.md` | Transformar task executada em conhecimento |
| `code-like-me` | `sub-skills/code-like-me/skill.md` | Flag do implement para código cirúrgico |

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

## Verificação de pré-requisitos

Antes de delegar para uma sub-skill, verifique se os pré-requisitos foram cumpridos:

| Sub-skill | Pré-requisitos |
|-----------|----------------|
| `install` | Nenhum |
| `init` | `GDD/` deve existir (install executado). Se não existir, sugerir rodar `install` primeiro |
| `plan` | `GDD/tasks/{cod}/description.md` deve existir (init executado). Se não existir, sugerir rodar `init` primeiro |
| `implement` | `GDD/tasks/{cod}/plan.md` deve estar preenchido (plan executado). Se estiver vazio, sugerir rodar `plan` primeiro |
| `pack-up` | Deve haver alterações no git para commitar (implement executado). Se não houver, informar o usuário |
| `update-plan` | `GDD/tasks/{cod}/plan.md` deve existir e estar preenchido |
| `learn` | Task deve ter pelo menos um commit registrado (pack-up executado) |
| `status` | `GDD/` deve existir |

## Recuperação e continuação

Se o usuário retorna após uma interrupção:

1. **Verificar estado atual** — Rodar `status` internamente para entender onde parou
2. **Identificar fase** — Ler `GDD/tasks/{cod}/status.md` (campo `phase`) e sugerir o próximo passo:
   - `initialized` → sugerir `plan`
   - `planned` → sugerir `implement`
   - `implementing` → sugerir continuar o `implement` ou rodar `update-plan` se o escopo mudou
   - `implemented` → sugerir `pack-up`
   - `packed-up` → sugerir `learn`
   - `learned` → task finalizada, sem próximo passo
3. **Fallback** — Se `status.md` não existir (task criada antes desta convenção), inferir a fase pelos arquivos existentes:
   - Só `description.md` existe → parou após `init`, sugerir `plan`
   - `plan.md` preenchido mas sem alterações no git → parou antes do `implement`, sugerir `implement`
   - Alterações no git não commitadas → parou durante ou após `implement`, sugerir `pack-up`
   - PR já criado → task finalizada
4. **Sugerir próximo passo** — Informar o usuário onde parou e qual skill rodar

## Comando: `help`

Quando o usuário pedir ajuda, disser "help", "o que posso fazer?", "como funciona?" ou qualquer variação:

1. **Verificar se o projeto já foi instalado** — checar se `GDD/` existe
2. **Verificar se há tasks em andamento** — checar `GDD/tasks/`
3. **Montar resposta contextual:**

**Se o projeto NÃO foi instalado:**

```
👋 **Bem-vindo ao GDD — Goal Driven Development!**

O GDD orquestra o ciclo completo de uma task: da coleta de requisitos até a entrega do PR.

🚀 **Para começar, rode `install`** — isso vai configurar o projeto criando a pasta GDD/ com:
  • knowledge.md — registro de tasks finalizadas
  • pack-up-instructions.md — suas convenções de branch, commit, PR e testes
  • tasks/ — pasta onde cada task terá sua descrição e plano

Após instalar, preencha o pack-up-instructions.md com as convenções do seu projeto.

Integrações opcionais (não obrigatórias):
  • Jira (Atlassian MCP) — busca automática de tasks
  • Figma (Figma MCP) — análise de design durante planejamento
```

**Se o projeto JÁ foi instalado mas NÃO há tasks:**

```
📋 **GDD — Pronto para começar!**

Seu projeto está configurado. Para iniciar sua primeira task:

1. `init` — Passe o link/código do Jira ou descreva a task manualmente
   → Cria a descrição, coleta contexto, faz Q&A com você

2. `plan` — Analisa a task e cria o plano de implementação
   → Consulta Figma, commits anteriores, arquitetura do projeto

3. `implement` — Executa o plano
   → Use `--code-like-me` para código que segue exatamente os padrões do projeto

4. `pack-up` — Finaliza e entrega
   → Review, commit, testes, push, PR — tudo automático

5. `learn` — Transforma a task em conhecimento
   → Extrai aprendizados, registra commits e decisões no knowledge

Outros comandos:
  • `status` — Ver dashboard de tasks
  • `update-plan` — Alterar plano durante implementação
```

**Se há tasks em andamento:**

Rodar `status` internamente e apresentar o dashboard junto com a sugestão do próximo passo:

```
📋 **GDD — Você tem tasks em andamento!**

{dashboard do status}

💡 Sugestão: {próximo passo baseado na fase da task mais recente}

Comandos disponíveis:
  • `init`         — Iniciar nova task
  • `plan`         — Criar plano de implementação
  • `implement`    — Executar o plano
  • `pack-up`      — Finalizar e entregar (commit + PR)
  • `learn`        — Transformar task em conhecimento
  • `status`       — Ver dashboard completo
  • `update-plan`  — Alterar plano durante implementação
```

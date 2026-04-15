# GDD — Goal Driven Development

Meta framework de skills para desenvolvimento orientado a objetivos. Orquestra o ciclo de vida completo de uma task — da coleta de requisitos até a entrega do PR — usando sub-skills especializadas que se comunicam entre si.

## Como funciona

O GDD cria uma camada de gestao por cima do seu projeto. Ao instalar, ele gera uma pasta `GDD/` (Working Development Directory) que armazena o estado de cada task: descricao, plano, knowledge acumulado e instrucoes de finalizacao.

Cada etapa do desenvolvimento e coberta por uma sub-skill dedicada. A skill orquestradora sabe qual chamar, verifica pre-requisitos e sugere o proximo passo.

## Ciclo de vida

```
install → init → plan → implement → pack-up
                  ↑        ↑           ↑
               review    review      review
               (plan)   (update)   (execution)
```

1. **install** — Configura o projeto. Cria a pasta `GDD/`, templates de knowledge e pack-up-instructions. Verifica MCPs opcionais (Figma, Jira). Executar apenas uma vez.

2. **init** — Inicializa uma task. Recebe link do Jira, codigo da task ou descricao manual. Busca dados no Jira, coleta links do Figma, consulta knowledge por tasks semelhantes, faz Q&A com o usuario e salva tudo em `description.md`.

3. **plan** — Cria o plano de implementacao. Analisa a descricao, commits de referencia, design do Figma, arquivos de convencao do projeto (`CLAUDE.md`, `ARCHITECTURE.md`, `AGENTS.md`), tira duvidas e escreve o plano. Roda review automatica antes de finalizar.

4. **implement** — Executa o plano. Tasks simples sao executadas diretamente. Tasks complexas sao divididas em subagents paralelos. Suporta flag `--code-like-me` para implementacao cirurgica que segue exatamente os padroes do projeto.

5. **pack-up** — Finaliza a task. Roda review plano vs execucao, commit, testes, linter, push e cria PR. Tudo seguindo as convencoes definidas no `pack-up-instructions.md`. **Nao escreve no knowledge** — isso e responsabilidade exclusiva da skill `learn`.

6. **learn** — Transforma a task executada em conhecimento reutilizavel. Analisa descricao, plano, commits e diffs para extrair aprendizados. Faz Q&A com o usuario para capturar decisoes nao visiveis no codigo. Registra tudo no knowledge.md para consulta em tasks futuras.

## Skills auxiliares

| Skill | Descricao |
|-------|-----------|
| **review** | Revisao automatica em 2 modos: descricao vs plano (`--plan`) e plano vs execucao (`--execution`). Gera relatorios sem corrigir — a skill chamadora decide. |
| **status** | Dashboard que mostra todas as tasks, em qual fase cada uma esta, branch atual e pendencias. |
| **update-plan** | Permite alterar o plano durante a implementacao. Mantém historico de alteracoes e roda review apos atualizar. |
| **code-like-me** | Implementacao cirurgica. Garante que o codigo escrito e indistinguivel do codigo existente no projeto. Usado como flag do implement. |

## Estrutura do projeto

```
GDD/
├── skill.md                          # Orquestradora principal
├── README.md
└── sub-skills/
    ├── install/skill.md
    ├── init/skill.md
    ├── plan/skill.md
    ├── implement/skill.md
    ├── pack-up/skill.md
    ├── learn/skill.md
    ├── review/skill.md
    ├── status/skill.md
    ├── update-plan/skill.md
    └── code-like-me/skill.md
```

## Estrutura gerada no projeto do usuario (apos install)

```
GDD/
├── knowledge.md                # Registro de tasks finalizadas (commits, arquivos, aprendizados) — escrito apenas pela skill `learn`
├── pack-up-instructions.md     # Convencoes de branch, commit, PR, testes, acoes finais
└── tasks/
    └── {cod-da-task}/
        ├── description.md      # Descricao, links Jira/Figma, Q&A, commits de referencia
        ├── plan.md             # Plano de implementacao
        └── status.md           # Estado atual da task (fase, branch, updated_at) — escrito por cada step do ciclo
```

### Arquivo `status.md` (por task)

Cada task tem um `status.md` com YAML frontmatter que registra em que fase a task esta. Isso permite que a skill `status` leia o estado direto, sem precisar inferir a partir de arquivos e estado do git.

```yaml
---
phase: implementing
updated_at: 2026-04-15T14:30:00Z
updated_by: implement
branch: task/PROJ-123/add-phone-field
---
```

Valores possiveis de `phase`:

| Valor | Quando | Escrito por |
|-------|--------|-------------|
| `initialized` | Task criada, aguardando plano | `init` |
| `planned` | Plano aprovado, aguardando implementacao | `plan` |
| `implementing` | Implementacao em andamento | `implement` |
| `implemented` | Implementacao concluida, aguardando pack-up | `implement` |
| `packed-up` | PR criado, aguardando learn | `pack-up` |
| `learned` | Knowledge registrado, task finalizada | `learn` |

## Integracoes opcionais

- **Jira (Atlassian MCP)** — Busca automatica de titulo, descricao, links do Figma e contexto da task
- **Figma (Figma MCP)** — Analise de design durante o planejamento e implementacao

Nenhuma integracao e obrigatoria. Sem elas, o framework funciona com input manual.

## Primeiros passos

1. Instale a skill GDD no seu Claude Code
2. Rode `install` no seu projeto
3. Preencha o `GDD/pack-up-instructions.md` com as convencoes do seu projeto
4. Rode `init` com o codigo da sua primeira task
5. Siga o ciclo: `plan` → `implement` → `pack-up` → `learn`

## Recuperacao

Se voce parou no meio de uma task, rode `status` para ver onde parou. A orquestradora detecta a fase automaticamente e sugere o proximo passo.

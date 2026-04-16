# GOD — Goal Oriented Development

Meta framework de skills para desenvolvimento orientado a objetivos. Orquestra o ciclo de vida completo de uma task — da coleta de requisitos até a entrega do PR — usando sub-skills especializadas que se comunicam entre si.

## Como funciona

O GOD cria uma camada de gestao por cima do seu projeto. Ao instalar, ele gera uma pasta `GOD/` que armazena o estado de cada task: descricao, plano, status, knowledge acumulado, convencoes e hooks.

Cada etapa do desenvolvimento e coberta por uma sub-skill dedicada. A skill orquestradora sabe qual chamar, verifica pre-requisitos e sugere o proximo passo.

## Ciclo de vida

```
install -> init -> plan -> implement -> pack-up
                    ^        ^            ^
                 review   review      review
                 (plan)  (update)   (execution)
```

1. **install** — Configura o projeto. Cria a pasta `GOD/`, arquivo `VERSION`, templates de `knowledge.md`, `patterns.md` e `hooks.md`. Verifica MCPs opcionais (Figma, Jira). Executar apenas uma vez.

2. **init** — Inicializa uma task. Recebe link do Jira, codigo da task ou descricao manual. Busca dados no Jira, coleta links do Figma, consulta knowledge por tasks semelhantes, faz Q&A com o usuario e salva tudo em `description.md`.

3. **plan** — Cria o plano de implementacao. Analisa a descricao, commits de referencia, design do Figma, arquivos de convencao do projeto (`CLAUDE.md`, `ARCHITECTURE.md`, `AGENTS.md`), tira duvidas e escreve o plano. Roda review automatica antes de finalizar.

4. **implement** — Executa o plano. Tasks simples sao executadas diretamente. Tasks complexas sao divididas em subagents paralelos. Suporta flag `--code-like-me` para implementacao cirurgica que segue exatamente os padroes do projeto.

5. **pack-up** — Finaliza a task. Roda review plano vs execucao, commit, push e cria PR seguindo os padroes definidos em `patterns.md`. Acoes executaveis (marcar PR como draft, adicionar labels, notificar canais, atualizar tickets) ficam nos hooks `before pack-up` e `after pack-up`. **Nao escreve no knowledge** — isso e responsabilidade exclusiva da skill `learn`.

## Ferramentas auxiliares (nao sao parte do fluxo linear)

| Skill | Descricao |
|-------|-----------|
| **review** | Revisao automatica em 2 modos: descricao vs plano (`--plan`) e plano vs execucao (`--execution`). Gera relatorios sem corrigir — a skill chamadora decide. |
| **status** | Dashboard que mostra todas as tasks, em qual fase cada uma esta, branch, se foi aprendida e quantos PRs tem. |
| **update-plan** | Permite alterar o plano durante a implementacao. Mantem historico de alteracoes e roda review apos atualizar. |
| **learn** | Transforma uma task executada em conhecimento reutilizavel. **Unica skill autorizada a escrever em `GOD/knowledge.md`**. Ativada explicitamente pelo usuario apos o pack-up. Marca `learned: true` no `status.md` sem alterar `phase`. |
| **clean-up** | Verifica tasks em `packed-up` cujos PRs ja foram mergiados e arquiva suas pastas em `GOD/tasks/.archived/`. Oferece rodar `learn` antes de arquivar tasks ainda nao aprendidas. Requer `gh` CLI. |
| **code-like-me** | Implementacao cirurgica. Garante que o codigo escrito e indistinguivel do codigo existente no projeto. Usado como flag do implement. |
| **upgrade** | Migra instalacoes do GOD entre versoes (ex: v1 -> v2 -> v3). Expansivel: cada bump de versao adiciona um arquivo em `sub-skills/upgrade/migrations/`. |

## Hooks do fluxo

Cada step do fluxo principal (`init`, `plan`, `implement`, `pack-up`) executa hooks opcionais antes e depois de sua logica principal. Os hooks sao lidos de `GOD/hooks.md` e escritos em linguagem natural.

Se o slot esta com `skip-hook`, a skill pula. Se tem instrucoes, a skill executa.

**Ferramentas auxiliares** (`learn`, `clean-up`, `update-plan`, `review`, `status`, `code-like-me`, `upgrade`) **nao tem hooks** — sao acionadas explicitamente pelo usuario.

Exemplos de uso:
- `before pack-up`: rodar specs e lint antes do commit
- `after pack-up`: marcar PR como draft, adicionar labels, remover reviewers, notificar canal do Slack, atualizar status no Jira
- `before init`: validar que o usuario esta no ambiente correto

## Estrutura do projeto

```
GOD/
├── SKILL.md                             # Orquestradora principal
├── README.md
└── sub-skills/
    ├── install/SKILL.md
    ├── init/SKILL.md
    ├── plan/SKILL.md
    ├── implement/SKILL.md
    ├── pack-up/SKILL.md
    ├── learn/SKILL.md
    ├── review/SKILL.md
    ├── status/SKILL.md
    ├── update-plan/SKILL.md
    ├── clean-up/SKILL.md
    ├── code-like-me/SKILL.md
    └── upgrade/
        ├── SKILL.md                     # Orquestrador de migracoes
        └── migrations/
            ├── v1-to-v2.md              # Tutorial v1 -> v2
            └── v2-to-v3.md              # Tutorial v2 -> v3 (GDD -> GOD rename)
```

## Estrutura gerada no projeto do usuario (apos install)

```
GOD/
├── VERSION                 # Versao instalada (atualmente v3)
├── knowledge.md            # Registro de tasks finalizadas — escrito apenas pela skill `learn`
├── patterns.md             # Convencoes do projeto: branch, commit, PR, acoes finais
├── hooks.md                # Pontos de extensao por step (before/after de init, plan, implement, pack-up)
└── tasks/
    ├── .archived/          # Tasks arquivadas pela skill `clean-up` (pode nao existir)
    │   └── {cod}/
    └── {cod-da-task}/
        ├── description.md  # Descricao, links Jira/Figma, Q&A, commits de referencia
        ├── plan.md         # Plano de implementacao
        └── status.md       # Estado atual da task (fase, branch, learned, prs, updated_at)
```

### Arquivo `VERSION`

Uma unica linha com a versao instalada, ex: `v3`. Usado pela skill `upgrade` para detectar migracoes necessarias.

### Arquivo `patterns.md`

**Apenas padroes** (nao contem acoes executaveis). Preenchido pelo usuario apos o install. Contem 4 secoes:

- **Branch inicial** — nome(s) do branch base. Suporta multiplos projetos se o repositorio hospedar varios.
- **Padrao de nome de branch** — formato esperado para branches de task
- **Padrao de mensagem de commit** — estrutura do commit (header, body, footer, idioma, tipos permitidos)
- **Padrao de mensagem de PR** — titulo, corpo, idioma, secoes obrigatorias

Lido por `init` (branch inicial + padrao de nome de branch) e `pack-up` (padrao de commit + padrao de PR).

Acoes executaveis (criar PR em draft, adicionar labels, rodar testes/lint, notificar Slack, atualizar Jira) nao ficam aqui — vao para `hooks.md`.

### Arquivo `hooks.md`

Template com 8 slots (before/after para cada step do fluxo):

```markdown
# before init
skip-hook

# after init
skip-hook

# before plan
skip-hook

...
```

Usuario substitui `skip-hook` por instrucoes em linguagem natural quando quer que algo seja executado naquele momento. Cada skill le seu slot correspondente e executa.

### Arquivo `status.md` (por task)

Cada task tem um `status.md` com YAML frontmatter que registra em que fase a task esta. Isso permite que a skill `status` leia o estado direto, sem precisar inferir a partir de arquivos e estado do git.

```yaml
---
phase: packed-up
updated_at: 2026-04-15T14:30:00Z
updated_by: pack-up
branch: task/PROJ-123/add-phone-field
learned: false
prs:
  - https://github.com/org/vakinha-api/pull/123
  - https://github.com/org/vakinha-web/pull/456
---
```

**Campos:**

| Campo | Descricao | Escrito por |
|-------|-----------|-------------|
| `phase` | Fase atual no fluxo (ver enum abaixo) | `init`, `plan`, `implement`, `pack-up` |
| `updated_at` | Timestamp ISO 8601 UTC da ultima atualizacao | todos que modificam o status |
| `updated_by` | Nome da skill que fez a ultima atualizacao | todos que modificam o status |
| `branch` | Nome do branch da task | `init` |
| `learned` | `true` se a task ja passou pelo `learn`. Campo ortogonal ao `phase` | `init` (inicializa `false`), `learn` (flipa `true`) |
| `prs` | Array de URLs de PRs criados para esta task (pode ter mais de um em monorepos) | `pack-up` (append a cada execucao) |

**Valores possiveis de `phase`:**

| Valor | Quando | Escrito por |
|-------|--------|-------------|
| `initialized` | Task criada, aguardando plano | `init` |
| `planned` | Plano aprovado, aguardando implementacao | `plan` |
| `implementing` | Implementacao em andamento | `implement` |
| `implemented` | Implementacao concluida, aguardando pack-up | `implement` |
| `packed-up` | PR(s) criado(s). Fase final do fluxo principal | `pack-up` |

> Observacao: `learn` nao altera `phase` — apenas marca `learned: true`. A task continua em `packed-up` mesmo apos o learn.

## Integracoes opcionais

- **Jira (Atlassian MCP)** — Busca automatica de titulo, descricao, links do Figma e contexto da task
- **Figma (Figma MCP)** — Analise de design durante o planejamento e implementacao
- **GitHub CLI (`gh`)** — Usado pelo `pack-up` para criar PRs e pelo `clean-up` para verificar status de merge. Altamente recomendado

Nenhuma integracao e obrigatoria. Sem Jira/Figma, o framework funciona com input manual. Sem `gh`, `pack-up` e `clean-up` ficam degradados (criacao e verificacao manuais).

## Primeiros passos

1. Instale a skill GOD no seu Claude Code
2. Rode `install` no seu projeto
3. Preencha o `GOD/patterns.md` com as convencoes do seu projeto
4. (Opcional) Preencha os slots de `GOD/hooks.md` que voce quer customizar
5. Rode `init` com o codigo da sua primeira task
6. Siga o ciclo: `plan` -> `implement` -> `pack-up`
7. (Opcional) Rode `learn` quando quiser transformar a task em conhecimento reutilizavel
8. (Opcional) Rode `clean-up` periodicamente para arquivar tasks com PRs ja mergiados

## Upgrade entre versoes

Se voce tem uma instalacao antiga do GOD (v1) e pulou para uma versao mais nova do framework (v2+):

1. Rode `upgrade` — a skill detecta automaticamente a versao instalada e aplica as migracoes em cadeia
2. Os valores configurados (convencoes, tasks, knowledge) sao preservados e reformatados conforme a nova estrutura
3. Arquivos antigos (ex: `pack-up-instructions.md`) sao removidos apenas apos confirmacao

Novas versoes do GOD adicionam migracoes em `sub-skills/upgrade/migrations/vN-to-vN+1.md`, tornando a skill expansivel indefinidamente.

## Recuperacao

Se voce parou no meio de uma task, rode `status` para ver onde parou. A orquestradora detecta a fase automaticamente (via `GOD/tasks/{cod}/status.md`) e sugere o proximo passo.

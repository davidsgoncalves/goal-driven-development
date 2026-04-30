# GOD — Goal Oriented Development

Meta framework de skills para desenvolvimento orientado a objetivos com **spec-driven development** integrado. Orquestra o ciclo de vida completo de uma task — da spec à entrega do PR — usando sub-skills especializadas que se comunicam entre si.

## Como funciona

O GOD cria uma camada de gestao por cima do seu projeto. Ao instalar, ele gera uma pasta `GOD/` que armazena o estado de cada task: description, plano, status, knowledge acumulado, convencoes e hooks. A **spec** de cada task vive **fora** da pasta `GOD/`, em path configurável (`specs_path`), porque é artefato canônico do produto e deve ser committada/lida por todos — independente de quem usa o GOD.

Cada etapa do desenvolvimento e coberta por uma sub-skill dedicada. A skill orquestradora sabe qual chamar, verifica pre-requisitos e sugere o proximo passo.

## Ciclo de vida

```
install -> init -> spec -> plan -> implement -> pack-up
                    ^        ^        ^            ^
                 review   review   review      review
                 (spec)   (plan) (update)   (execution)
```

1. **install** — Configura o projeto. Cria a pasta `GOD/`, arquivo `VERSION`, templates de `knowledge.md`, `patterns.md`, `learned-patterns.md`, `hooks.md`, e o `config.md` com `specs_path` (perguntado ao usuário). Verifica MCPs opcionais (Figma, Jira). Executar apenas uma vez.

2. **init** — Inicializa uma task. Recebe link do Jira, codigo da task ou descricao manual. Salva o input bruto em `description.md` — sem enriquecer, sem buscar Jira, sem tocar em git.

3. **spec** — Produz a spec canônica em `<specs_path>/{cod}.md`. Busca dados em Jira/Figma, faz Q&A focada **exclusivamente em escopo** (proibido falar de implementação), escreve REQs em formato EARS (`WHEN ... THEN ... SHALL ...`), ACs com IDs estáveis (`AC-NNN.N`), cenários (happy/edge/erro) e NFRs (performance, segurança, a11y, observabilidade). Roda `review --spec` antes de finalizar. **A spec é o contrato** que o resto do fluxo consome.

4. **plan** — Lê a spec pronta e produz o plano técnico. Detecta single vs multi-project (`git rev-parse --show-toplevel`), resolve a(s) branch(es) (nome + base) usando `patterns.md`, consulta knowledge por padrões técnicos e escreve o plano focado em **HOW** (arquitetura, arquivos, passos). Cada passo do plano referencia ACs específicos da spec. **Não toca em escopo** — escopo é responsabilidade da skill `spec`.

5. **implement** — Cria a(s) branch(es) da task no git, lê spec + plano, executa os passos. Tasks simples são executadas diretamente; tasks complexas são divididas em subagents paralelos. **Por padrão aplica `code-like-me`** (use `--skip-code-like-me` para desativar). A spec é consultada repetidamente — cada AC é a "definição de pronto" do passo correspondente do plano. Após escrever, roda verificação contra `learned-patterns.md`.

6. **pack-up** — Finaliza a task. Roda review plano vs execução, commit, push e cria PR seguindo os padrões em `patterns.md`. **Anexa link da spec no corpo do PR automaticamente** quando `spec_path` está populado em `status.md`. Ações executáveis (marcar PR como draft, adicionar labels, notificar canais, atualizar tickets) ficam nos hooks `before pack-up` e `after pack-up`. **Não escreve no knowledge** — isso é responsabilidade exclusiva da skill `learn`.

## Ferramentas auxiliares (nao sao parte do fluxo linear)

| Skill | Descricao |
|-------|-----------|
| **review** | Revisao automatica em 3 modos: spec (`--spec` com semantica profunda; `--quick` skipa pra so lint), descricao+spec vs plano (`--plan`), plano vs execucao (`--execution`). A partir da v8.1, cada modo delega pra subagent isolado (fresh eyes, sem vies de auto-validacao). Gera relatorios sem corrigir — a skill chamadora decide. |
| **publish-spec** | Publica/republica a spec em destinos configuraveis (Jira, Slack, stdout, custom). Auxiliar manual ao hook `after spec`. Aceita `--target` (repetivel) e `--dry-run`. |
| **coverage** | Gera matriz AC × validacao pra uma task dentro do fluxo do GOD. Parseia `// covers: AC-X` em testes + le `coverage.md` (validacoes manuais). Usado pelo `pack-up` e `review --execution`, ou manual a qualquer momento. Tolerante por design — ACs orfaos viram alerta visual, nao falha de processo. |
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
├── SDD-ROADMAP.md                       # Roadmap de evolução pra Spec-Driven Development
└── sub-skills/
    ├── install/SKILL.md
    ├── init/SKILL.md
    ├── init-tree/SKILL.md
    ├── spec/SKILL.md                    # NOVO em v6: produz a spec canônica. v7: ganha --review-feedback e hooks before/after
    ├── publish-spec/SKILL.md            # NOVO em v7: publica/republica spec em targets externos
    ├── coverage/SKILL.md                # NOVO em v8: matriz AC × validação por task
    ├── plan/SKILL.md
    ├── implement/SKILL.md               # v8: passo 5.5 anota `// covers: AC-X` nos testes
    ├── pack-up/SKILL.md                 # v8: passo 4.5 chama coverage e injeta tabela no PR
    ├── learn/SKILL.md
    ├── review/SKILL.md                  # 3 modos: --spec (semântica profunda em v7), --plan, --execution (cobertura em v8)
    ├── status/SKILL.md
    ├── update-plan/SKILL.md
    ├── pause/SKILL.md
    ├── resume/SKILL.md
    ├── clean-up/SKILL.md
    ├── code-like-me/SKILL.md
    └── upgrade/
        ├── SKILL.md                     # Orquestrador de migracoes
        └── migrations/
            ├── v1-to-v2.md
            ├── v2-to-v3.md              # GDD -> GOD rename
            ├── v3-to-v4.md              # pause/resume + changelog
            ├── v4-to-v5.md              # learned-patterns
            ├── v5-to-v6.md              # spec extraída + config.md + specs_path
            ├── v6-to-v7.md              # hooks spec + review profundo + freshness check + publish-spec
            └── v7-to-v8.md              # coverage AC × validação + tabela no PR
```

## Estrutura gerada no projeto do usuario (apos install)

```
GOD/
├── VERSION                 # Versao instalada (atualmente v8)
├── config.md               # Configuracao local: specs_path (root do repo de specs)
├── knowledge.md            # Registro de tasks finalizadas — escrito apenas pela skill `learn`
├── patterns.md             # Convencoes do projeto: branch, commit, PR, acoes finais
├── learned-patterns.md     # Regras generalizaveis aprendidas em PRs (escopo: geral/lang/projeto)
├── hooks.md                # Pontos de extensao por step (before/after de init, plan, implement, pack-up)
└── tasks/
    ├── .archived/          # Tasks arquivadas pela skill `clean-up` (pode nao existir)
    │   └── {cod}/
    ├── {cod-do-pai}/       # Pasta de contexto criada por `init-tree` (Epic/Story/pai). Contem apenas description.md com kind: context
    │   └── description.md
    └── {cod-da-task}/
        ├── description.md  # Input bruto do usuario (Jira link, codigo, ou texto manual). Frontmatter kind: task
        ├── plan.md         # Plano tecnico de implementacao (primeira secao = "Branch de trabalho")
        ├── changelog.md    # Documento de continuidade: progresso incremental do implement + blocos de pause/resume (criado sob demanda)
        ├── coverage.md     # (v8, sob demanda) Validacoes manuais + cache da matriz AC × validacao
        └── status.md       # Estado atual da task (fase, paused, spec_path, spec_version_consumed, branch, branch_base, learned, prs, updated_at)

<specs_path>/               # Repo de specs (root configurado em GOD/config.md, FORA da pasta GOD/)
├── README.md               # Explica estrutura e convencoes — gerado pelo install/spec na primeira vez
├── tasks/                  # Spec autocontida por task (escrita pela skill `spec`)
│   └── {cod-da-task}.md    # REQs em EARS, ACs numerados, cenarios, NFRs
├── domains/                # (reservado) Feature specs eternas — populado por skill futura (v9)
└── flows/                  # (reservado) Indices que amarram multiplas features — populado por skill futura
```

A spec mora separada do GOD/ porque é **artefato do produto**, não do workflow individual. A pasta `GOD/` pode ser ignorada do git (privada do dev), enquanto `<specs_path>/` é committada e lida por todos.

### Cenários de configuracao do `specs_path`

O `specs_path` é configurável no `install`. Quatro cenários comuns:

| Cenário | Path típico | Quando usar |
|---------|-------------|-------------|
| **Local no repo** | `docs/specs/` | Single-project, time pequeno, specs pertencem ao próprio repo |
| **Repo dedicado no workspace** | `./vakinha-specs/` (multi-project) ou `../vakinha-specs/` (single-project) | Multi-project workspace, specs visíveis pra todos os repos |
| **Repo dedicado em qualquer lugar** | `/Users/eu/projetos/empresa-specs/` | Path absoluto livre, usado quando specs vivem fora dos workspaces de código |
| **Pasta sem git** | qualquer um dos acima | Specs documentadas mas não versionadas separadamente |

O `install` (e a migration v5→v6) detectam o contexto (`git rev-parse --show-toplevel`) e oferecem opções calibradas. Se a pasta não existe, oferecem criar; se não é repo git, oferecem `git init`.

### Arquivo `VERSION`

Uma unica linha com a versao instalada, ex: `v4`. Usado pela skill `upgrade` para detectar migracoes necessarias.

### Arquivo `patterns.md`

**Apenas padroes** (nao contem acoes executaveis). Preenchido pelo usuario apos o install. Contem 5 secoes:

- **Branch inicial** — nome(s) do branch base. Suporta multiplos projetos se o repositorio hospedar varios.
- **Padrao de nome de branch** — formato esperado para branches de task
- **Padrao de mensagem de commit** — estrutura do commit (header, body, footer, idioma, tipos permitidos)
- **Padrao de mensagem de PR** — titulo, corpo, idioma, secoes obrigatorias
- **Status Jira a ignorar em batch** — lista de status que `init-tree` deve pular ao processar folhas em lote. Opcional (default: Done, Cancelled, Closed, Resolved, Won't Do)

Lido por `plan` (branch inicial + padrao de nome de branch, para resolver branch da task), `pack-up` (padrao de commit + padrao de PR) e `init-tree` (status a ignorar).

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
spec_path: docs/specs/PROJ-123.md
branch: task/PROJ-123/add-phone-field
branch_base: main
learned: false
prs:
  - https://github.com/org/vakinha-api/pull/123
  - https://github.com/org/vakinha-web/pull/456
---
```

**Campos:**

| Campo | Descricao | Escrito por |
|-------|-----------|-------------|
| `phase` | Fase atual no fluxo (ver enum abaixo) | `init`, `spec`, `plan`, `implement`, `pack-up` |
| `updated_at` | Timestamp ISO 8601 UTC da ultima atualizacao | todos que modificam o status |
| `updated_by` | Nome da skill que fez a ultima atualizacao | todos que modificam o status |
| `spec_path` | Caminho do arquivo `<cod>.md` no `specs_path` configurado | `init` (inicializa `null`), `spec` (popula com path) |
| `branch` | Nome do branch da task | `init` (inicializa `null`), `plan` (resolve) |
| `branch_base` | Branch base do PR | `init` (inicializa `null`), `plan` (resolve) |
| `learned` | `true` se a task ja passou pelo `learn`. Campo ortogonal ao `phase` | `init` (inicializa `false`), `learn` (flipa `true`) |
| `prs` | Array de URLs de PRs criados para esta task (pode ter mais de um em monorepos) | `pack-up` (append a cada execucao) |

**Valores possiveis de `phase`:**

| Valor | Quando | Escrito por |
|-------|--------|-------------|
| `initialized` | Task criada, aguardando spec | `init` |
| `specified` | Spec produzida e revisada, aguardando plano | `spec` |
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
2. Rode `install` no seu projeto — vai perguntar `specs_path` (default: `docs/specs/`)
3. Preencha o `GOD/patterns.md` com as convencoes do seu projeto
4. (Opcional) Edite `GOD/config.md` se quiser ajustar o `specs_path` depois
5. (Opcional) Preencha os slots de `GOD/hooks.md` que voce quer customizar
6. Rode `init` com o codigo da sua primeira task
7. Siga o ciclo: `spec` -> `plan` -> `implement` -> `pack-up`
8. (Opcional) Rode `learn` quando quiser transformar a task em conhecimento reutilizavel
9. (Opcional) Rode `clean-up` periodicamente para arquivar tasks com PRs ja mergiados

## Upgrade entre versoes

Se voce tem uma instalacao antiga do GOD (v1) e pulou para uma versao mais nova do framework (v2+):

1. Rode `upgrade` — a skill detecta automaticamente a versao instalada e aplica as migracoes em cadeia
2. Os valores configurados (convencoes, tasks, knowledge) sao preservados e reformatados conforme a nova estrutura
3. Arquivos antigos (ex: `pack-up-instructions.md`) sao removidos apenas apos confirmacao

Novas versoes do GOD adicionam migracoes em `sub-skills/upgrade/migrations/vN-to-vN+1.md`, tornando a skill expansivel indefinidamente.

## Recuperacao

Se voce parou no meio de uma task, rode `status` para ver onde parou. A orquestradora detecta a fase automaticamente (via `GOD/tasks/{cod}/status.md`) e sugere o proximo passo.

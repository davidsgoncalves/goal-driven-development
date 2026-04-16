---
name: init
description: |
  Cria a estrutura de uma nova task no projeto: branch (single-project) ou delegação para `plan` (multi-project), pasta em `GOD/tasks/` e os arquivos `description.md` (com o input bruto do usuário), `plan.md` (vazio) e `status.md` (fase `initialized`). Não busca dados no Jira, não consulta knowledge, não faz Q&A — isso é responsabilidade da skill `plan`. Use quando o usuário mencionar: "nova task", "iniciar task", "init", "criar task", ou quando a fase de inicialização for ativada pelo GOD.
tools: Read, Glob, Grep, Bash, Edit, Write
---

# Init — Sub-skill de Inicialização de Task

> Cria a estrutura base de uma nova task. Salva o input do usuário sem enriquecer. O trabalho de enriquecimento (Jira, Figma, knowledge, Q&A) acontece na skill `plan`.

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

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos **na ordem**:

### 0. Executar hook `before init`

Ler `GOD/hooks.md` e localizar a seção `# before init`.

- Se o conteúdo for `skip-hook`: pular e seguir para o passo 1.
- Se houver instruções em linguagem natural: executá-las integralmente antes de prosseguir. Se as instruções falharem ou pedirem confirmação, pausar e consultar o usuário.

### 1. Detectar contexto: single-project vs multi-project workspace

Antes de ler convenções, identificar se o diretório atual é um projeto único ou um workspace com múltiplos projetos:

- Executar `git rev-parse --show-toplevel` no diretório atual.
  - **Se o comando sucede** e retorna um caminho: é um repositório git (single-project). Seguir o fluxo normal de branch nesta skill.
  - **Se o comando falha** (erro "not a git repository"): o diretório atual é um workspace (ex: pasta que contém múltiplos projetos, cada um com seu próprio `.git`). **Modo multi-project ativo.**

No **modo multi-project**, o `init` não tem contexto suficiente para decidir em qual(is) projeto(s) o branch da task deve ser criado — isso depende do escopo da task, que só fica claro após o enriquecimento (Jira, Figma, Q&A). Portanto, **pular toda a lógica de git (passo 4)** e delegar a organização de branches para a skill `plan`. Continuar executando os demais passos normalmente, porém com `branch: null` em `status.md`.

### 2. Ler convenções de branch no `patterns.md`

Ler `GOD/patterns.md` e extrair:

- **Branch inicial** — nome do branch base. Se o repositório contém múltiplos projetos com branches diferentes, identificar qual aplica ao projeto corrente (pelo diretório ou perguntando ao usuário). No modo multi-project, esta informação é apenas lida para referência — o `plan` usará para criar branches depois.
- **Padrão de nome de branch** — formato a ser seguido ao criar o branch da task (ex: `task/<cod-da-task>/<descrição-kebab-case>`).

No modo single-project, esses valores são obrigatórios para o passo 4. No modo multi-project, apenas o **padrão de nome de branch** é necessário aqui (o branch inicial por projeto será relido pelo `plan`).

### 3. Receber input da task

O usuário deve fornecer **uma** das seguintes opções:

- **Link do Jira** — ex: `https://empresa.atlassian.net/browse/PROJ-123` → extrair o código (`PROJ-123`) da URL
- **Código da task** — ex: `PROJ-123` → usar direto
- **Nome/descrição manual** — texto livre. Neste caso, pedir ao usuário um código ou nome curto para identificar a task (ex: `minha-task`)

Se o padrão de branch (passo 2) exige um segmento de descrição (ex: `<descrição-kebab-case>`) e o input do usuário não fornece algo claro, perguntar ao usuário uma descrição curta para compor o nome do branch.

**Não buscar dados no Jira nesta skill.** Apenas capturar o input. A skill `plan` fará o fetch do Jira quando for elaborar o plano.

### 4. Verificar estado do git e criar o branch da task

> **Pular este passo inteiro se o modo multi-project foi detectado no passo 1.** A criação dos branches nos projetos afetados será feita pela skill `plan` após o enriquecimento da descrição.

Com o branch inicial e o padrão de nome de branch (passo 2) e o cod-da-task + descrição (passo 3) em mãos:

1. Verificar se o usuário está no branch inicial (`git branch --show-current`)
2. Verificar se existem alterações não commitadas (`git status`)

**Se o branch está correto e não há alterações pendentes:**
- `git pull` para atualizar o branch inicial
- Criar o branch da task aplicando o **padrão de nome de branch** (ex: `task/PROJ-123/add-phone-field`)
- Se o pull falhar (ex: conflitos remotos), avisar o usuário e aguardar orientação antes de continuar

**Se o branch está errado OU existem alterações não commitadas:** apresentar as seguintes opções ao usuário:

> ⚠️ Foram detectadas pendências no git antes de iniciar a task:
> - [Branch atual: `X` — esperado: `Y`] (se aplicável)
> - [Alterações não commitadas detectadas] (se aplicável)
>
> Escolha uma opção:
> 1. **Reverter e continuar** — descarta as alterações, faz checkout no branch inicial e cria o branch da nova task
> 2. **Criar apenas as pastas** — cria a estrutura da task em `GOD/tasks/` mas não mexe no git. Resolva as pendências manualmente e rode o init novamente
> 3. **Abortar** — cancela o init sem fazer nada

Aguardar a escolha do usuário e agir conforme:
- **Opção 1:** `git checkout -- .` + `git checkout {branch-inicial}` + `git pull` + criar branch da task aplicando o **padrão de nome de branch** lido no passo 2
- **Opção 2:** pular para o passo 5 (criar estrutura sem mexer no git) e encerrar após criar as pastas
- **Opção 3:** encerrar sem executar nada

### 5. Criar estrutura da task

Criar a seguinte estrutura em `GOD/tasks/`:

```
GOD/tasks/{cod-da-task}/
├── description.md
├── plan.md
└── status.md
```

**`description.md`** — preencher com estrutura mínima contendo **apenas o input bruto do usuário**:

```markdown
# {cod-da-task}

## Input do usuário

{input bruto conforme fornecido — link do Jira, código puro, ou texto manual}

---

> Esta descrição está bruta. A skill `plan` irá enriquecê-la com:
> - dados do Jira (se houver código/link)
> - links do Figma encontrados no Jira
> - referências a tasks semelhantes do `knowledge.md`
> - perguntas e respostas esclarecendo escopo e edge cases
```

**`plan.md`** — criar vazio, será preenchido pela skill `plan`.

**`status.md`** — criar com YAML frontmatter registrando o estado inicial:

```yaml
---
phase: initialized
updated_at: {timestamp-iso-8601-utc}
updated_by: init
branch: {nome-do-branch-criado-ou-null-se-opcao-2}
learned: false
prs: []
---
```

- `phase`: sempre `initialized` neste passo
- `updated_at`: timestamp ISO 8601 em UTC (ex: `2026-04-15T14:30:00Z`)
- `updated_by`: sempre `init` neste passo
- `branch`: nome do branch criado no passo 4 (single-project). Deixar `null` se: (a) o usuário escolheu a opção 2 ("Criar apenas as pastas"), ou (b) o modo multi-project foi detectado no passo 1 — nesse caso o `plan` vai popular este campo ao organizar os branches.
- `learned`: sempre `false` neste passo. Será flipado para `true` pela skill `learn` quando o usuário escolher transformar a task em conhecimento.
- `prs`: sempre `[]` neste passo. Será populado pela skill `pack-up` a cada PR criado.

### 6. Executar hook `after init`

Ler `GOD/hooks.md` e localizar a seção `# after init`.

- Se o conteúdo for `skip-hook`: pular e seguir para o passo 7.
- Se houver instruções em linguagem natural: executá-las integralmente antes do relatório final.

### 7. Reportar resultado

> ✅ Task `{cod-da-task}` inicializada!
>
> 🌿 Branch: `{nome-do-branch}` (ou "não criado" se opção 2, ou "será organizado pelo `plan`" se modo multi-project)
> 📄 `GOD/tasks/{cod-da-task}/description.md` — input bruto salvo (aguardando enriquecimento pelo `plan`)
> 📋 `GOD/tasks/{cod-da-task}/plan.md` — aguardando planejamento
> 📍 `GOD/tasks/{cod-da-task}/status.md` — fase: `initialized`
>
> 💡 Próximo passo: rode `plan` — ela vai buscar dados no Jira, consultar knowledge, fazer Q&A com você e então escrever o plano de implementação. [Em modo multi-project: o `plan` também vai criar os branches nos projetos afetados após entender o escopo.]
>
> [Se hooks before/after foram executados, listar resumidamente o que rodou]

---

## Guard-rails

- **Esta skill não escreve em `GOD/knowledge.md`.** Apenas a skill `learn` pode fazê-lo.
- **Esta skill não busca dados em sistemas externos** (Jira, Figma). O fetch e a consulta ao knowledge são responsabilidade da skill `plan`.
- **Esta skill não faz Q&A com o usuário sobre a task.** O esclarecimento de escopo acontece na skill `plan`, quando há mais contexto coletado.

---
name: init
description: |
  Cria a estrutura de uma nova task no projeto: pasta em `GOD/tasks/` e os arquivos `description.md` (com o input bruto do usuário), `plan.md` (vazio) e `status.md` (fase `initialized`). Não toca no git, não busca dados no Jira, não consulta knowledge, não faz Q&A — isso é responsabilidade das skills `plan` e `implement`. Use quando o usuário mencionar: "nova task", "iniciar task", "init", "criar task", ou quando a fase de inicialização for ativada pelo GOD.
tools: Read, Glob, Grep, Bash, Edit, Write
---

# Init — Sub-skill de Inicialização de Task

> Cria a estrutura base de uma nova task em `GOD/tasks/`. Salva o input do usuário sem enriquecer. O trabalho de enriquecimento (Jira, Figma, knowledge, Q&A, resolução de branch) acontece na skill `plan`. A criação da branch no git acontece na skill `implement`.

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

## Invocação programática

Esta skill pode ser invocada:

- **Interativamente pelo usuário** (fluxo padrão) — quando o usuário digita "nova task", "init", passa um código ou link do Jira, etc.
- **Programaticamente pela skill `init-tree`** — a skill `init-tree` chama `init` para cada folha da árvore Jira que ela está processando. Nesse caso, o código da task e a descrição já vêm no contexto da chamada, dispensando qualquer Q&A interativo.

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos **na ordem**:

### 0. Executar hook `before init`

Ler `GOD/hooks.md` e localizar a seção `# before init`.

- Se o conteúdo for `skip-hook`: pular e seguir para o passo 1.
- Se houver instruções em linguagem natural: executá-las integralmente antes de prosseguir. Se as instruções falharem ou pedirem confirmação, pausar e consultar o usuário.

### 1. Receber input da task

O usuário deve fornecer **uma** das seguintes opções (ou a skill chamadora já fornece no contexto):

- **Link do Jira** — ex: `https://empresa.atlassian.net/browse/PROJ-123` → extrair o código (`PROJ-123`) da URL
- **Código da task** — ex: `PROJ-123` → usar direto
- **Nome/descrição manual** — texto livre. Neste caso, pedir ao usuário um código ou nome curto para identificar a task (ex: `minha-task`)

**Não buscar dados no Jira nesta skill.** Apenas capturar o input bruto. A skill `plan` fará o fetch do Jira quando for elaborar o plano.

### 2. Criar estrutura da task

Criar a seguinte estrutura em `GOD/tasks/`:

```
GOD/tasks/{cod-da-task}/
├── description.md
├── plan.md
└── status.md
```

**`description.md`** — preencher com frontmatter mínimo + input bruto do usuário:

```markdown
---
kind: task
parent: null
---

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

**Sobre o frontmatter:**
- `kind: task` — sinaliza que a pasta representa uma task real (com plan + implement). Contrasta com `kind: context` usado pelo `init-tree` em nós pai/intermediários.
- `parent: null` — task solta, sem pai. Quando chamado por `init-tree`, o valor pode ser o código do nó imediatamente acima na árvore do Jira (ex: `parent: PROJ-101`).

**`plan.md`** — criar vazio, será preenchido pela skill `plan`.

**`status.md`** — criar com YAML frontmatter registrando o estado inicial:

```yaml
---
phase: initialized
updated_at: {timestamp-iso-8601-utc}
updated_by: init
branch: null
branch_base: null
learned: false
prs: []
---
```

- `phase`: sempre `initialized` neste passo
- `updated_at`: timestamp ISO 8601 em UTC (ex: `2026-04-15T14:30:00Z`)
- `updated_by`: sempre `init` neste passo
- `branch`: sempre `null`. A skill `plan` resolve o nome da branch da task; a skill `implement` cria de fato no git.
- `branch_base`: sempre `null`. A skill `plan` resolve o branch base (dependente de patterns + multi-project).
- `learned`: sempre `false`. Será flipado para `true` pela skill `learn` quando o usuário escolher transformar a task em conhecimento.
- `prs`: sempre `[]`. Será populado pela skill `pack-up` a cada PR criado.

### 3. Executar hook `after init`

Ler `GOD/hooks.md` e localizar a seção `# after init`.

- Se o conteúdo for `skip-hook`: pular e seguir para o passo 4.
- Se houver instruções em linguagem natural: executá-las integralmente antes do relatório final.

### 4. Reportar resultado

> ✅ Task `{cod-da-task}` inicializada!
>
> 📄 `GOD/tasks/{cod-da-task}/description.md` — input bruto salvo (aguardando enriquecimento pelo `plan`)
> 📋 `GOD/tasks/{cod-da-task}/plan.md` — aguardando planejamento
> 📍 `GOD/tasks/{cod-da-task}/status.md` — fase: `initialized`, branch: `null` (será resolvida pelo `plan` e criada pelo `implement`)
>
> 💡 Próximo passo: rode `plan` — ela vai buscar dados no Jira, consultar knowledge, resolver a branch da task (nome + base) e escrever o plano de implementação.
>
> [Se hooks before/after foram executados, listar resumidamente o que rodou]

Se a skill foi invocada pelo `init-tree`, o relatório final é consolidado pela skill chamadora; aqui basta retornar controle silenciosamente após a criação bem-sucedida.

---

## Guard-rails

- **Esta skill não toca no git.** Não faz checkout, não cria branch, não valida estado. A resolução do nome da branch é responsabilidade do `plan`; a criação física é do `implement`.
- **Esta skill não escreve em `GOD/knowledge.md`.** Apenas a skill `learn` pode fazê-lo.
- **Esta skill não busca dados em sistemas externos** (Jira, Figma). O fetch e a consulta ao knowledge são responsabilidade da skill `plan`.
- **Esta skill não faz Q&A com o usuário sobre a task.** O esclarecimento de escopo acontece na skill `plan`, quando há mais contexto coletado.
- **Esta skill não lê `GOD/patterns.md`.** A resolução de branch (single-project) e a organização de branches (multi-project) migraram para o `plan` (resolução) e `implement` (criação física).

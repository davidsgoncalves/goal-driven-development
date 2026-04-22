---
name: install
description: |
  Configura a arquitetura de pastas e arquivos GOD no projeto do usuário e verifica integrações MCP opcionais. Use quando o usuário mencionar: "instalar god", "install", "configurar god", "setup god", ou na primeira execução do framework.
tools: Read, Glob, Grep, Bash, Edit, Write
---

# Install — Sub-skill de Instalação

> Configura a arquitetura de pastas e arquivos GOD no projeto do usuário e verifica integrações MCP opcionais.

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

### 0. Verificar se já existe instalação anterior

Antes de qualquer coisa, verificar o estado das pastas no diretório raiz.

- **Se `GOD/` existe e tem `GOD/VERSION` com conteúdo `v4`:** informar que o projeto já está instalado na versão atual e encerrar.
- **Se `GOD/` existe mas `GOD/VERSION` não existe (ou aponta pra versão anterior):** informar que é uma instalação de versão antiga e sugerir rodar a skill `upgrade` em vez de reinstalar. Não sobrescrever arquivos existentes.
- **Se `GOD/` não existe mas `GDD/` existe:** instalação legada da skill GDD detectada. Informar o usuário e sugerir rodar `upgrade` (ou `migrate`) para migrar automaticamente de GDD para GOD. Não instalar do zero — os dados do usuário (tasks, knowledge, patterns, hooks) serão preservados pela migração. Encerrar sem criar nada.
- **Se nem `GOD/` nem `GDD/` existem:** prosseguir com a instalação.

### 1. Criar estrutura GOD

No diretório raiz do projeto do usuário, crie a seguinte estrutura:

```
GOD/
├── VERSION
├── knowledge.md
├── patterns.md
├── hooks.md
└── tasks/
```

- `VERSION` — arquivo com conteúdo `v4` (uma linha, sem espaços)

- `knowledge.md` — criado com template padrão (ver seção abaixo)
- `patterns.md` — criado com template padrão (ver seção abaixo)
- `hooks.md` — criado com template padrão (ver seção abaixo)
- `tasks/` — pasta vazia para armazenar tasks do projeto

### 2. Preencher template do `VERSION`

Conteúdo exato:

```
v4
```

### 3. Preencher template do `knowledge.md`

O arquivo `GOD/knowledge.md` deve ser criado com o seguinte template:

```markdown
# Knowledge — Registro de Tasks

> Registro de tasks finalizadas com referências de commit e aprendizados. Usado pelo `init` para encontrar tasks semelhantes e pelo `plan` para aproveitar decisões anteriores. **Escrito apenas pela skill `learn`** — nenhuma outra skill modifica este arquivo.

## Tasks finalizadas

<!-- Formato:
### {cod-da-task} — {breve descrição}
- **commits:** {hash1}, {hash2}, ...
- **arquivos principais:** {lista dos arquivos mais relevantes}
- **aprendizados:** {o que foi aprendido, decisões tomadas, armadilhas evitadas}
-->
```

### 4. Preencher template do `patterns.md`

O arquivo `GOD/patterns.md` deve ser criado com o seguinte template para o usuário preencher:

```markdown
# Patterns — Convenções do projeto

> Este arquivo define **apenas os padrões** do projeto: branches, commits, PRs e filtros auxiliares. Lido pelas skills `plan` (branch inicial + padrão), `pack-up` (commit + PR) e `init-tree` (status Jira a ignorar).
> Ações executáveis (criar PR em draft, rodar testes, notificar canais, atualizar tickets) ficam no `hooks.md`.

## Branch inicial
Descreva aqui o branch inicial (ex: `main`, `master`, `develop`).
Se o repositório contém múltiplos projetos com branches diferentes, liste cada um.

Exemplo:
- projeto-web — `develop`
- projeto-api — `main`

## Padrão de nome de branch
Descreva o padrão esperado para nomes de branches de task.
Ex: `task/<cod-da-task>/<descrição-em-ingles-kebab-case>`

## Padrão de mensagem de commit
Descreva o formato esperado do commit (header, body, footer, idioma, tipos permitidos).

## Padrão de mensagem de PR
Descreva o formato do título e corpo do PR, idioma e seções obrigatórias.

## Status Jira a ignorar em batch
Lista de status do Jira que `init-tree` deve pular ao processar folhas (subtasks) em lote. Se a seção estiver ausente ou vazia, o default é: `Done`, `Cancelled`, `Closed`, `Resolved`, `Won't Do`.

Exemplo (um por linha, nome exato como aparece no Jira):
- Done
- Cancelled
- Closed
- Resolved
- Won't Do
```

### 5. Preencher template do `hooks.md`

O arquivo `GOD/hooks.md` deve ser criado com o seguinte template:

```markdown
# Hooks — Pontos de extensão por step

> Cada seção abaixo é um hook opcional. Se você quiser que algo seja executado antes ou depois de um step do fluxo, escreva aqui em linguagem natural — a skill correspondente vai ler e executar.
> Se não quer nada nesse hook, deixe o valor `skip-hook`.
>
> Apenas os steps do fluxo principal têm hooks: `init`, `plan`, `implement`, `pack-up`.
> Ferramentas auxiliares (`learn`, `update-plan`, `review`, `status`) não têm hooks.

# before init
skip-hook

# after init
skip-hook

# before plan
skip-hook

# after plan
skip-hook

# before implement
skip-hook

# after implement
skip-hook

# before pack-up
skip-hook

# after pack-up
skip-hook
```

Após criar, informe ao usuário que ele deve preencher o `patterns.md` com as convenções do projeto e, opcionalmente, preencher os hooks no `hooks.md`.

### 6. Gitignore (opcional)

Pergunte ao usuário se deseja adicionar a pasta `GOD/` ao `.gitignore` do projeto.

- **Se sim:** adicione `GOD/` ao `.gitignore` existente (ou crie o arquivo se não existir)
- **Se não:** siga para o próximo passo

### 7. Verificar integrações opcionais

Verifique o que está disponível no ambiente do usuário:

- **Figma** (`claude.ai Figma` MCP) — verificar se está disponível e autenticado. Melhora `plan` e `implement` com análise de design.
- **Jira/Atlassian** (`claude.ai Atlassian` MCP) — verificar se está disponível e autenticado. Permite que `plan` busque dados da task automaticamente.
- **GitHub CLI (`gh`)** — executar `gh --version` e `gh auth status` para verificar instalação e autenticação. É **altamente recomendado** porque:
  - O `pack-up` usa `gh pr create` para abrir PRs
  - O `clean-up` usa `gh pr view` para verificar status de merge dos PRs

Nenhuma dessas integrações é obrigatória, mas sem `gh` a experiência do `pack-up` e do `clean-up` fica degradada (criação manual de PR, verificação manual de merge).

### 8. Reportar resultado

Montar a resposta listando o que está ok e o que está faltando:

```
✅ Instalação v4 concluída! Estrutura GOD criada.

🔌 Integrações:
  [✓/✗] Figma MCP — {status}
  [✓/✗] Jira (Atlassian) MCP — {status}
  [✓/✗] GitHub CLI (gh) — {status}

{Se algum item estiver ✗, sugerir conexão/instalação com link apropriado:}
  - Figma: conectar MCP em Claude
  - Jira: conectar MCP em Claude
  - gh: https://cli.github.com (depois `gh auth login`)

📋 Próximos passos:
  1. Preencha `GOD/patterns.md` com as convenções do seu projeto
  2. (Opcional) Preencha slots de `GOD/hooks.md` que você quer customizar
  3. Rode `init` para iniciar sua primeira task
```

---

## Guard-rails

- **Esta skill não escreve em `GOD/knowledge.md`** (apenas cria o arquivo vazio com template). Atualizações de conteúdo são responsabilidade exclusiva de `learn`.
- **Esta skill não sobrescreve instalações existentes.** Se detectar uma versão anterior já instalada, orienta o usuário a rodar `upgrade` ou nenhuma ação.

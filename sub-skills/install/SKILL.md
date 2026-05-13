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

- **Se `GOD/` existe e tem `GOD/VERSION` com conteúdo `v11`:** informar que o projeto já está instalado na versão atual e encerrar.
- **Se `GOD/` existe mas `GOD/VERSION` não existe (ou aponta pra versão anterior):** informar que é uma instalação de versão antiga e sugerir rodar a skill `upgrade` em vez de reinstalar. Não sobrescrever arquivos existentes.
- **Se `GOD/` não existe mas `GDD/` existe:** instalação legada da skill GDD detectada. Informar o usuário e sugerir rodar `upgrade` (ou `migrate`) para migrar automaticamente de GDD para GOD. Não instalar do zero — os dados do usuário (tasks, knowledge, patterns, hooks) serão preservados pela migração. Encerrar sem criar nada.
- **Se nem `GOD/` nem `GDD/` existem:** prosseguir com a instalação.

### 1. Criar estrutura GOD

No diretório raiz do projeto do usuário, crie a seguinte estrutura:

```
GOD/
├── VERSION
├── config.md
├── knowledge.md
├── patterns.md
├── learned-patterns.md
├── hooks.md
└── tasks/
```

- `VERSION` — arquivo com conteúdo `v11` (uma linha, sem espaços)
- `config.md` — configuração local do GOD nesse projeto (ver passo 1.5 abaixo). Contém `specs_path` (onde a spec da task vai morar)
- `knowledge.md` — criado com template padrão (ver seção abaixo)
- `patterns.md` — criado com template padrão (ver seção abaixo)
- `learned-patterns.md` — criado com template padrão (ver seção abaixo)
- `hooks.md` — criado com template padrão (ver seção abaixo)
- `tasks/` — pasta vazia para armazenar tasks do projeto

### 1.5. Configurar `specs_path` e criar `GOD/config.md`

A partir da v6, a spec de cada task vive **fora** da pasta `GOD/`. Motivo: a spec é ativo canônico do produto — committada e lida por todos —, enquanto a pasta `GOD/` é workflow individual e pode ser ignorada do git.

**Conceito-chave:** o `specs_path` é o **root do repo de specs**, não a pasta direto onde as tasks são escritas. O GOD escreve em `<specs_path>/tasks/<cod>.md`. Subpastas como `domains/` e `flows/` são reservadas pra skills futuras (feature specs eternas, fluxos cross-feature) — não criadas agora.

#### 1.5.1. Detectar contexto e apresentar opções

Antes de perguntar, **detectar o contexto** rodando `git rev-parse --show-toplevel` no diretório atual:

- **Sucesso (está dentro de repo git)** → contexto **single-project**: dentro de um repositório.
- **Falha** → contexto **workspace multi-project**: pasta-mãe contendo múltiplos repos.

Apresentar opções calibradas pelo contexto:

**Se single-project:**

```
📐 Onde guardar as specs das tasks?

A spec é artefato canônico do produto — committável separadamente, lida por todos.

Opções:
  1. docs/specs/                                  (default — dentro deste repo)
  2. ../<workspace>/<nome-do-repo-de-specs>/      (repo dedicado ao lado deste, no workspace pai)
  3. <path-absoluto>                              (qualquer outro lugar — você digita)
  4. <outro-relativo>                             (qualquer outro path relativo a aqui)

Escolha (1/2/3/4) ou tecle Enter pra default:
```

**Se multi-project workspace:**

```
📐 Onde guardar as specs das tasks?

Detectei que você está num workspace multi-project (pasta sem .git contendo repos).
Recomendado: repo dedicado de specs ao lado dos repos de código.

Opções:
  1. ./<nome-do-repo-de-specs>/    (repo dedicado neste workspace — recomendado)
  2. <path-absoluto>               (qualquer outro lugar — você digita)
  3. <outro-relativo>              (qualquer outro path relativo a aqui)

Escolha (1/2/3) ou tecle Enter pra opção 1:
```

#### 1.5.2. Resolver e criar a estrutura

Com o `specs_path` decidido, executar:

1. **Se a pasta não existe**: criar com `mkdir -p <specs_path>`.
2. **Se a pasta existe e não é repo git**: perguntar `"Inicializar como repo git separado? (s/n)"`. Se sim, rodar `git init` lá. Se não, prosseguir como pasta normal.
3. **Se a pasta existe e já é repo git**: usar como está. Não tocar.
4. **Criar subpasta `tasks/`** dentro do `specs_path` (`mkdir -p <specs_path>/tasks/`).
5. **Criar README mínimo** em `<specs_path>/README.md` se não existir (ver template abaixo). Se já existir, não tocar.
6. **Não criar `domains/` nem `flows/` agora** — reservados pra skills futuras escreverem sob demanda.

Template do `<specs_path>/README.md`:

```markdown
# Specs

Repositório canônico de specs do produto. Cada spec é o **contrato de escopo** de uma feature/task — REQs em formato EARS, ACs com IDs estáveis, cenários e NFRs explícitos.

## Estrutura

```
specs/
├── tasks/                # Spec autocontida por task (uma por entrega)
│   └── <cod>.md          # ex: PROJ-123.md
├── domains/              # (reservado) Feature specs eternas por domínio do produto
└── flows/                # (reservado) Índices que amarram múltiplas features (jornadas e2e)
```

`tasks/` é populado pelo framework GOD (skill `spec`) na fase de SDD por task.
`domains/` e `flows/` serão populados por skills futuras quando feature specs eternas e fluxos cross-feature forem suportados.

## Convenções

- Toda spec começa com frontmatter: `spec_version`, `task`, `created_at`, `updated_at`.
- ACs têm IDs estáveis: `AC-NNN.N` (ex: `AC-001.2`). Não renomear depois de citar em código/teste.
- Specs não falam de implementação — proibido mencionar framework, biblioteca, banco. Isso é HOW, vai pro plan da task.
- Specs são commitadas como artefato de produto. Histórico via `git log`.
```

#### 1.5.3. Criar `GOD/config.md`

Conteúdo:

```markdown
# Config — Configuração local do GOD

> Configuração específica desta instalação do GOD no projeto. Diferente do `patterns.md`,
> que descreve convenções **do projeto** (lidas por todos), este arquivo descreve onde o
> GOD escreve/lê **artefatos** dentro do filesystem. Pode variar entre desenvolvedores se
> a pasta `GOD/` estiver no `.gitignore`.

## specs_path

Root do repo de specs. O GOD escreve em `<specs_path>/tasks/<cod>.md`. Subpastas
`domains/` e `flows/` são reservadas pra skills futuras.

Aceita relativo (resolve a partir do diretório onde o GOD foi instalado) ou absoluto.

{specs_path}

> Cenários:
> - Local no repo: `docs/specs/`
> - Workspace multi-project: `./myorg-specs/` ou `../myorg-specs/`
> - Repo separado em qualquer lugar: `/Users/eu/projetos/<workspace>/<repo-de-specs>/`

## publish_spec_default_target

Default usado pela sub-skill `publish-spec` quando `--target` não é passado.
Aceita um único target ou múltiplos separados por vírgula.

Valores conhecidos: `jira`, `slack`, `stdout`, `notion`. Targets customizados
exigem definição em `GOD/hooks.md` como `# publish-spec target: <nome>`.

(deixe vazio pra usar `stdout` como default original)

> Exemplos:
> - `jira` — toda execução de `publish-spec` sem flag publica no Jira
> - `jira, slack` — publica nos dois ao mesmo tempo
> - (vazio) — comportamento original: `stdout`

## principles_path

(v10) Caminho para o arquivo de princípios do projeto. Lido pelo `plan` para gerar
o bloco "Considerações arquiteturais". Bullets curtos, projeto-específicos.

(deixe vazio pra desativar — `plan` pula o bloco quando não há principles configurado)

{principles_path}

> Cenários:
> - Default no GOD: `GOD/principles.md`
> - No repo de specs: `<specs_path>/principles.md`
> - Em outro lugar do código: `docs/principles.md`

## architecture_path

(v10) Caminho para o arquivo de arquitetura do projeto. Lido pelo `plan` junto com
principles. Padrões "preferidos mas negociáveis" (3-5 padrões).

(deixe vazio pra desativar)

{architecture_path}

## domains_path

(v10) Caminho para a **pasta** de domínios. Cada arquivo `<dominio>.md` declara
regras de negócio (BRs) com IDs derivados do `domain:` do frontmatter
(ex: `domain: payments` → `BR-PAYMENTS-NNN`). Lido pelo `spec` (sugere
applicable_rules), `implement` (sugere `// rule: BR-X`) e `pack-up` (tabela no PR).

(deixe vazio pra desativar — fluxo passa silenciosamente sem mencionar BRs)

{domains_path}

> Cenários:
> - Default no repo de specs: `<specs_path>/domains/`
> - No GOD: `GOD/domains/` (raro — domains são canônicos do produto)

## peer_review_default

(v10.3) Modo de execução do `review --spec/--plan/--execution`.

Valores aceitos:
- `subagent` (**default**) — review roda em subagent isolado com contexto fresco. Fresh eyes anti-viés. Custa ~1.5x-2x tokens vs inline.
- `inline` — review roda na própria skill chamadora. **Perde fresh eyes anti-viés**, mas economiza tokens. Use em projeto pequeno/solo onde o tradeoff compensa.
- `skip` — não roda review automaticamente. Pra ambientes restritos ou pipelines onde peer-review é etapa separada.

subagent

> Override pontual via flag CLI: `review --execution --inline` força inline nesta invocação sem mudar config.

## reviewers

(v12) Lista de GitHub handles que a skill `ready` adiciona como reviewers do PR ao tirar de draft.
Um handle por linha, sem `@`. Linhas vazias e linhas começando com `#` são ignoradas.

(deixe vazio pra `ready` rodar sem adicionar reviewers — só tira de draft)

```
# alice
# bob
# carol
```

> Cenários:
> - Time pequeno: 1-3 handles fixos, sempre os mesmos
> - Round-robin: usuário gerencia manualmente comentando/descomentando linhas
> - Sem reviewers automáticos: deixe vazio, `ready` apenas tira de draft
```

Substituir `{specs_path}` pelo valor decidido. As seções `publish_spec_default_target`, `principles_path`, `architecture_path` e `domains_path` ficam vazias por padrão (retrocompat — quem não ativar não enxerga diferença). Se o usuário inicializou como repo git separado nesse passo, anotar isso no relatório final.

### 1.6. Ativar artefatos opcionais (v10)

A v10 introduziu 3 artefatos **opcionais** que ativam advisor de arquitetura e regras de negócio. Pra cada um, perguntar ao usuário se quer ativar agora. Default: pular (pode rodar `install` de novo ou editar `config.md` manualmente depois).

**1.6.1. Princípios (`principles.md`)**

```
🏛️  Quer ativar princípios do projeto?

`principles.md` contém bullets curtos com decisões duradouras do projeto
(ex: "PII de doador anônimo nunca é exposta em log/métrica"). Lido pelo
`plan` pra gerar o bloco "Considerações arquiteturais".

Opções:
  1. Sim, default em GOD/principles.md
  2. Sim, em outro caminho (você digita)
  3. Pular (pode ativar depois editando GOD/config.md)

Escolha (1/2/3) ou Enter pra pular:
```

- **(1)** → criar arquivo vazio em `GOD/principles.md` com template neutro (abaixo). Popular `principles_path` no `config.md`.
- **(2)** → perguntar caminho (relativo resolve a partir do GOD; absoluto OK). Criar arquivo vazio. Popular `config.md`.
- **(3)** → deixar `principles_path:` vazio. Pular criação.

Template do `principles.md` (neutro, sem hardcode de projeto):

```markdown
# Princípios

> Decisões duradouras do projeto. Bullets curtos, projeto-específicos.
> Lido pela skill `plan` para gerar o bloco "Considerações arquiteturais".
> Sem isto, o `plan` pula esse bloco silenciosamente.

<!-- Exemplos do que cabe aqui (apague depois de preencher os seus):
- "<área> é evento contábil — nunca alterar valor pós-confirmação"
- "FE não fala com banco direto — sempre via API"
- "PII de <ator> nunca é exposta em log/métrica"
-->
```

**1.6.2. Arquitetura (`architecture.md`)**

Pergunta análoga, com texto:

> 🏗️ Quer ativar arquitetura do projeto?
>
> `architecture.md` lista 3-5 padrões "preferidos mas negociáveis" (ex:
> "controllers finos, lógica em service objects"). Lido junto com principles
> pelo `plan`.

Mesmo fluxo de opções (1/2/3). Template:

```markdown
# Arquitetura

> Padrões "preferidos mas negociáveis" do projeto. Lido pela skill `plan`
> junto com principles.

## Camadas

<!-- Ex: Controllers finos / lógica em service objects / repositories isolam DB
     Apague e escreva os seus.
-->

## Convenções

<!-- Ex: feature folders, não tipo-folders / DTOs com Zod / etc. -->
```

**1.6.3. Domínios (`domains/`)**

Pergunta análoga:

> 📜 Quer ativar regras de negócio (domains)?
>
> `domains/<dominio>.md` declara invariantes do domínio (BRs). IDs viram
> `BR-<DOMINIO>-NNN` derivado do frontmatter de cada arquivo. Lido pelo
> `spec` (sugere applicable_rules), `implement` (sugere `// rule:` no código)
> e `pack-up` (tabela no PR).

Opções:

```
  1. Sim, default em <specs_path>/domains/
  2. Sim, em outro caminho (você digita)
  3. Pular (pode ativar depois)
```

- **(1)** → criar pasta `<specs_path>/domains/` (vazia). Popular `domains_path`.
- **(2)** → criar pasta no caminho fornecido. Popular `config.md`.
- **(3)** → pular.

**Não criar arquivo `domains/<exemplo>.md` automaticamente.** Domínios são responsabilidade do usuário (cada projeto tem seus). GOD apenas cria a pasta vazia. Quando o usuário criar o primeiro arquivo, deve seguir esta estrutura:

```markdown
---
domain: <nome-em-lowercase>
domain_version: 1
---

# Domain — <nome bonito>

## BR-<DOMINIO_UPPER>-001: <nome curto>
**INVARIANT** <sujeito> **SHALL** <comportamento invariante>.
**Why:** <motivo — incidente, regulação, decisão consciente>.

## BR-<DOMINIO_UPPER>-002: ...
```

> O sufixo `<DOMINIO_UPPER>` no ID é **derivado do `domain:` do frontmatter**, em uppercase. GOD nunca prescreve nome de domínio — você escolhe.

### 2. Preencher template do `VERSION`

Conteúdo exato:

```
v11
```

### 3. Copiar templates pra `GOD/` (lazy load v10.2)

Os templates dos arquivos abaixo vivem em `sub-skills/install/templates/*.tmpl` e são copiados pra `GOD/` durante a instalação. Não estão mais inline na skill — economia de tokens cada vez que `install` é carregada.

Pra cada arquivo, copiar o template correspondente:

| Destino | Template |
|---------|----------|
| `GOD/knowledge.md` | `sub-skills/install/templates/knowledge.md.tmpl` |
| `GOD/patterns.md` | `sub-skills/install/templates/patterns.md.tmpl` |
| `GOD/learned-patterns.md` | `sub-skills/install/templates/learned-patterns.md.tmpl` |
| `GOD/hooks.md` | `sub-skills/install/templates/hooks.md.tmpl` |
| `GOD/principles.md` *(opcional, v10)* | `sub-skills/install/templates/principles.md.tmpl` |
| `GOD/architecture.md` *(opcional, v10)* | `sub-skills/install/templates/architecture.md.tmpl` |

Operação:
- `cp <template> <destino>` — não substitua se o destino já existe.
- Os arquivos opcionais `principles.md`/`architecture.md` só são copiados se o usuário ativou no passo 1.6.

**Exemplos comuns pra `after spec`** (preenchimento posterior em `hooks.md`):
- Postar comentário no Jira com link da spec + contagem de REQs/ACs.
- Postar mensagem em Slack `#produto` com resumo da spec.
- Linkar URL da spec no card Linear/Trello.

Após criar, oriente o usuário a preencher `patterns.md` com as convenções do projeto e, opcionalmente, os hooks em `hooks.md`.

### 4. Gitignore (opcional)

Pergunte ao usuário se deseja adicionar a pasta `GOD/` ao `.gitignore` do projeto.

- **Se sim:** adicione `GOD/` ao `.gitignore` existente (ou crie o arquivo se não existir)
- **Se não:** siga para o próximo passo

### 5. Verificar integrações e runtime

Verifique o que está disponível no ambiente do usuário:

- **Python 3.8+** (v10.2 — recomendado) — executar `python3 --version` e validar versão >= 3.8. Habilita scripts otimizados em `sub-skills/_lib/` (parsing de cobertura, BRs, etc.) que evitam que o LLM faça trabalho determinístico — economia significativa de tokens em `coverage`, `pack-up`, `review --execution`. Sem `python3`, esses passos caem pro fallback LLM (mais lento e caro). Cross-platform: macOS (Xcode CLI tools ou Homebrew), Linux/WSL (`apt install python3`).
- **Figma** (`claude.ai Figma` MCP) — verificar se está disponível e autenticado. Melhora `plan` e `implement` com análise de design.
- **Jira/Atlassian** (`claude.ai Atlassian` MCP) — verificar se está disponível e autenticado. Permite que `plan` busque dados da task automaticamente.
- **GitHub CLI (`gh`)** — executar `gh --version` e `gh auth status` para verificar instalação e autenticação. É **altamente recomendado** porque:
  - O `pack-up` usa `gh pr create` para abrir PRs
  - O `clean-up` usa `gh pr view` para verificar status de merge dos PRs

Nenhuma dessas integrações é obrigatória, mas sem `gh` a experiência do `pack-up` e do `clean-up` fica degradada (criação manual de PR, verificação manual de merge), e sem `python3` os passos otimizados rodam via LLM (custo elevado de tokens).

> 💡 Após o install, rode `doctor` (v10.2) pra ver diagnóstico completo do ambiente e instruções de correção pra cada item faltante.

### 6. Reportar resultado

Montar a resposta listando o que está ok e o que está faltando:

```
✅ Instalação v10 concluída! Estrutura GOD criada.

📐 Repo de specs configurado: {specs_path}
   • Pasta {criada / já existia}
   • Estrutura {tasks/ criada}
   • README {criado / já existia}
   • git: {repo separado inicializado / repo já existente / pasta dentro do projeto / pasta sem git}

🏛️  Artefatos opcionais (v10):
   • principles_path: {ativado em <path> / desativado}
   • architecture_path: {ativado em <path> / desativado}
   • domains_path: {ativado em <path> / desativado}

🔌 Integrações e runtime:
  [✓/✗] python3 (>= 3.8) — {versão detectada / ausente — fallback LLM ativo}
  [✓/✗] Figma MCP — {status}
  [✓/✗] Jira (Atlassian) MCP — {status}
  [✓/✗] GitHub CLI (gh) — {status}

{Se algum item estiver ✗, sugerir conexão/instalação com link apropriado:}
  - python3: `brew install python3` (macOS) ou `apt install python3` (Linux/WSL) — habilita scripts otimizados
  - Figma: conectar MCP em Claude
  - Jira: conectar MCP em Claude
  - gh: https://cli.github.com (depois `gh auth login`)

📋 Próximos passos:
  1. Preencha `GOD/patterns.md` com as convenções do seu projeto
  2. (Opcional) Preencha slots de `GOD/hooks.md` que você quer customizar
  3. (Opcional, v10) Se ativou principles/architecture/domains, preencha os arquivos com o conteúdo do seu projeto
  4. `GOD/learned-patterns.md` começa vazio — a skill `learn` vai preenchê-lo após a revisão de PR
  5. Rode `init {cod}` para iniciar sua primeira task. Fluxo v11: init → spec → [publish-spec] → plan → implement → pack-up. Pra mudança trivial (typo, copy), use `init {cod} --profile=trivial` e pule direto pro `implement`.
```

---

## Guard-rails

- **Esta skill não escreve em `GOD/knowledge.md` nem em `GOD/learned-patterns.md`** (apenas cria os arquivos vazios com template). Atualizações de conteúdo são responsabilidade exclusiva de `learn`.
- **Esta skill não sobrescreve instalações existentes.** Se detectar uma versão anterior já instalada, orienta o usuário a rodar `upgrade` ou nenhuma ação.

# Migração v1 → v2

## Objetivo

A v2 traz 4 mudanças estruturais:

1. **Divide `pack-up-instructions.md` em dois arquivos:**
   - `patterns.md` — convenções fixas (branch, commit, PR — sem "ações finais" que agora viram hooks)
   - `hooks.md` — pontos de extensão executáveis antes/depois de cada step do fluxo (`init`, `plan`, `implement`, `pack-up`)

2. **Introduz `GDD/VERSION`** — permite detecção de versão em upgrades futuros.

3. **Introduz `GDD/tasks/{cod}/status.md`** — arquivo de status por task. Na v1 a fase era inferida; na v2 cada task tem seu estado explícito. A migração cria esse arquivo retroativamente.

4. **Schema do `status.md` na v2:**
   - `phase` — enum de 5 valores (`initialized`, `planned`, `implementing`, `implemented`, `packed-up`)
   - `learned` (boolean) — se a task já passou pelo `learn`. Campo ortogonal ao `phase`
   - `prs` (array de URLs) — populado pelo `pack-up` a cada PR criado
   - Nota: o valor `learned` como `phase` (que existia em versões iniciais da v1) foi substituído pelo boolean `learned: true` em combinação com `phase: packed-up`

## Arquivos afetados

**Criados:**
- `GDD/VERSION` — conteúdo: `v2`
- `GDD/patterns.md` — convenções fixas (migradas do `pack-up-instructions.md`)
- `GDD/hooks.md` — pontos de extensão (novos, exceto o slot `before pack-up` que recebe o conteúdo de "Processos de finalização" do `pack-up-instructions.md`)

**Removido (após confirmação do usuário):**
- `GDD/pack-up-instructions.md`

**Inalterados (nenhuma reescrita automática):**
- `GDD/knowledge.md`
- `GDD/tasks/{cod}/description.md`, `plan.md`, `status.md`

> ℹ️ **Sobre `description.md` de tasks legadas:**
> Na v1, a skill `init` já gravava a descrição enriquecida (título, descrição completa do Jira, links do Figma, referências do knowledge, Q&A) diretamente no `description.md`. Na v2, a responsabilidade de enriquecer migrou para `plan`, então o `init` v2 grava apenas o input bruto. Isso significa que, ao migrar, **tasks legadas terão o `description.md` no formato "já enriquecido" da v1**.
>
> Isso **não quebra** a v2: a skill `plan` v2 detecta o estado "enriquecido" no passo 2 e confirma com o usuário se quer re-enriquecer ou apenas atualizar o plano. Formatos antigos de seção (ex: "Tasks semelhantes encontradas no knowledge" em vez do v2 "Tasks semelhantes no knowledge") são aceitos — são diferenças cosméticas, não funcionais.
>
> A migração **não reescreve** esses `description.md` automaticamente. Se o usuário quiser padronizar com o template v2, ele pode rodar `plan` novamente e escolher "re-enriquecer" quando a skill perguntar.

## Riscos conhecidos

- Se o `pack-up-instructions.md` do usuário tiver seções renomeadas ou faltando, a migração pode deixar campos em branco. Nesses casos, alertar o usuário e perguntar como preencher.
- Se o usuário tiver editado manualmente a estrutura do `pack-up-instructions.md` (adicionou seções novas), essas seções extras serão movidas pra um bloco `## Outras convenções` no final do `patterns.md` e reportadas pro usuário.
- Se o usuário tiver múltiplos projetos com branches iniciais diferentes (caso do exemplo Vakinha), preservar o formato de lista em `patterns.md`.
- **Tasks legadas no estado `initialized` (pós-`init` v1, pré-`plan` v1):** podem ter descrição parcialmente enriquecida (dependendo de até onde o init v1 chegou antes da interrupção). A v2 aceita ambos os estados, mas vale reportar ao usuário na seção de relatório final quantas tasks em `initialized` existem, para que ele saiba que ao rodar `plan` essas tasks podem ter fluxo diferente.

---

## Passos da migração

Execute os passos **na ordem**. Ao final de cada passo, verifique que o estado esperado está correto antes de prosseguir.

### Passo 1 — Ler o `pack-up-instructions.md` existente

Ler o arquivo `GDD/pack-up-instructions.md` inteiro. Identificar as seguintes seções (pelos títulos de nível 1 `#` ou nível 2 `##`, a depender de como o usuário formatou):

**Seções que viram padrões (vão para `patterns.md`):**
- Branch inicial
- Padrão de nome de branch
- Padrão de mensagem de commit
- Padrão de mensagem de PR

**Seções que viram hooks (vão para `hooks.md`):**
- Processos de finalização → slot `before pack-up`
- Ações finais → slot `after pack-up`

Para cada seção, armazenar o conteúdo (sem o título). Se alguma seção estiver ausente, marcá-la como `MISSING` e incluir no relatório final.

Se houver seções **extras** (não previstas acima), armazenar separadamente para incluir em `## Outras convenções` no `patterns.md`.

### Passo 2 — Criar `GDD/VERSION`

Criar o arquivo `GDD/VERSION` com exatamente uma linha:

```
v2
```

### Passo 3 — Criar `GDD/patterns.md`

Criar o arquivo `GDD/patterns.md` com o seguinte conteúdo, **preenchendo cada seção com os valores capturados no passo 1**:

```markdown
# Patterns — Convenções do projeto

> Este arquivo define **apenas os padrões** do projeto: branches, commits e PRs. Lido pelas skills `init` e `pack-up`.
> Ações executáveis (criar PR em draft, rodar testes, notificar canais, atualizar tickets) ficam no `hooks.md`.

## Branch inicial
{{conteúdo da seção "Branch inicial" do pack-up-instructions.md}}

## Padrão de nome de branch
{{conteúdo da seção "Padrão de nome de branch"}}

## Padrão de mensagem de commit
{{conteúdo da seção "Padrão de mensagem de commit"}}

## Padrão de mensagem de PR
{{conteúdo da seção "Padrão de mensagem de PR"}}
```

**Não incluir seção "Ações finais".** Na v2, as ações pós-PR do usuário migram para o slot `after pack-up` em `hooks.md` (passo 4).

**Regras de preenchimento:**
- Preservar a formatação original do conteúdo (blocos de código, listas, exemplos) — **não** reformatar nem resumir.
- Se uma seção estava marcada como `MISSING`, escrever `_Não configurado — preencher manualmente._` no lugar do conteúdo.
- Se houver seções extras capturadas no passo 1, adicionar ao final:

```markdown
## Outras convenções

{{seções extras, com seus títulos originais}}
```

### Passo 4 — Criar `GDD/hooks.md`

Criar o arquivo `GDD/hooks.md` com o seguinte template. Dois slots recebem conteúdo migrado do `pack-up-instructions.md`:

- `before pack-up` ← **"Processos de finalização"**
- `after pack-up` ← **"Ações finais"**

Os outros seis slots ficam como `skip-hook`.

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
{{conteúdo da seção "Processos de finalização" do pack-up-instructions.md — preservar integralmente}}

# after pack-up
{{conteúdo da seção "Ações finais" do pack-up-instructions.md — preservar integralmente}}
```

**Regras de preenchimento dos slots migrados:**
- Se a seção original existia no `pack-up-instructions.md`, copiar o conteúdo **exatamente como estava** (preservar listas, exemplos, regras específicas por projeto).
- Se a seção **não existia ou estava vazia**, deixar `skip-hook` no slot correspondente.
- Não adicionar comentários nem reformatar — o usuário leu isso antes, precisa continuar fazendo sentido pra ele.

### Passo 5 — Atualizar as tasks existentes (se aplicável)

Verificar cada pasta em `GDD/tasks/`:

1. Se a pasta **não contém `status.md`** (task criada antes de `status.md` existir — possível se o projeto foi instalado antes do fim da v1):
   - Criar `status.md` inferindo a fase a partir dos arquivos existentes:
     - Só `description.md` ou `plan.md` vazio → `phase: initialized`
     - `plan.md` preenchido, sem branch da task ou sem commits → `phase: planned`
     - Branch existe, commits feitos, sem PR → `phase: implemented`
     - PR criado → `phase: packed-up`
   - `updated_by`: `upgrade`
   - `updated_at`: timestamp atual
   - `branch`: tentar identificar pelo git (buscar branch cujo nome contém o código da task), ou deixar `null` se não encontrar
   - `learned`: `false` — a migração não tenta inferir se a task foi aprendida. Se o usuário já rodou `learn` nessa task antes, ele pode editar o arquivo manualmente ou rodar `learn` de novo (é idempotente no knowledge.md)
   - `prs`: `[]` — array vazio. A migração não tenta recuperar URLs de PRs antigos. Se a task estiver em `packed-up` e o usuário quiser usar `clean-up`, ele precisa popular `prs` manualmente com as URLs dos PRs já criados, OU rodar `pack-up` novamente (que vai criar um novo PR e popular)

2. Se a pasta **já contém `status.md`** mas é do formato v1 (sem `learned` e sem `prs`):
   - **Adicionar** os campos ausentes ao frontmatter:
     - `learned: false`
     - `prs: []`
   - **Não alterar** `phase`, `updated_at`, `updated_by`, `branch`
   - **Se o valor antigo de `phase` era `learned`** (único caso em que v1 tinha esse valor mas v2 não tem):
     - Alterar `phase` para `packed-up`
     - Setar `learned: true`
     - `updated_by: upgrade` e `updated_at` atualizado (para rastrear a migração)

3. Se a pasta **já contém `status.md` completo** (todos os campos v2): não alterar.

**Não reescrever `description.md`.** O formato enriquecido da v1 (gravado pelo `init` v1, que buscava Jira/Figma/knowledge/Q&A) é aceito pela v2 como estado "já enriquecido". A skill `plan` v2 vai detectar e oferecer re-enriquecer ou apenas atualizar o plano.

**Contagem para o relatório final:** enquanto percorre as tasks, contar quantas estão em cada fase (especialmente `initialized`) para reportar no passo 7.

### Passo 6 — Confirmar remoção do `pack-up-instructions.md`

Perguntar ao usuário:

> O conteúdo de `GDD/pack-up-instructions.md` foi migrado para `GDD/patterns.md` e `GDD/hooks.md`. Como deseja tratar o arquivo antigo?
>
> 1. **Remover** — deletar `GDD/pack-up-instructions.md`
> 2. **Renomear para .bak** — manter como `GDD/pack-up-instructions.md.bak` para referência
> 3. **Manter** — deixar intocado (não recomendado; pode causar confusão)

Agir conforme a escolha.

### Passo 7 — Reportar resultado

Apresentar ao usuário:

```
✅ Migração v1 → v2 aplicada!

Arquivos criados:
  - GDD/VERSION (v2)
  - GDD/patterns.md
  - GDD/hooks.md

{Se tasks foram atualizadas, listar quantas e quais fases foram inferidas}

Tasks legadas no estado `initialized`: {N}
  ⚠️ Essas tasks têm `description.md` no formato enriquecido da v1. Ao rodar
  `plan` nelas, a skill vai detectar e perguntar se você quer re-enriquecer
  (rebuscar Jira/Figma/knowledge) ou apenas atualizar o plano.

{Se houve seções MISSING no pack-up-instructions.md original, listar aqui}
{Se houve seções extras realocadas em "Outras convenções", listar aqui}

{Ação aplicada ao pack-up-instructions.md: removido / renomeado / mantido}

📋 Revise `patterns.md` e `hooks.md` — os valores foram preservados do arquivo original, mas vale conferir a formatação e preencher eventuais lacunas.
```

Ao final, **a skill orquestradora de upgrade** (`sub-skills/upgrade/SKILL.md`) atualiza `GDD/VERSION` para `v2` (embora este passo também já faça). Se a cadeia tiver mais migrações depois desta (ex: v2→v3), a orquestradora prossegue; caso contrário, encerra o upgrade com sucesso.

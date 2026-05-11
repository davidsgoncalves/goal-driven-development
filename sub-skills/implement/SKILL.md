---
name: implement
description: |
  Executa o plano de implementação da task, criando subagents para tasks complexas ou executando diretamente para tasks simples. Por padrão aplica `code-like-me` (modo cirúrgico); use `--skip-code-like-me` para desativar. Use quando o usuário mencionar: "implementar task", "implement", "executar plano", ou quando a fase de implementação for ativada pelo GOD.
tools: Read, Glob, Grep, Bash, Edit, Write, Agent
---

# Implement — Sub-skill de Implementação

> Executa o plano de implementação da task, criando subagents para tasks complexas ou executando diretamente para tasks simples. **Por padrão aplica `code-like-me`** (modo cirúrgico, imitando os devs do projeto). Use `--skip-code-like-me` para desativar.

## Flags

- `--skip-code-like-me` — Desativa a aplicação da sub-skill `code-like-me`. Nesse modo livre, a IA segue o plano e as convenções do projeto, mas tem liberdade para escolher a abordagem sem precisar replicar estilo dev-por-dev. **Sem esta flag, `code-like-me` é aplicado automaticamente.**
- `--skip-patterns-check` — Desativa a verificação contra `GOD/learned-patterns.md` (passo 6.5). Útil quando o usuário quer rodar implement rapidamente sem o ajuste automático de regras. **Sem esta flag, a verificação roda sempre que o arquivo existe e tem pelo menos uma regra.**
- `--debug` *(v10.6)* — registra passos em `debug.log` via `_lib/debug_log.py`. Pontos: freshness (3), preparar git (2.05), execução (5), anotações covers/rules (5.5/5.6), patterns check (6.5). Ver SKILL raiz.

## Otimização v10.2

Esta skill delega tarefas determinísticas pra scripts em `sub-skills/_lib/` quando `python3 ≥ 3.8` está disponível:
- **Freshness check** (passo 3) → `freshness_check.py`
- **Atualizar `status.md`** em qualquer passo (2.1, transições) → `update_status.py`
- **Cobertura final** se chamada → `parse_coverage.py` via skill `coverage`

Falha de script cai pro fallback LLM automaticamente (ver "Delegação pra `_lib/`" no SKILL.md raiz).

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos **na ordem**:

### 0. Executar hook `before implement`

Ler `GOD/hooks.md` e localizar a seção `# before implement`.

- Se o conteúdo for `skip-hook`: pular e seguir para o passo 1.
- Se houver instruções em linguagem natural: executá-las integralmente antes de prosseguir.

### 1. Identificar a task

- Se o contexto da conversa já contém o código da task, usar esse código
- Caso contrário, perguntar ao usuário o código da task (ex: `PROJ-123`)

### 1.5. Detectar fluxo trivial (v11)

Ler `GOD/tasks/{cod-da-task}/status.md` e olhar `phase` + `profile`.

**Se `phase: initialized` E `profile: trivial`:** task é trivial — pula spec e plan inteiros. Implement resolve branch sozinho.

1. **Pular passo 2 (ler spec/plano e freshness)** — não há spec nem plan pra trivial.
2. **Resolver branch + branch_base manualmente:**
   - Ler `GOD/patterns.md` pra obter convenção de nome (`branch_format`, ex: `task/{cod}/{slug}`).
   - Pedir ao usuário um slug curto descrevendo a mudança (ex: `fix-button-copy`). Default: usar o próprio código da task como slug.
   - Resolver `branch_base` lendo `patterns.md` (geralmente `main` ou `develop`).
   - Atualizar `status.md` via `update_status.py`: `branch=<resolvido>`, `branch_base=<resolvido>`.
3. **Saltar pra passo 2.05 (preparar git)** — segue o fluxo normal a partir daí.
4. **Pular passos que dependem de spec/plan:** anotações `// covers: AC-X` (passo 5.5) e `// rule: BR-X` (passo 5.6) **não se aplicam** — task trivial não tem ACs nem BRs aplicáveis registradas.

**Se `phase: initialized` E `profile ∈ {normal, critical}`:** task tem init mas não passou pela spec — orientar o usuário:

> ⚠️ Task `{cod}` ainda está em `phase: initialized` (perfil `{profile}`). Spec ainda não foi escrita.
>
> - Pra rodar implement com escopo formal: rode `spec {cod}` antes (vai abrir Q&A focada em escopo, escrever a spec e atualizar status pra `specified`).
> - Se essa task é trivial e você não quer spec: rode primeiro `init {cod} --profile=trivial` (vai sobrescrever `profile: trivial` no status).

Encerrar.

**Caso contrário (phase ∈ {specified, planned, implementing}):** seguir fluxo normal a partir do passo 2.

### 2. Ler spec e plano, checar freshness

A spec é o **contrato de escopo**; o plano é o **mapa técnico**. Ambos são consumidos:

1. **Ler `GOD/tasks/{cod-da-task}/status.md`** e extrair `spec_path` e `spec_version_consumed`.
   - Se `spec_path` ausente: a task não passou pela `spec`. Orientar a rodar `spec` antes.
2. **Ler a spec** em `<spec_path>` (relativo ao diretório do GOD ou absoluto).
   - Se o arquivo não existe: avisar e pedir confirmação do path atual ou re-rodar `spec`.
   - Extrair REQs, ACs (com IDs estáveis), cenários e NFRs — vão ser referenciados durante a implementação.
   - Extrair `spec_version` do frontmatter da spec.
3. **Freshness check (v7+, estendido na v9, otimizado v10.2):**

   **Caminho preferido (v10.2):** delegar pra `sub-skills/_lib/freshness_check.py --task {cod}`. JSON traz `drift`, `delta`, `changelog_entries`. Pula leitura manual de status.md + spec.md + changelog.md.

   **Fallback (LLM):**
   - Se `spec_version_consumed` é `null` → primeira execução do `implement`, prosseguir.
   - Se `spec_version_consumed` < `spec_version` da spec atual → **a spec mudou desde o último `plan` ou `implement`**. Aplicar **freshness check estendido (v9)**:

     **3.1. Carregar deltas do changelog.**
     Ler `<specs_path>/tasks/{cod}-changelog.md` (se existir — só existe se `update-spec` rodou). Extrair entradas das versões `(spec_version_consumed + 1)` até `spec_version` atual. Para cada uma, capturar:
     - REQs/ACs alterados, adicionados, removidos (da seção "Deltas")
     - "Impacto na execução" (lista de IDs apontada explicitamente pela skill `update-spec`)

     Se o changelog não existir, a mudança veio de edição direta da spec (ou pré-v9). Nesse caso, fazer diff bruto entre versões só é possível se o usuário registrou no git — alertar como degradado:

     > ℹ️ Spec foi alterada sem passar por `update-spec` — não há changelog estruturado. Vou tratar todos os ACs como potencialmente afetados.

     **3.2. Cruzar com cobertura existente.**
     Ler `GOD/tasks/{cod}/coverage.md` (v8) se existir. Para cada AC afetado, identificar:
     - Testes que o cobrem (linhas anotadas via `// covers: AC-X`)
     - Validações manuais registradas
     - Se nenhuma cobertura registrada: AC ainda não foi implementado/validado nesta versão — sem ação especial, só listar.

     **3.3. Apresentar diagnóstico ao usuário.**

     > ⚠️ A spec mudou desde a última execução desta task.
     > - Versão consumida: v{spec_version_consumed}
     > - Versão atual da spec: v{spec_version}
     >
     > **Mudanças:**
     > {por entrada do changelog: motivo + resumo + IDs afetados}
     >
     > **Impacto cruzado com `coverage.md`:**
     > - AC-001.2 (alterado) → testes afetados: `tests/notify.spec.ts:42`, `tests/notify.spec.ts:51`
     > - AC-002.1 (removido) → teste órfão: `tests/legacy.spec.ts:18` (decisão: manter? remover?)
     > - REQ-004 (adicionado) → sem cobertura ainda — **passo novo no plano necessário**
     >
     > Como prosseguir?
     > - (a) Rodar `update-plan` agora pra incorporar mudanças no plano (recomendado se há REQs novos)
     > - (b) Reabrir passos do plano relacionados aos IDs afetados (mostro a lista, você navega item por item)
     > - (c) Prosseguir mesmo assim (assume que o código já está alinhado com a spec nova)
     > - (d) Abortar

     **3.4. Aplicar a escolha.**
     - **(a)** delegar a `update-plan`, depois retornar pro freshness check (loop).
     - **(b)** percorrer a lista — pra cada AC afetado, mostrar arquivos/testes vinculados, perguntar "manter? alterar? remover?"; aplicar mudanças específicas; quando terminar, prosseguir com implement.
     - **(c)** prosseguir, mas **registrar em `changelog.md` da task** (não confundir com changelog da spec) que a versão N foi consumida sem revisão de impacto — fica visível pro pack-up/learn depois.
     - **(d)** abortar sem mexer em nada.

   - Se igual → spec não mudou, prosseguir normalmente.
4. **Ler `GOD/tasks/{cod-da-task}/plan.md`** para obter o plano técnico.
   - Se o plano estiver vazio, informar o usuário que precisa rodar a skill `plan` antes.
   - Se o plano existir, analisar sua estrutura e complexidade.

Durante a implementação, a spec é consultada repetidamente (cada AC é a "definição de pronto" do passo correspondente do plano). O plano é o roteiro; a spec é o critério.

### 2.05. Preparar git (validar estado + criar/ativar branch(es) da task)

Esta skill é responsável pela criação física da(s) branch(es) no git. O `plan` já resolveu nomes e bases — aqui apenas executamos.

1. **Ler `GOD/tasks/{cod-da-task}/status.md`** e identificar o formato do campo `branch`:
   - **String** (ex: `branch: task/PROJ-123/xxx` + `branch_base: main`) → **modo single-project**. Uma branch a criar.
   - **Lista de objetos** (ex: `branch: [{project, name, base}, ...]`) → **modo multi-project workspace**. Uma branch por projeto afetado.
   - **`null` em qualquer lado:** se chegou aqui via passo 1.5 (fluxo trivial), branch foi resolvido naquele passo e o status.md foi atualizado — re-ler. Se mesmo assim continua null ou se veio direto pra cá com phase ≥ specified, a task não foi planejada corretamente — orientar o usuário a rodar `plan` primeiro e encerrar.

2. **Single-project** (uma branch):
   - Verificar se a branch da task já existe localmente (`git rev-parse --verify {branch}`):
     - **Existe:**
       - Se o usuário já está nela (`git branch --show-current == branch`): prosseguir.
       - Se está em outra branch **sem** alterações não commitadas: `git checkout {branch}` e prosseguir.
       - Se está em outra branch **com** alterações não commitadas: apresentar opções ao usuário (ver bloco 4 abaixo).
     - **Não existe:**
       - Se está na `branch_base` limpa: `git pull` + `git checkout -b {branch}`.
       - Se está em outra branch **sem** alterações: `git checkout {branch_base}` + `git pull` + `git checkout -b {branch}`.
       - Se há alterações não commitadas: apresentar opções ao usuário (bloco 4).

3. **Multi-project workspace** (N branches, uma por projeto):
   - Para **cada entrada** `{project, name, base}` da lista no `status.md`:
     1. Fazer `cd {workspace}/{project}` (o `workspace` é o `pwd` atual, já que o modo multi-project foi detectado exatamente por "pwd sem `.git`" no plan).
     2. Aplicar a lógica idêntica do single-project neste diretório: checar existência da branch, criar/checkout, tratar pendências.
     3. Se **algum projeto** tiver pendências, apresentar opções ao usuário (bloco 4) com escopo desse projeto. A escolha vale **apenas para esse projeto** — os demais continuam normalmente.
   - Ao final, o usuário estará no último projeto processado (o `cd` não "volta"). Registrar no report qual é o diretório-base de trabalho esperado.

4. **Opções quando há alterações não commitadas ou estado inesperado (single ou qualquer projeto do multi):**

   > ⚠️ Foram detectadas pendências no git antes de começar a implementação da task `{cod-da-task}` {em `{projeto}` se multi-project}:
   > - [Branch atual: `X` — esperado: `{branch}` ou `{branch_base}`] (se aplicável)
   > - [Alterações não commitadas detectadas] (se aplicável)
   >
   > Escolha uma opção:
   > 1. **Reverter e continuar** — descarta as alterações e procede com a criação/checkout da branch da task
   > 2. **Stash e continuar** — guarda as alterações com `git stash` e procede; você pode recuperar depois com `git stash pop`
   > 3. **Pular este projeto** (apenas multi-project) — segue para o próximo projeto da lista, deixando este inalterado. A task ficará incompleta para este projeto até resolução manual
   > 4. **Abortar** — cancela a execução sem tocar no git

   - **Opção 1:** `git checkout -- .` + (se necessário) `git checkout {base}` + `git pull` + `git checkout -b {name}` (ou checkout direto se já existe)
   - **Opção 2:** `git stash push -m "implement-god {cod-da-task}"` + mesmo fluxo de checkout/criação
   - **Opção 3 (só multi-project):** anotar o projeto pulado no changelog (ver 5.1) e seguir para o próximo
   - **Opção 4:** encerrar silenciosamente

5. **Atualizar `status.md`:**
   - Os campos `branch` / `branch_base` já refletem os nomes resolvidos pelo plan. Se algo mudou durante esta preparação (ex: recriou uma branch manualmente), atualizar.

### 2.1. Atualizar status para `implementing`

Antes de começar a implementação de fato, atualizar `GOD/tasks/{cod-da-task}/status.md`:

- `phase`: `implementing`
- `updated_at`: timestamp ISO 8601 em UTC
- `updated_by`: `implement`
- `branch`, `branch_base`, `learned`, `prs`: preservar valores atuais (branch já existe no git agora, após o passo 2.05)

### 2.2. Garantir existência do `changelog.md`

Verificar se `GOD/tasks/{cod-da-task}/changelog.md` existe.

- **Se não existe**, criar com o header:
  ```markdown
  # Changelog — {cod-da-task}
  ```
- **Se já existe** (ex: criado por uma pausa prévia da skill `plan`, ou por retomada anterior), manter e anexar as próximas entradas ao final.

Este arquivo é o **documento de continuidade** da task. Será atualizado incrementalmente durante toda a implementação (passo 5.1) e é o artefato que `pause`/`resume` manipulam para registrar interrupções e retomadas.

### 2.3. Se a task está retomando de uma pausa, carregar contexto do changelog

Se `status.md` **não** tiver `paused: true` mas o `changelog.md` **tiver** um bloco `▶ RESUME` como última entrada (ou algum bloco `⏸ PAUSE` em algum momento do histórico), significa que a task já foi pausada e retomada antes.

Neste caso:
- Ler o `changelog.md` inteiro para reconstruir o que já foi feito antes da pausa
- Identificar o último passo concluído (última entrada não-PAUSE/RESUME antes do bloco de pausa)
- Retomar a implementação a partir do próximo passo do plano, não reexecutando os passos já registrados no changelog

### 3. Carregar contexto visual (Figma)

Ler o `GOD/tasks/{cod-da-task}/description.md` e verificar se há links do Figma.

Se houver links do Figma:
- Acessar o Figma via MCP Figma (`get_design_context`) para cada link
- Usar o design como referência visual durante a implementação
- Cada subagent que implementar UI deve receber o contexto do Figma relevante ao seu escopo

### 4. Avaliar complexidade e decidir estratégia

Analisar o plano e decidir a estratégia de execução:

**Task simples (sem divisão de sub-tasks no plano):**
- Executar a implementação diretamente, seguindo os passos do plano na ordem

**Task complexa (com múltiplas sub-tasks no plano):**
- Criar um subagent (via Agent tool) para cada sub-task independente
- Sub-tasks que dependem umas das outras devem ser executadas sequencialmente
- Sub-tasks independentes podem ser executadas em paralelo
- Cada subagent recebe:
  - O contexto completo da task (descrição + plano)
  - Apenas o escopo da sua sub-task específica
  - As convenções do projeto (de `CLAUDE.md`, `ARCHITECTURE.md`, etc.)

### 5. Implementar

**Em ambos os modos, validar a cadeia completa sempre que aplicável** — ex: frontend → API → backend → banco. Uma feature não está pronta se só um dos lados foi tocado.

**Modo padrão — `code-like-me` ativo (cirúrgico, imitando os devs do projeto):**
- Aplicar todas as diretrizes da sub-skill `code-like-me` durante a implementação
- Cada mudança deve ser cirúrgica — mínimo impacto, máxima aderência ao código existente
- Encontrar analogias no código existente antes de criar algo novo
- O código produzido deve ser indistinguível do que um dev do projeto escreveria
- Validar cadeia completa (front → API → back → banco) onde aplicável

**Com flag `--skip-code-like-me` (modo livre, seguindo padrões do projeto):**
- Seguir o plano de implementação passo a passo
- Respeitar as convenções do projeto encontradas nos arquivos de configuração (lidos pelo `plan` e refletidos nas considerações técnicas)
- A IA tem liberdade para escolher a abordagem que achar melhor dentro das convenções, sem precisar replicar estilo dev-por-dev
- Validar cadeia completa (front → API → back → banco) onde aplicável

### 5.1. Registrar progresso no `changelog.md`

A cada **sub-task concluída** ou **passo significativo do plano** concluído, anexar ao final de `GOD/tasks/{cod-da-task}/changelog.md`:

```markdown

## {timestamp-iso-8601-utc} — {resumo curto do que foi feito}
- **Arquivos:** {lista de arquivos criados ou modificados}
- **Notas:** {decisões tomadas, padrões seguidos, pontos de atenção — opcional}
```

Diretrizes:
- **Granularidade:** uma entrada por sub-task quando houver divisão no plano; caso contrário, uma entrada por passo significativo (ex: "endpoint criado", "componente integrado", "migration aplicada"). Não criar entrada a cada edição micro.
- **Timestamp:** ISO 8601 em UTC (ex: `2026-04-22T15:10:00Z`).
- **Arquivos:** listar apenas os relevantes pra orientar retomada (não precisa incluir arquivo de lock, auto-gerados, etc.).
- **Notas:** preencher só quando houver uma decisão não óbvia pelo plano (ex: "usei o padrão de paginação do endpoint /orders como base"). Se o passo foi execução direta do plano sem desvios, pode omitir.

Este registro incremental é o que permite retomada futura: se a task for interrompida (por pausa explícita ou simples abandono da conversa), o changelog preserva o estado da implementação para que uma próxima sessão possa continuar sem perder contexto.

### 5.2. Detecção de barreira

Se durante a execução você identificar:

- **Código/endpoint/módulo ausente** — algo que o plano assume existir mas não existe no projeto e criar está fora do escopo
- **Dependência externa indisponível** — serviço fora do ar, credencial faltando, MCP necessário não autenticado, biblioteca não instalada e sem autonomia pra instalar
- **Decisão do usuário pendente** — ambiguidade no plano ou escopo que exige resposta do usuário antes de prosseguir, e o usuário não está disponível no momento
- **Conflito inesperado com o repositório** — arquivos modificados por terceiros, merge conflict, estado de git inesperado que não pode ser resolvido com autonomia

**Não tente contornar.** Não invente stubs, não assume valores, não deixa TODO espalhado pelo código.

1. Confirmar rapidamente com o usuário: "Detectei `{barreira específica}`. Vou pausar a task e registrar o blocker pra retomarmos depois — ok?"
2. Se o usuário confirmar ou estiver ausente, delegar à skill `pause` passando o motivo da barreira como observação.
3. A skill `pause` escreve o bloco `⏸ PAUSE` no changelog e marca `paused: true`. A implementação pára aqui.

### 5.5. Anotação AC↔teste (v8)

Após escrever testes, anotar ACs cobertos via comentário leve. Alimenta a skill `coverage`.

**Sintaxe:** comentário `// covers: AC-X[, AC-Y]` (ou `# covers:` em Ruby/Python) acima do bloco de teste. Múltiplos ACs separados por vírgula.

**Regras:**
- Cruzar testes da task com ACs lidos no passo 2.
- Teste sem AC correspondente: não anotar (ausência = "não rastreado pra spec"). Não inventar ACs.
- Se sente que falta AC, sinal de spec incompleta → anotar em changelog e sugerir `update-spec`.

**ACs sem teste automatizado** (FE sem E2E, validações visuais, auditoria pós-deploy): editar `GOD/tasks/{cod}/coverage.md`, seção `## Validações manuais`:

```markdown
- AC-002.1: validação manual em staging por PM
- AC-002.2: visual em staging por UX
```

Honestidade — registrar explícito se é manual; não fingir teste.

### 5.6. Anotação BR↔código (v10, se `applicable_rules` populado)

Se a spec tem `applicable_rules` no frontmatter (v10) **e** `domains_path` está configurado em `GOD/config.md`:

1. Carregar BRs aplicáveis do frontmatter da spec; ler cada uma em `<domains_path>/<dominio>.md`.
2. Identificar **onde a invariante é mantida (enforced)** — não onde o conceito só trafega:
   - ❌ leitura simples: `const owner = vakinha.owner_id;`
   - ✅ enforcement: `if (vakinha.owners.length > 1) throw new Error(...)`
3. Anotar comentário **acima da linha de enforcement**: `// rule: BR-<DOMINIO>-<N> — <descrição curta>`. Sintaxe: `// rule:` em TS/JS/Go/Java/C#; `# rule:` em Ruby/Python.
4. **Heurística "enforced":** `if ... throw`, filter/where aplicando regra, validação explícita, transação/lock que mantém invariante.
5. **Anti-poluição:** ~1 anotação por arquivo de domínio. Zero em controllers/views/mappers. >5 anotações = sugerir centralização.
6. **BR sem ponto de enforcement nesta task** (ex: task só lê meta mas BR-007 trata de update): anotar em `coverage.md` na seção `## BRs aplicáveis sem anotação`. Não anotar no código.
7. **Não inventar BR** — se sente que falta uma, anotar "BR candidata: <desc>" no changelog. Criação de BR é manual em `<domains_path>/<dominio>.md` (skill `rules` virá na v10.5).

`pack-up` parseia `// rule:` e gera tabela "BRs aplicáveis × anotadas" no PR.

### 6. Verificação pós-implementação

Após implementar:
- Ler os arquivos alterados para verificar consistência e coerência
- Verificar se todos os passos do plano foram executados

> ℹ️ Esta skill **não roda** type-check, linter, testes ou qualquer outro processo de validação automatizada. Esses processos são configurados pelo usuário nos hooks (`after implement` ou `before pack-up`, conforme preferência) e executados por aqueles hooks.

### 6.5. Verificação contra `learned-patterns.md`

Esta etapa **roda por padrão** e captura pequenos desvios de regras registradas pelo `learn` em tasks anteriores (ex: "handlers internos usam prefixo `on*`", "linha em branco entre setup imperativo e `try`"). Se a flag `--skip-patterns-check` foi passada, **pular este passo inteiro** e seguir para o 7.

1. **Localizar o arquivo.**
   - Ler `GOD/learned-patterns.md`.
   - Se o arquivo **não existe**: criar com o template canônico (mesmo template do `install` passo 4.5) e pular — não há regras a aplicar ainda.
   - Se existe mas **não tem regras** (apenas header + `---`): pular — não há regras a aplicar.

2. **Filtrar regras aplicáveis ao que foi implementado.**
   - Identificar linguagens dos arquivos alterados (extensões: `.rb` → `ruby`; `.ts`/`.tsx`/`.js`/`.jsx` → `js-ts`; `.py` → `python`; etc.).
   - Identificar projeto(s) tocado(s) (em single-project, o próprio; em multi-project, cada subprojeto afetado).
   - Carregar apenas as regras cujo escopo seja `geral`, `linguagem: <uma das linguagens>`, ou `projeto: <um dos projetos>`.
   - **Ignorar** regras marcadas com `~~riscado~~`.

3. **Checar os arquivos modificados contra cada regra aplicável.**
   - Reler os arquivos modificados (não o repo inteiro).
   - Para cada regra, verificar se há violações no que foi alterado.
   - **Ignorar código legado não tocado nesta task** — só o diff importa. (Ex: uma regra tipo "prefixo `on*`" aplica-se a handlers novos/modificados, não a handlers antigos intactos.)

4. **Ajustar automaticamente quando a correção é mecânica.**
   - Regras de formatação (linhas em branco, ordem de blocos, indentação) → corrigir direto.
   - Regras de nomenclatura simples (ex: `handle*` → `on*` em handlers novos) → corrigir direto.
   - **Se a correção exige escolha semântica** (ex: escolher `logable` correto ao gravar no modelo `Log`), **perguntar ao usuário** antes de ajustar.

5. **Registrar no `changelog.md`** (uma entrada só, mesmo que várias regras sejam checadas):

   ```markdown

   ## {timestamp-iso-8601-utc} — patterns-check
   - **Regras aplicadas:** {contagem} regras (escopos: {lista dos escopos usados})
   - **Ajustes automáticos:** {lista de arquivos ajustados e qual regra motivou} — ou "nenhum ajuste necessário"
   - **Pendências:** {regras que precisam de decisão do usuário, se houver} — ou omitir se não houver
   ```

6. **Se houver pendências não resolvíveis automaticamente**, apresentar ao usuário antes de seguir pro passo 7 e aguardar decisão.

### 7. Atualizar status para `implemented`

Após concluir a verificação pós-implementação, atualizar `GOD/tasks/{cod-da-task}/status.md`:

- `phase`: `implemented`
- `updated_at`: timestamp ISO 8601 em UTC
- `updated_by`: `implement`
- `spec_version_consumed`: **`spec_version` da spec lida no passo 2** (int) — atualiza pra refletir o que foi efetivamente implementado contra
- `branch`, `branch_base`, `learned`, `prs`: preservar valores atuais

### 8. Executar hook `after implement`

Ler `GOD/hooks.md` e localizar a seção `# after implement`.

- Se o conteúdo for `skip-hook`: pular e seguir para o passo 9.
- Se houver instruções em linguagem natural: executá-las integralmente antes do relatório final.

### 9. Reportar resultado

Apresentar ao usuário:
- Resumo do que foi implementado
- Arquivos criados ou modificados
- Se usou subagents, listar o que cada um fez
- Pendências ou pontos de atenção (se houver)
- Se hooks before/after foram executados, listar resumidamente o que rodou
- Ponteiro para `GOD/tasks/{cod-da-task}/changelog.md` como histórico incremental da implementação

---

## Guard-rails

- Dona da criação da branch no git (init não toca, plan só resolve nome+base).
- Lê `learned-patterns.md` (passo 6.5); pode criar arquivo vazio com template se ausente. Não escreve conteúdo (só `learn` faz).

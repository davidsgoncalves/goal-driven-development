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

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos **na ordem**:

### 0. Executar hook `before implement`

Ler `GOD/hooks.md` e localizar a seção `# before implement`.

- Se o conteúdo for `skip-hook`: pular e seguir para o passo 1.
- Se houver instruções em linguagem natural: executá-las integralmente antes de prosseguir.

### 1. Identificar a task

- Se o contexto da conversa já contém o código da task, usar esse código
- Caso contrário, perguntar ao usuário o código da task (ex: `PROJ-123`)

### 2. Ler o plano

Ler o arquivo `GOD/tasks/{cod-da-task}/plan.md` para obter o plano de implementação.

- Se o plano estiver vazio, informar o usuário que precisa rodar a skill `plan` antes
- Se o plano existir, analisar sua estrutura e complexidade

### 2.05. Preparar git (validar estado + criar/ativar branch(es) da task)

Esta skill é responsável pela criação física da(s) branch(es) no git. O `plan` já resolveu nomes e bases — aqui apenas executamos.

1. **Ler `GOD/tasks/{cod-da-task}/status.md`** e identificar o formato do campo `branch`:
   - **String** (ex: `branch: task/PROJ-123/xxx` + `branch_base: main`) → **modo single-project**. Uma branch a criar.
   - **Lista de objetos** (ex: `branch: [{project, name, base}, ...]`) → **modo multi-project workspace**. Uma branch por projeto afetado.
   - **`null` em qualquer lado:** a task não foi planejada corretamente — orientar o usuário a rodar `plan` primeiro e encerrar.

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

### 6. Verificação pós-implementação

Após implementar:
- Ler os arquivos alterados para verificar consistência e coerência
- Verificar se todos os passos do plano foram executados

> ℹ️ Esta skill **não roda** type-check, linter, testes ou qualquer outro processo de validação automatizada. Esses processos são configurados pelo usuário nos hooks (`after implement` ou `before pack-up`, conforme preferência) e executados por aqueles hooks.

### 7. Atualizar status para `implemented`

Após concluir a verificação pós-implementação, atualizar `GOD/tasks/{cod-da-task}/status.md`:

- `phase`: `implemented`
- `updated_at`: timestamp ISO 8601 em UTC
- `updated_by`: `implement`
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

- **Esta skill é a dona da criação da branch no git.** O `init` não toca em git; o `plan` apenas resolve nome + base; o `implement` cria/ativa fisicamente.
- **Esta skill não escreve em `GOD/knowledge.md`.** Apenas a skill `learn` pode fazê-lo.

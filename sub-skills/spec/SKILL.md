---
name: spec
description: |
  Produz a spec da task como artefato canônico, **antes** do init. Aceita input bruto direto (link Jira / código / texto livre), busca dados externos (Jira/Figma), faz Q&A focada em escopo (proibido falar de implementação), detecta o perfil da task (trivial/normal/critical) e escreve `spec.md` no `specs_path` configurado. É a primeira skill do fluxo na v9. Use quando o usuário mencionar: "criar spec", "spec da task", "escrever spec", ou quando começar uma task nova com perfil normal/critical.
tools: Read, Glob, Grep, Bash, Edit, Write, Agent
---

# Spec — Entry point do fluxo

> Produz a spec da task (WHAT e por quê, separado do HOW). Entry point do fluxo v9: aceita input bruto direto, busca dados em Jira/Figma, escreve em `<specs_path>/tasks/{cod}.md` antes que qualquer estrutura de execução exista.
>
> Tasks legacy v8 com `GOD/tasks/{cod}/description.md` são lidas pra retrocompat — descrição é importada como seção `## Input bruto` da spec nova.

## Flags

- `--review-feedback` — modo de loop de validação. Re-executa a spec incorporando feedback externo (comentário do PM/UX no Jira/Slack). Incrementa `spec_version` no frontmatter. Limite de 2 ciclos automáticos consecutivos antes de exigir conversa síncrona com o stakeholder. Ver seção dedicada abaixo.
- `--quick` — pula verificações semânticas profundas do `review --spec` (mantém só lint estrutural). Útil pra iteração rápida em tasks normais. **Em modo `--quick`, hook `after spec` é executado mas a sugestão de `publish-spec` ao final é silenciada.**
- `--type=normal|critical` — força o perfil da task, dispensando heurística + confirmação. **Não há `--type=trivial` aqui** — task trivial não precisa de spec; o usuário deve rodar `init --type=trivial` diretamente.
- `--target <destino>` *(v10.1)* — após escrever spec canônica em `<specs_path>/tasks/{cod}.md`, publicar **adicionalmente** no destino. Valores: `jira`, `slack`, `stdout`, `clipboard`, `file:<path>`, `notion`, ou custom definido em `hooks.md`. Reusa internamente a sub-skill `publish-spec` — não duplica lógica. Sem `--target`, comportamento atual (não publica automaticamente; `publish-spec` continua sendo skill separada pra invocação manual).
- `--debug` *(v10.6)* — registra ações em `GOD/tasks/{cod}/debug.log` via `_lib/debug_log.py`. Opt-in por invocação. Pontos críticos a logar: detecção de perfil (1.5), análise heurística (5.5), Q&A (6), self-validação (8.5), review (9), publicação (10.5). Ver "Debug log opt-in" no SKILL.md raiz.

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos **na ordem**:

### 0. Executar hook `before spec`

Ler `GOD/hooks.md` e localizar a seção `# before spec`.

- Se o conteúdo for `skip-hook`: pular e seguir para o passo 0.5.
- Se houver instruções em linguagem natural: executá-las integralmente antes de prosseguir.

### 0.4. Sincronizar repo de specs (sync check)

Antes de checar se a spec existe localmente, garantir que o filesystem reflete o estado remoto. Sem isso, dois devs trabalhando na mesma task podem criar specs divergentes silenciosamente.

1. **Resolver `specs_path`** (apenas pra esta verificação — a resolução completa é no passo 1). Ler `GOD/config.md` ou usar default `docs/specs/`.

2. **Detectar se `<specs_path>` é git:**
   - Rodar `git -C <specs_path> rev-parse --git-dir` (silenciar erro).
   - Se sucede → repo git. Prosseguir com fetch.
   - Se falha → pasta sem git (raro). Pular este passo.

3. **Fetch silencioso:**
   - `git -C <specs_path> fetch --quiet` (~1s típico).
   - Se falhar (sem rede, repo inválido, credenciais): avisar uma vez, perguntar se quer prosseguir mesmo assim. Não abortar automaticamente — dev offline ainda precisa rodar a skill.

4. **Comparar HEAD local vs remoto:**
   - Identificar branch atual: `git -C <specs_path> rev-parse --abbrev-ref HEAD`.
   - Identificar tracking remoto: `git -C <specs_path> rev-parse --abbrev-ref --symbolic-full-name @{u}` (silenciar erro — branch pode não ter upstream).
   - Se sem upstream: pular comparação (não dá pra saber se está atualizado), prosseguir.
   - Comparar: `git -C <specs_path> rev-list --left-right --count HEAD...@{u}` retorna `A B` onde A = commits locais à frente, B = commits remotos à frente.

5. **Reagir conforme estado:**
   - **`B == 0`** (local em paridade ou à frente): tudo OK, prosseguir silenciosamente.
   - **`B > 0`** (remoto tem commits novos não puxados): **alertar duro**:

     > ⚠️ Repo de specs (`<specs_path>`) tem **{B} commits remotos não puxados**.
     >
     > Outro dev pode ter trabalhado em specs nesta janela — incluindo, possivelmente, a spec da task que você quer agora.
     >
     > Como prosseguir?
     > - (a) **Puxar agora** (`git pull --ff-only` no repo de specs) e seguir — recomendado.
     > - (b) **Prosseguir mesmo assim** (risco real de conflito de merge no push depois).
     > - (c) **Abortar** e fazer pull manual primeiro.

   - Se (a) → executar `git -C <specs_path> pull --ff-only`. Se fast-forward falhar (merge não-trivial necessário), abortar com orientação ("seu repo de specs tem divergências locais e remotas. Resolva manual antes de rodar `spec`").
   - Se (b) → prosseguir, mas registrar em memória que houve aviso (não persiste — só pra log do passo final).
   - Se (c) → encerrar silenciosamente.

### 0.5. Identificar a task e capturar input bruto

A spec na v9 **não exige `description.md` prévio**. Aceita input direto. Estados possíveis:

**Caso A — Task nova (fluxo v9 normal):**
- O usuário passa link/código do Jira ou texto livre direto na invocação.
- Se nada foi passado, perguntar: "Link do Jira, código da task ou descrição livre?"
- Extrair o código da task:
  - Link Jira → extrair (ex: `PROJ-123`)
  - Código puro → usar direto
  - Texto livre → pedir um identificador curto (ex: `meu-feature`)
- Guardar o input bruto em memória (vai pra seção `## Input bruto` da spec no passo 8).

**Caso B — Spec já existe em `<specs_path>/tasks/{cod}.md`:**
- Detectar lendo o frontmatter. Se sim, pular pra passo 8 e perguntar ao usuário se quer:
  - (a) re-rodar Q&A e regenerar spec do zero (cuidado: descarta histórico)
  - (b) atualizar a spec sem repetir Q&A (modo `--review-feedback` é mais apropriado pra incorporar feedback)
  - (c) abortar

**Caso C — Task legacy v8 (`GOD/tasks/{cod}/description.md` existe):**
- Detectar e ler o input bruto de lá. Avisar o usuário:

  > 📦 Detectada task legacy (v8): `GOD/tasks/{cod}/description.md` existe. Lendo o input de lá pra retrocompat. A spec gerada vai pra `<specs_path>/tasks/{cod}.md` (estrutura v9 do specs_path).

- Não criar nova seção de input — o `description.md` legacy permanece como referência.

### 1. Resolver o `specs_path` e garantir estrutura mínima

Ler `GOD/config.md` e extrair o valor de `specs_path` (root do repo de specs).

1. **Se `config.md` não existe ou não tem a seção `## specs_path`**: assumir default `docs/specs/` (relativo ao diretório onde o GOD está instalado) e informar o usuário ("usei o default `docs/specs/` — você pode editar `GOD/config.md` pra alterar").
2. **Resolver path:**
   - Se relativo, resolver a partir do diretório onde `GOD/` está instalado.
   - Se absoluto, usar como está.
3. **Garantir estrutura mínima:**
   - Se `<specs_root>/` não existe: criar com `mkdir -p`.
   - Se `<specs_root>/tasks/` não existe: criar com `mkdir -p`.
   - Se `<specs_root>/README.md` não existe: criar com o template canônico abaixo.

Template do `<specs_root>/README.md` (criar apenas se não existir):

```markdown
# Specs

Repositório canônico de specs do produto. Cada spec é o **contrato de escopo** de uma feature/task — REQs em formato EARS, ACs com IDs estáveis, cenários e NFRs explícitos.

## Estrutura

```
specs/
├── tasks/                      # Spec autocontida por task (uma por entrega)
│   ├── <cod>.md                # ex: PROJ-123.md
│   └── <cod>-changelog.md      # (v9, sob demanda) histórico de mudanças via update-spec
├── domains/                    # (reservado) Feature specs eternas por domínio do produto
└── flows/                      # (reservado) Índices que amarram múltiplas features (jornadas e2e)
```

`tasks/` é populado pelo framework GOD (skill `spec`) na fase de SDD por task.
`domains/` e `flows/` serão populados por skills futuras quando feature specs eternas e fluxos cross-feature forem suportados.

## Convenções

- Toda spec começa com frontmatter: `spec_version`, `task`, `created_at`, `updated_at`.
- ACs têm IDs estáveis: `AC-NNN.N` (ex: `AC-001.2`). Não renomear depois de citar em código/teste.
- Specs não falam de implementação — proibido mencionar framework, biblioteca, banco. Isso é HOW, vai pro plan da task.
- Specs são commitadas como artefato de produto. Histórico via `git log` e via `<cod>-changelog.md` (quando `update-spec` foi usado).
```

Guardar em memória: `<specs_root>` (root) e `<tasks_dir>` = `<specs_root>/tasks/`. A spec final será escrita em `<tasks_dir>/{cod-da-task}.md`.

### 1.5. Detectar perfil da task

Determinar o perfil que afeta cerimônia ao final do fluxo. Três perfis:

| Perfil | Quando se aplica | Comportamento ao final |
|--------|------------------|-------------------------|
| `trivial` | Mudança cosmética (copy, typo, dep upgrade) | **Não cabe nesta skill.** Spec aborta com sugestão de rodar `init --type=trivial` direto |
| `normal` | Feature curta, bug com escopo claro, sem stakeholder externo ativo | Spec gerada, `publish-spec` **não sugerido** ao final |
| `critical` | Feature grande, múltiplos stakeholders, exige aprovação externa | Spec gerada, `publish-spec` **sugerido** ao final pra travar antes do `init` |

**Resolução de perfil:**

1. Se `--type=normal` ou `--type=critical` foi passado → usar direto, pular heurística.
2. Caso contrário, aplicar **heurística**:
   - **Sinais de `trivial`** (qualquer um basta): input ≤ 80 caracteres + sem código Jira; texto contém termos como "typo", "trocar copy", "renomear botão", "atualizar dep", "mudar texto" sem detalhes; nenhum AC explícito mencionado.
   - **Sinais de `critical`** (qualquer um basta): input vem de Jira com >3 comentários; descrição menciona stakeholder externo (PM, UX, legal, compliance); descrição menciona impacto em múltiplos sistemas/projetos; ACs já mencionam métricas de SLA, LGPD, compliance, ou auditoria.
   - **Default**: `normal`.
3. **Confirmação rápida com o usuário** (sempre, mesmo sem ambiguidade — custa pouco e evita pular publish-spec por engano):

   > 🎯 Detectei o perfil desta task como **`{perfil}`**.
   >
   > - `trivial` → pula spec, vai direto pro `init --type=trivial`.
   > - `normal` → spec sem publicação automática, segue pro `init`.
   > - `critical` → spec + sugestão de `publish-spec` pra validar com stakeholder antes do `init`.
   >
   > Confirma o perfil **`{perfil}`**? ([s] confirma / [t] trivial / [n] normal / [c] critical)

4. Se o usuário escolheu `trivial`, **abortar imediatamente** com:

   > ⏭️ Task `{cod}` é trivial. Spec dispensada.
   >
   > 💡 Próximo passo: `init {cod} --type=trivial` (cria branch sem passar por spec/plan).

5. Guardar perfil escolhido em memória (vai pro frontmatter da spec).

### 2. Buscar dados no Jira (se aplicável)

Se o input bruto contém um link ou código do Jira:

- Acessar o Jira via MCP Atlassian (ex: `getJiraIssue`) e obter:
  - Título da task
  - Descrição completa
  - Links do Figma (nos campos ou na descrição)
  - Critérios de aceitação que o ticket já trouxer
  - Parent task e subtasks (contexto mais amplo)
  - Comentários relevantes (entram como insumo da Q&A)

Se o input bruto é apenas texto manual (sem código Jira), pular este passo.

### 3. Consultar knowledge por tasks semelhantes

Ler `GOD/knowledge.md`. Verificar se há tasks anteriores com contexto semelhante.

Se encontrar, registrar:
- Códigos de commits relacionados (pra incluir como referência na spec, opcional)
- Aprendizados relevantes que podem afetar **escopo** (não implementação)

### 4. Analisar design do Figma (se aplicável)

Se o Jira trouxe links do Figma, ou se o input bruto já continha links:

- Acessar o Figma via MCP Figma (`get_design_context`)
- Identificar **estados, fluxos, edge cases visuais** — isso vira input pra Q&A e pra cenários da spec
- **Não detalhar implementação visual aqui** (cores, componentes específicos) — isso é HOW, vai pro plan

Se não houver links do Figma, pular.

### 4.5. Sugerir BRs aplicáveis (v10, se `domains_path` configurado)

Se `GOD/config.md` tem `domains_path` populado e a pasta existe:

1. **Listar arquivos `<dominio>.md`** no `domains_path`. Pra cada arquivo, ler frontmatter (`domain:`) e BRs declaradas (cabeçalhos `## BR-<DOMINIO_UPPER>-NNN`).
2. **Heurística de relevância:** comparar input bruto + dados Jira + Figma com:
   - Texto do título da BR (`## BR-X-001: Dono único`)
   - Texto do `**Why:**` (motivo)
   - Substantivos do domínio (ex: domain `payments` → palavras como "payment", "doação", "valor", "saque")
3. **Listar BRs candidatas** ordenadas por relevância heurística. Sempre mostrar com confirmação:

   > 📜 BRs potencialmente aplicáveis a esta task:
   > - `BR-PAYMENTS-001` (Dono único) — alta relevância (task menciona "dono")
   > - `BR-PAYMENTS-007` (Meta monotônica) — média relevância (task afeta valor)
   > - `BR-AUTH-003` (Sessão expira em 24h) — baixa relevância (task toca user_id)
   >
   > Confirme quais aplicar (separado por vírgula, ou Enter pra aceitar as de alta relevância apenas):

4. **Guardar** lista de BR-IDs confirmadas em memória pra ir pro frontmatter da spec (passo 8).

Se `domains_path` não está configurado ou pasta vazia, **pular este passo silenciosamente** (sem mensagem de erro).

> Heurística é deliberadamente conservadora — falso positivo treina dev a ignorar a sugestão. Quando em dúvida, **não sugerir**. A skill `audit-rules` (v10.5) vai cobrir BRs perdidas.

### 5. Coletar contexto do produto

Ler arquivos canônicos do projeto que descrevem **produto**, não código:
- `README.md` (descrição do produto)
- `CLAUDE.md` (instruções do projeto)
- Specs já existentes em `<specs_root>/tasks/` que possam ter relação

A busca é case-insensitive. Não ler ARCHITECTURE.md aqui — isso é HOW, fica pro plan.

### 5.5. Análise heurística pré-Q&A (v10.1)

Antes de perguntar qualquer coisa, varrer input bruto + dados Jira/Figma coletados procurando excessos (HOW dentro de WHAT) e gaps (WHAT que falta).

1. **Carregar `sub-skills/spec/heuristics.md`** (arquivo separado com tabelas de detectores).
2. **Aplicar detectores na ordem:**
   - **Excessos** (seção 1 do heuristics.md): bloco de código, schema técnico detalhado, framework leak (lista de palavras-flag na seção 4), pseudo-código, decisão de banco/storage. Pra cada match, registrar `{tipo, trecho, ação sugerida}`.
   - **Gaps** (seção 2): objetivo vago, ator não nomeado, não-objetivos ausentes, NFRs ausentes (perf/LGPD/observabilidade/auditoria), cenários de erro ausentes, comportamento não-testável. Pra cada gap, registrar `{tipo, motivo, pergunta sugerida}`.
   - **Tamanho** (seção 3): contar sinais de feature. Threshold: 2+ sinais "forte" OU 3+ sinais "médio" → `tamanho: feature`. Senão, `tamanho: simples`.
3. **Apresentar resumo da análise** (não interativo — só pra contexto da Q&A):

   ```
   🔍 Análise heurística:
     • Excessos detectados: {N} ({tipos})
     • Gaps detectados: {N} ({tipos})
     • Tamanho: {simples|feature}
   ```

4. **Guardar lista estruturada** em memória — alimenta:
   - Passo 6 (Q&A): pergunta apenas sobre gaps detectados.
   - Passo 6.5 (feature split): se `tamanho: feature`, oferece quebrar em subtasks.
   - Passo 8 (template): se há excessos pra preservar, popula `## Notas técnicas (input pro plan)`.
   - Passo 8.5 (self-validação): valida correção dos excessos antes do review.

Se nenhum excesso/gap detectado e tamanho=simples, anunciar:

> ✅ Input bem estruturado. Q&A leve apenas pra confirmar entendimento.

E seguir pro passo 6 com Q&A mínima (apenas confirmação).

### 6. Sessão de Q&A com o usuário — focada em gaps detectados

Fazer perguntas agrupadas focadas em **escopo** e **comportamento esperado**. **Proibido perguntar sobre implementação** (linguagem, framework, padrão arquitetural, biblioteca). Se dúvida técnica aparecer naturalmente, anotar pra repassar ao `plan`.

**Princípio v10.1:** perguntar APENAS sobre os gaps detectados no passo 5.5. Se um bloco já está coberto pelo input, pular o bloco inteiro com mensagem explícita ("Objetivo claro do input — sem dúvidas").

**Blocos possíveis** (cada um incluído na Q&A apenas se algum gap do tipo foi detectado):

**Bloco "objetivo + ator + não-objetivos"** — incluir se há gap nesses:
- Qual o problema único que esta task resolve? (apenas se objetivo vago)
- Quem efetivamente faz/consome o resultado? Time específico? SLA implícito? (apenas se ator não nomeado)
- Há algo no escopo aparente que você quer deixar claro que NÃO entra? (apenas se não-objetivos ausentes)

**Bloco "comportamento e cenários"** — incluir se há gap:
- (Listar dependências externas detectadas) — comportamento esperado se cada uma falhar?
- Edge cases que ainda não estão claros?
- O que reverte e o que persiste em caso de falha parcial?

**Bloco "NFRs"** — incluir apenas as dimensões com gap:
- Performance: limite explícito? (apenas se ausente e relevante)
- LGPD/PII: dado pessoal envolvido? como tratar retenção? (apenas se PII detectada e sem menção)
- Observabilidade: algo precisa ser logado/alertado? (apenas se ausente)
- Acessibilidade: UI envolvida? requisitos a11y? (apenas se UI no escopo sem menção)
- Auditabilidade: quem fez o quê precisa ficar registrado? (apenas se operação financeira/admin sem menção)

**Bloco "decisões técnicas no input"** — incluir se há excessos detectados:

> O input tem decisões técnicas embutidas: {lista de excessos}. Em SDD bem feito, isso vai pro `plan`, não pra spec. Quer:
> - (a) Manter como está (fica prescritivo, mas time sênior decide)
> - (b) Mover pra `## Notas técnicas (input pro plan)` na spec — preserva mas separa do escopo
> - (c) Remover — `plan` resolve do zero

Default sugerido: **(b)**. Preserva trabalho mas separa.

Diretrizes:
- **Aceite "não sei" ou "depois"** — gera placeholder explícito (`(a confirmar com infra)`) em vez de inventar.
- **Agrupe perguntas** — todos os blocos do mesmo turno vão juntos, não 1 por turno.
- Se nenhum gap detectado, anuncie "sem dúvidas" e siga.

**Registrar todo o Q&A** — vai pra seção "Discovery" da spec.

### 6.5. Feature split inline (v10.1, opcional)

Se a heurística do passo 5.5 marcou `tamanho: feature` E `applicable_rules` não está em modo trivial, oferecer ao usuário:

> 🧩 Heurística detectou que esta task tem características de feature ({sinais}). Sugiro quebrar:
>
> - (a) Gerar **spec pai** (escopo geral) + **N specs de subtasks** (escopo independente cada). Cada subtask vira arquivo próprio em `<specs_path>/tasks/{cod}-{N}.md` ou seguindo padrão de subtask do Jira.
> - (b) Continuar como spec única — você sabe o que está fazendo.
> - (c) Abortar e usar `init-tree` se a árvore Jira já existe (`init-tree {epic}` puxa do Jira em batch).

Se (a):
1. Inferir candidatos a subtasks pela análise de REQs detectados no input + dependências externas.
2. Apresentar lista numerada e ordem (reflete dependência — primeira aterrissa antes das outras).
3. Pedir confirmação/ajuste do usuário.
4. Gerar spec pai + N specs de subtasks no passo 8 (template). Pai recebe REQs gerais que orquestram a feature; cada subtask recebe REQs específicos do que ela entrega.

Se (b) ou (c): seguir fluxo normal (spec única).

Se `tamanho: simples`: pular este passo silenciosamente.

### 7. Resolver título e composição final

Antes de escrever:
- **Título** da spec: vem do Jira (se disponível) ou perguntar ao usuário.
- **Timestamp**: ISO 8601 em UTC para `created_at` e `updated_at`.
- **Frontmatter `profile`**: o perfil resolvido no passo 1.5 (`normal` ou `critical`).

### 8. Escrever `spec.md`

Escrever o arquivo em `<tasks_dir>/{cod-da-task}.md` (= `<specs_root>/tasks/{cod-da-task}.md`). Se já existir, pedir confirmação antes de sobrescrever.

Template canônico (v9):

```markdown
---
spec_version: 1
task: {cod-da-task}
profile: {normal|critical}
applicable_rules: [{lista de BR-IDs confirmados no passo 4.5, ou [] se nenhum aplicável / domains_path desativado}]
created_at: {timestamp-iso-8601-utc}
updated_at: {timestamp-iso-8601-utc}
---

# SPEC-{cod-da-task} — {título da task}

## Input bruto

{input cru fornecido pelo usuário ou trazido do Jira — ipsis litteris, sem enriquecer.
Caso a task seja legacy v8 e a leitura tenha vindo de `GOD/tasks/{cod}/description.md`,
copiar o input dali. Esta seção substitui o `description.md` separado em tasks v9.}

## Objetivo

{Uma frase clara do problema sendo resolvido. Sem solução técnica.}

## Não-objetivos

{O que está explicitamente fora de escopo. Se nada relevante: "Nenhum não-objetivo declarado.".}

## Discovery

{Q&A do passo 6 em formato pergunta/resposta. Se não houve Q&A: "Escopo claro a partir do input — sem dúvidas levantadas.".}

## Requisitos

### REQ-001: {nome curto}
**WHEN** {contexto disparador} **THEN** o sistema **SHALL** {comportamento esperado}.

#### Critérios de aceitação
- AC-001.1: {critério testável e específico}
- AC-001.2: ...

### REQ-002: ...
...

## Cenários

### Happy path
{Descrição do fluxo esperado em condições normais.}

### Edge cases
- {edge case 1}: {comportamento esperado}
- {edge case 2}: ...

### Erros
- {erro possível}: {comportamento esperado}

## NFRs

- **Performance:** {limite explícito ou "não aplicável"}
- **Segurança / LGPD:** {requisitos ou "sem dado pessoal envolvido"}
- **Acessibilidade:** {requisitos ou "não aplicável"}
- **Observabilidade:** {eventos a logar ou "não aplicável"}

## Referências

- Jira: {url ou "—"}
- Figma: {url ou "—"}
- Tasks semelhantes (knowledge): {códigos ou "nenhuma"}

## Notas técnicas (input pro plan)

{Apenas se o passo 5.5 detectou excessos que o usuário escolheu preservar (opção (b) do passo 6 — mover pra cá em vez de remover).
Esta seção contém pseudo-código, schemas, decisões arquiteturais embutidas no input que ficam preservadas mas SEPARADAS do escopo. O `plan` consome como sugestão técnica, não como prescrição. Se vazia, omitir a seção inteira (template skipa quando passo 5.5 não detectou excessos a preservar).}
```

**Regras de qualidade:**
- ACs são **testáveis e específicos** — "deve ser rápido" é vago; "responde em <200ms" é testável.
- Critérios usam IDs estáveis (`AC-001.1`) — vão ser referenciados depois.
- Não vazar implementação — se a spec menciona React, banco, framework, é violação.
- EARS (`WHEN ... THEN ... SHALL ...`) é o formato preferido pros REQs. Se um REQ não cabe em EARS, prosa imperativa é aceitável.
- A seção `## Input bruto` preserva o material original sem edição — não tente "limpar".

### 8.5. Self-validação inline (v10.1 — otimizado v10.2)

**Caminho preferido (v10.2):** delegar lint estrutural pra `sub-skills/_lib/validate_spec.py --task {cod}`. Recebe JSON com `blocking` e `warnings`. Aplicar correções dos `warnings` corrigíveis inline; pra `blocking`, pedir confirmação ao usuário antes de prosseguir.

**Fallback (LLM)** ou complemento do script: rodar checklist mínimo da seção 5 de `heuristics.md` na spec recém-escrita. Corrige o trivial inline; sinaliza ao usuário o que não dá pra corrigir.

Checks (ordem de execução):

1. **Cada REQ tem ao menos 1 AC** — `bloqueia`. Se algum REQ está sem AC, perguntar ao usuário e adicionar (loop até cobrir).
2. **ACs têm ID estável (`AC-NNN.N`)** — `corrige inline`. Numerar automaticamente os que estão sem ID.
3. **Sem palavras-tabu sem métrica nos ACs** ("rápido", "fácil", "intuitivo", "escalável", "seguro" sem qualificação) — `bloqueia`. Reescrever ou perguntar métrica ao usuário.
4. **Sem framework leak em REQs/ACs/Objetivo** — `corrige inline ou pergunta`. Aplicar lista de palavras-flag (seção 4 de heuristics.md). Se detectado, oferecer mover pra `## Notas técnicas (input pro plan)` ou reescrever.
5. **Cada AC tem cenário associado** (happy/edge/erro) — `sugere`. Não bloqueia.
6. **Seção NFRs presente** (mesmo com "não aplicável") — `corrige inline`. Adicionar com placeholders.
7. **Não-objetivos declarados** — `sugere`. Se a seção está vazia, sugerir; não bloqueia.
8. **Ator humano nomeado** — `sugere`. Se ausente, sugerir; não bloqueia.
9. **`## Input bruto` preservado sem edição** — `bloqueia`. Restaurar do estado original se foi alterado.
10. **Para feature** (passo 6.5 escolheu (a)): subtasks têm escopo independente — `sugere`.
11. **Para feature**: ordem reflete dependência real — `sugere`. Pedir ao usuário pra confirmar.

**Regra de ouro:** self-validação corrige trivial; `review --spec` (passo 9) faz peer-review semântica profunda em subagent isolado. As duas se complementam, não substituem.

Reportar ao usuário só o que **bloqueou** ou foi **corrigido**:

```
🔧 Self-validação:
  ✓ ACs IDs auto-numerados (3 corrigidos)
  ✓ NFRs adicionados com placeholders (4 dimensões)
  ⚠ AC-002.1 tem palavra-tabu "rápido" sem métrica — corrigir antes do review
```

Se algum check `bloqueia` falhou, **pausar pra correção** antes de seguir pro passo 9.

### 9. Rodar review

Chamar a sub-skill `review --spec` passando o código da task. Se a flag `--quick` foi passada pra esta skill, repassar pra `review --spec --quick`.

- Se o relatório retornar **Aprovado**: prosseguir.
- Se o relatório retornar **Ajustes necessários**: avaliar correções, aplicar as pertinentes na `spec.md` e seguir.
- Se o relatório retornar **Reprovado**: reescrever a spec com base no feedback e rodar a review novamente.

Verificações que o `--spec` faz (a partir da v7):
- **Estrutura sempre:** ACs têm IDs estáveis, cada REQ tem AC, todas as seções obrigatórias.
- **Lint sempre:** sem vazamento de implementação, sem vagueness, sem contradição.
- **Semânticas (skipadas com `--quick`):** cobertura input→spec profunda, cenários cobrem ACs, NFRs adequados, ortogonalidade, edge cases óbvios.

### 10. Executar hook `after spec`

Ler `GOD/hooks.md` e localizar a seção `# after spec`.

- Se o conteúdo for `skip-hook`: pular e seguir para o passo 11.
- Se houver instruções em linguagem natural: executá-las integralmente antes do relatório final.

Casos comuns: postar comentário no Jira da task com resumo da spec, notificar canal Slack, atualizar card Linear/Trello.

**Pós-execução do hook**, atualizar o frontmatter da spec recém-escrita com:

```yaml
last_published_at: {timestamp-iso-8601-utc}
published_to: [<lista de destinos extraída do hook executado, ex: jira, slack>]
```

Esses campos rastreiam ciência ativa de quem foi notificado. Se o hook for `skip-hook`, **não** definir esses campos (omitir do frontmatter).

### 10.5. Publicar via --target (v10.1, opcional)

Se a flag `--target <destino>` foi passada na invocação:

1. **Delegar à sub-skill `publish-spec`** passando `{cod}` e o target. Reusa a infra existente (publica no Jira via MCP, posta no Slack, etc.) — não duplica lógica.
2. **Capturar resultado** do `publish-spec`. Se sucesso, atualizar frontmatter com `last_published_at` e `published_to` (igual o hook `after spec` faria).
3. Se falha (MCP indisponível, target inválido), avisar o usuário e prosseguir — spec canônica em `<specs_path>` continua sendo a fonte da verdade.

Sem `--target`, pular este passo silenciosamente. Usuário pode rodar `publish-spec {cod}` manualmente depois.

### 11. Reportar resultado (ASCII)

Saída em blocos ASCII (box-drawing fora de fences) parametrizado por perfil.

**Estrutura:**

```
═══════════════════════════════════════════════════════════════════════════
  Spec criada: {cod} — {título}
  Perfil: {normal|critical}  ·  spec_version: {N}
  REQs: {N}  ·  ACs: {M}  ·  NFRs declarados: {K}/4
═══════════════════════════════════════════════════════════════════════════

┌─ Onde mora ─────────────────────────────────────────────────────────────
│ 📐 {tasks_dir}/{cod}.md
│ 📡 Publicado em: {jira/slack/— se hook after spec rodou}
│ 📤 Target adicional: {se --target foi usado}
└─────────────────────────────────────────────────────────────────────────

┌─ Análise heurística ────────────────────────────────────────────────────
│ Excessos tratados: {N} ({tipos})
│ Gaps fechados via Q&A: {N}
│ Self-validação: {ok | corrigido com usuário}
│ Tamanho: {simples | feature → N subtasks}
└─────────────────────────────────────────────────────────────────────────

{Bloco "Próximo passo" adaptado}
```

**Próximo passo por perfil:**

- **critical:** sugerir `publish-spec {cod}` → aguardar validação → `spec --review-feedback {cod}` se vier feedback → `init {cod}`.
- **normal:** sugerir `init {cod}` direto. Mencionar `spec --review-feedback` como opção se feedback chegar.
- **`--quick` ou `--target` usado:** suprimir bloco publish-spec (já publicou ou foi por flag).
- **feature split (passo 6.5 (a)):** listar subtasks geradas com contagens, sugerir `init {cod-1}` (primeira da ordem).

---

## Modo `batch` (invocação por init-tree)

Modo não-interativo pra processar folhas de árvore Jira em lote.

**Diferenças vs interativo:** pula Q&A (passo 6), pula confirmação de perfil, pula `review --spec` (passo 9) e hook `after spec` (passo 10). Marca frontmatter `draft: true`. Retorna silenciosamente.

**Refinamento posterior:** quando usuário roda `spec {cod}` interativo em spec com `draft: true`, oferecer:
- (a) Re-rodar Q&A completa, regenerar spec, remover `draft`, incrementar `spec_version`.
- (b) Refinar manualmente, rodar só `review --spec`.
- (c) Manter rascunho e abortar.

---

## Modo `--review-feedback` (loop de validação leve, pré-init)

Modo opt-in pra incorporar feedback recebido fora do GOD (comentário Jira, Slack, conversa). Roda apenas **antes do init** — se `GOD/tasks/{cod}/status.md` existe, **abortar** e orientar `update-spec`.

**Passos:**

1. **Solicitar feedback bruto** (cole comentário/mensagem).
2. **Checar `feedback_cycles`** no frontmatter. Se ≥ 2, alertar:

   > ⚠️ 3ª iteração consecutiva sem init. Considere conversa síncrona. Seguir mesmo assim? (s/n)

3. **Analisar feedback × spec** — identificar REQs/ACs afetados.
4. **Apresentar diff proposto** ("aplicar tudo? (s) ou ajustar antes? (a)").
5. **Aplicar:** incrementa `spec_version`, atualiza `updated_at`, incrementa `feedback_cycles`. Adiciona bloco em "Histórico de feedback":

   ```markdown
   ### v{N} — {timestamp}
   **Origem:** {Jira | Slack | conversa | texto livre}
   **Resumo:** {1 linha}
   **Aplicado:** {REQs/ACs alterados}
   ```

6. **Re-rodar `review --spec`** (sem `--quick`).
7. **Re-executar hook `after spec`** se configurado.
8. **Reportar:** `spec_version v{N-1} → v{N}` + `feedback_cycles {N}/2`.

**Reset do contador:** `init` ou `update-spec` rodando = reset pra 0.

---

## Guard-rails

- Dona única da spec inicial. `update-spec` (v9) escreve mudanças pós-init.
- Não fala de implementação — REQs/ACs são puramente comportamento.
- Não cria `GOD/tasks/{cod}/` (responsabilidade do `init`), não toca git.
- `--review-feedback` só roda antes do `init` (status.md ausente).
- **Task trivial não passa por aqui.** Spec aborta com sugestão de `init --type=trivial`. Não tente forçar uma "spec mínima" pra typo — isso polui o repo de specs.

---
name: god
description: |
  GOD (Goal Oriented Development) — Meta framework que orquestra o ciclo de vida completo de uma task. Fluxo v11: init → spec → [publish-spec] → plan → implement → pack-up. Init é entry point estrutural (cria pasta vazia); spec produz o WHAT canônico depois. v10 acrescenta architecture advisor opcional (principles + architecture) e domain rules opcionais (BRs com IDs derivados do domain frontmatter — agnóstico ao projeto). Inclui variantes (init-tree) e auxiliares (review, status, update-plan, update-spec, pause, resume, learn, code-like-me, upgrade) e integração com Jira/Figma. Use quando o usuário mencionar: "god", "nova task", "iniciar task", "init em lote", "iniciar epic", "iniciar várias tasks", "subtasks do jira", "spec da task", "criar spec", "atualizar spec", "spec mudou", "planejar task", "implementar task", "pack up", "pause", "resume", "pausar", "retomar", "learn", "conhecimento", "status das tasks", "upgrade god", "help", "regras de negócio", "BR aplicável", ou qualquer variação do ciclo de desenvolvimento orientado a objetivos.
tools: Read, Glob, Grep, Bash, Edit, Write, Agent
---

# GOD — Skill Orquestradora

> Skill principal do framework GOD. Orquestra o ciclo de vida de uma task: da inicialização até a entrega. Tem awareness de todas as sub-skills e roteia o usuário para a skill correta.

## Ciclo de vida de uma task (v11 — init estrutural + spec WHAT; v12 — auto + stack + ready)

```
install → init → spec → [publish-spec] → plan → implement → pack-up → [ready]
                  ↑                       ↑        ↑           ↑
               review                  review   review      review
               (spec)                  (plan)  (update)  (execution)
```

> **Adições v12:**
> - **Flag `--auto`** (em `init` e `init-tree`): encadeia o ciclo todo até `pack-up` sem gates de aprovação. Abre worktree (com symlink de `node_modules`) e segue spec → plan → implement → pack-up. Em falha irresolúvel, para e chama humano.
> - **Flag `--stack`** (em `init` e `init-tree`): lê `is blocked by` no Jira, monta DAG, grava `stack_parent` no `status.md`. `plan` usa branch do parent como `branch_base`; `implement` faz cascata de rebase contra o parent no início. PRs sempre abertos contra `main` (draft). Composável: `init-tree PROJ-100 --auto --stack`.
> - **Sub-skill `ready`**: step manual pós-pack-up. Tira PR de draft + adiciona reviewers de `GOD/config.md`. Modo recomendação (sem arg) cruza `stack_parent` com estado dos PRs e propõe lista em batch ("PROJ-101 mergeou → liberar PROJ-102, PROJ-103, PROJ-104?"). **Nunca dispara automático** — sempre humano.
> - **Sub-skill `spec-tree`**: usada por `init-tree --auto`. Q&A unificada em batch pra gerar N specs em uma sessão (em vez de N sessões individuais).
> - **Helper `_lib/parse_jira_deps.py`**: topo-sort + atribuição de `stack_parent` a partir de DAG de dependências do Jira.

> **Mudança v11:** init agora é o entry point estrutural — cria a pasta da task (`GOD/tasks/{cod}/`) com `plan.md` vazio e `status.md` (`phase: initialized`) **antes** de qualquer outra coisa. spec roda depois e atualiza esse mesmo status.md (transição `initialized → specified`). Espelha a simetria com `init-tree` (que também cria pasta primeiro). Init nunca tocou git, então a "spec-first como gate" da v9 era ceremonial — agora init é só bookkeeping puro.
>
> **Trivial:** mata o flag `--type=trivial`. Em vez disso, `init --profile=trivial` carimba label no status.md. Trivial salta spec e plan e vai direto pro `implement`. Implement detecta `phase: initialized + profile: trivial` e resolve branch sozinho.
>
> **Auto-init silencioso:** se o usuário invocar `spec {cod}` sem ter rodado init antes (hábito do fluxo v9), spec roda init programaticamente — sem fricção. State machine fica consistente, experiência pro usuário não muda.

1. **install** — Configura o projeto (executar apenas uma vez). Pergunta `specs_path` (onde a spec da task vai morar) e cria `GOD/config.md`.
2. **init** — Entry point estrutural. Aceita código da task (Jira/texto livre/ID curto) e cria `GOD/tasks/{cod}/` com `plan.md` vazio + `status.md` (`phase: initialized`). Aceita `--profile=trivial|normal|critical` (default `normal`) só pra carimbar label. Não toca em git, não busca dados externos.
3. **spec** — Produz o WHAT canônico. Aceita input bruto direto (Jira/texto livre), busca dados em Jira/Figma, detecta perfil da task (trivial/normal/critical), faz Q&A focada em escopo, escreve REQs em EARS, ACs com IDs estáveis, cenários e NFRs em `<specs_path>/tasks/{cod}.md`. Atualiza `status.md` pra `phase: specified`. Roda `review --spec`. Se status.md não existe, roda init programaticamente (auto-init silencioso).
4. **publish-spec** *(opcional, sugerido em perfil critical)* — Publica spec em Jira/Slack/stdout pra validar com stakeholder antes do plan.
5. **plan** — Lê a spec pronta. Detecta single vs multi-project, resolve branch+base, escreve o plano focado em **HOW** (arquitetura, arquivos, passos), referenciando ACs. Não toca em escopo nem em git.
6. **implement** — Cria a(s) branch(es) da task no git, executa o plano. Roda freshness check estendido: se a spec foi atualizada via `update-spec`, lista ACs alterados, cruza com `coverage.md` e oferece reabrir passos relacionados. Consulta a spec durante a escrita. Após escrever código, valida contra `learned-patterns.md`. **Detecta fluxo trivial** (`phase: initialized + profile: trivial`) — pula spec/plan e resolve branch sozinho.
7. **pack-up** — Finaliza a task (review, commit, push, PR). Carimba `spec_version_delivered` no PR + link do `{cod}-changelog.md` se houve mudança de escopo durante a task.

**Variante de entrada:**
- **init-tree** — variante de inicialização em lote: recebe um nó-raiz do Jira (Epic, Story, Task com subtasks), desce a árvore, cria pastas de contexto pra nós internos e cria estrutura de execução vazia (`plan.md` + `status.md` com `phase: initialized`) pra cada folha. **Não escreve specs em batch** (gerar rascunhos sem Q&A produzia lixo). O usuário roda `spec {cod}` por folha quando estiver pronto pra escrever cada spec.

**Ferramentas auxiliares (não são parte do fluxo linear):**
- **review** — Revisa qualidade em 3 modos: spec (`--spec` com semântica profunda; `--quick` pra só lint), descrição+spec vs plano (`--plan`), plano vs execução com cobertura de ACs (`--execution`). A partir da v8.1, cada modo delega pra **subagent isolado** com contexto fresco — fresh eyes sem viés de auto-validação. **v10.3:** modo configurável via `peer_review_default` em `GOD/config.md` (valores: `subagent` default, `inline`, `skip`). Flags CLI `--subagent`/`--inline`/`--skip` overridem pontual.
- **publish-spec** — Publica/republica a spec em destinos configuráveis (Jira, Slack, stdout, custom). Auxiliar manual ao hook `after spec`.
- **coverage** — Gera matriz "AC × validação" pra uma task dentro do fluxo do GOD. Parseia `// covers: AC-X` em testes + lê `coverage.md` (validações manuais). Usado pelo `pack-up` e `review --execution`, ou manual a qualquer momento. Tolerante por design — ACs órfãos viram alerta visual, decisão fica do dev.
- **status** — Dashboard de tasks em andamento e suas fases
- **update-spec** *(v9)* — Aplica mudança de escopo na spec de uma task que já passou por `init`. Pergunta motivo, edita spec, bumpa `spec_version`, escreve delta em `<specs_path>/tasks/{cod}-changelog.md`. Próximo `implement` detecta drift (freshness check estendido) e oferece reabrir passos.
- **update-plan** — Atualiza o plano durante a implementação quando surgem mudanças
- **pause** — Pausa uma task em andamento, registra observação opcional no `changelog.md` e marca `paused: true` no status. Pode ser invocada pelo usuário ou por `implement`/`plan` quando detectam barreira
- **resume** — Retoma uma task pausada, carrega contexto do changelog, remove `paused` do status e delega de volta à skill da fase ativa
- **learn** — Transforma uma task executada em conhecimento reutilizável (ativação explícita pelo usuário). Numa mesma invocação executa duas ações em sequência: (1) escreve entrada da task em `GOD/knowledge.md`; (2) pergunta ao usuário por regras generalizáveis e as anexa em `GOD/learned-patterns.md`. Marca `learned: true` no `status.md` sem alterar `phase`
- **clean-up** — Arquiva tasks em `packed-up` cujos PRs já foram mergiados (move para `GOD/tasks/.archived/`). Oferece rodar `learn` antes de arquivar tasks ainda não aprendidas
- **code-like-me** — Implementação cirúrgica que segue padrões do projeto (usada como flag do implement)
- **upgrade** — Migra instalações do GOD de uma versão para outra (expansível por versão)

## Delegação pra `sub-skills/_lib/` (v10.2)

A partir da v10.2, processos puramente determinísticos (parsing de comentários, lint estrutural, atualização de YAML, geração de tabelas) são feitos por **scripts Python** em `sub-skills/_lib/` em vez do LLM. Economiza tokens significativamente.

**Padrão de delegação** (sub-skills referenciam este padrão; não repetir lógica em cada SKILL.md):

1. **Verificar python3 ≥ 3.8** disponível: `command -v python3 && python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)'`.
2. **Verificar script existe**: `[ -f sub-skills/_lib/<script>.py ]`.
3. **Rodar via Bash**: `python3 sub-skills/_lib/<script>.py <args>`. Capturar stdout (JSON) e stderr separados.
4. **Se exit 0** → parsear JSON da stdout, usar resultado.
5. **Se exit != 0 ou exception** → **avisar usuário UMA vez** com `⚠️ Script {nome} falhou (exit {code}): {stderr resumido}. Caindo pro fallback LLM.` e seguir o caminho fallback documentado na própria skill.
6. **Se python3 ausente** → seguir fallback silenciosamente (instalar python3 já foi sugerido pelo `install` ou `doctor`).

**Garantia crítica:** **falha de script NUNCA interrompe o processo da skill.** Skill sempre tem caminho fallback funcional via LLM. Scripts são otimização, não dependência rígida.

**Garantia de carregamento sob demanda:** scripts em `sub-skills/_lib/*.py` **NUNCA devem ser lidos via tool Read** pelo agent. Apenas executados via Bash. Eles não são skills (não têm SKILL.md, não são carregados automaticamente pelo Claude Code). Tratá-los como "leitura pra entender" infla contexto sem ganho — o agente já sabe o **contrato** do script (argumentos + JSON de saída) pela documentação aqui no SKILL.md raiz; conteúdo do script é detalhe de implementação. Mesma regra vale pro helper `debug_log.py` (v10.6) — invocado só quando `--debug` está presente, sem Read em nenhuma circunstância.

**Scripts disponíveis:**

| Script | Função | Skills que delegam |
|--------|--------|---------------------|
| `parse_coverage.py` | Matriz AC × validação a partir do diff/repo | coverage, pack-up, review --execution |
| `parse_rules.py` | Parser de `// rule: BR-X` no diff (v10) | pack-up, review --execution |
| `parse_spec.py` | Extrai frontmatter + REQs + ACs da spec | plan, implement, review |
| `validate_spec.py` | Lint estrutural da spec (REQ tem AC, IDs, palavras-tabu) | spec passo 8.5, review --spec |
| `freshness_check.py` | Compara spec_version atual × spec_version_consumed | plan, implement |
| `update_status.py` | Read-modify-write de status.md | spec, init, plan, implement, pack-up, learn, pause, resume, update-spec |
| `gen_pr_description.py` | Markdown do PR description a partir de JSON | pack-up |

Todos os scripts: Python 3.8+ stdlib only. Cross-platform (macOS, Linux, WSL). Rodar `python3 <script>.py --help` pra ver argumentos.

## Padrão de context blob (v10.4)

A partir da v10.4, skills do fluxo principal podem **passar artefatos pré-lidos** pra sub-skills/subagents em vez de cada um ler do disco. Reduz leituras redundantes (mesmo `status.md` lido 3x numa execução de pack-up vira 1x).

### Quando usar

Skills que orquestram outras skills/subagents:
- **`pack-up`** — chama `coverage`, `review --execution`. Carrega context no início e passa adiante.
- **`spec`** — chama `review --spec`. Pode passar context (input bruto, dados Jira, knowledge consultado).
- **`plan`** — chama `review --plan`. Pode passar context (spec, description).

### Estrutura do context blob

JSON serializável com chaves específicas por skill. Exemplo pra pack-up:

```json
{
  "task": "PROJ-123",
  "status": "<conteúdo de GOD/tasks/PROJ-123/status.md>",
  "plan": "<conteúdo de plan.md>",
  "spec": "<conteúdo da spec, se cabe inline>",
  "spec_path": "docs/specs/tasks/PROJ-123.md",
  "coverage": "<conteúdo de coverage.md, se existe>",
  "patterns": "<conteúdo de GOD/patterns.md>",
  "hooks": "<conteúdo relevante de hooks.md>"
}
```

### Threshold pra arquivos grandes (lazy via path)

Pra evitar prompt gigante:

```
Se um arquivo > 8000 chars (~2000 tokens):
  - NÃO incluir o conteúdo no context blob
  - Incluir apenas o path (ex: "spec_path": "...")
  - Sub-skill/subagent decide se lê tudo ou faz scan parcial
Senão:
  - Incluir conteúdo inline
```

Threshold é heurístico, não rígido. Skill chamadora decide.

### Como sub-skill consome

Sub-skills/subagents ficam **flexíveis** — aceitam context inline mas têm fallback pra ler do disco. Padrão:

```
1. Verificar se context foi passado (chave existe e não é vazia).
2. Se sim: usar direto, sem invocar Read.
3. Se não: ler do disco (caminho original v10.3).
```

**Garantia:** retrocompat preservada. Invocação sem context blob continua funcionando.

### Como subagent recebe

Skill chamadora invoca `Agent` tool com prompt que inclui o context:

```
Agent({
  description: "Review execution PROJ-123",
  prompt: """
  CONTEXTO PRÉ-CARREGADO (não invoque Read pra estes arquivos):
  
  === status.md ===
  {context.status}
  
  === plan.md ===
  {context.plan}
  
  ...
  
  INSTRUÇÕES:
  {prompt original do modo}
  """
})
```

Subagent reconhece o cabeçalho `=== arquivo ===` e usa o conteúdo direto. Pra arquivos não pré-carregados (ex: arquivos do diff em `--execution`), continua usando Bash/Read normalmente.

## Debug log opt-in (v10.6)

Skills do fluxo principal (init, spec, plan, implement, pack-up) aceitam flag `--debug` em qualquer invocação. Quando presente, registra ações em `GOD/tasks/{cod}/debug.log` (JSON Lines) usando o helper `sub-skills/_lib/debug_log.py`.

**Sem flag, nenhum log é escrito** — zero overhead em uso normal. Opt-in **explícito** por invocação. Se você quer logar uma sessão completa, passa `--debug` em **cada skill chamada** (não há flag de sessão persistente — design intencional pra evitar "esqueci ligado").

### Quando logar

Pontos crítics em cada skill, no estilo:

```bash
python3 sub-skills/_lib/debug_log.py \
  --task {cod} \
  --skill {nome} \
  --step "X.Y descrição" \
  --action {verbo_curto} \
  --details '{"key": "value"}' \
  --god-root {god_root}
```

Verbo de `--action` (convenção):
- `entered` — passo iniciado
- `delegated` — delegou pra script Python ou subagent (`--details` inclui qual)
- `fallback_llm` — caiu pro caminho LLM (script falhou ou ausente)
- `batch_consumed` — usou JSON do batch (v10.5)
- `context_blob_used` — consumiu artefato pré-carregado (v10.4)
- `skipped` — passo pulado (ex: hook skip-hook, profile trivial)
- `completed` — passo terminou OK
- `error` — falha que não interrompeu (caiu pro fallback)

`--details` é JSON livre. Inclua sinais correlacionados com custo: `acs` (contagem), `diff_files`, `diff_size_bytes`, `mode` (subagent/inline), `subagent_type`.

### Análise depois

Pra ler o log:

```bash
cat GOD/tasks/{cod}/debug.log | jq .            # com jq instalado
cat GOD/tasks/{cod}/debug.log                    # sem jq
```

Ou agregar:

```bash
# quantos eventos por skill
cat GOD/tasks/{cod}/debug.log | jq -r .skill | sort | uniq -c

# quais passos rodaram fallback_llm
cat GOD/tasks/{cod}/debug.log | jq 'select(.action=="fallback_llm")'
```

### Garantias

- **Falha do `debug_log.py` nunca interrompe a skill** — chamada é fire-and-forget. Se o helper falhar (disk cheio, permissão, etc.), o fluxo continua. Padrão de invocação: rodar via Bash em `&` ou capturar erro silenciosamente.
- **Sem `--debug`, helper nunca é invocado.** Sem flag, zero overhead — agent não toca no script, não menciona, não verifica existência.
- **Helper nunca é lido via Read tool.** É script Python; agent só **executa** via Bash quando flag está presente. Conteúdo do script não entra no contexto.
- **Sem skill `debug-log` formal.** O helper é arquivo `.py` em `_lib/`; não há `SKILL.md` correspondente, então Claude Code não carrega o helper automaticamente em invocação alguma.

## Hooks do fluxo

Cada step do fluxo principal (`init`, `spec`, `plan`, `implement`, `pack-up`) executa hooks opcionais antes e depois de sua lógica principal, lidos de `GOD/hooks.md`. Se o slot estiver com `skip-hook`, pula. Se tiver instruções em linguagem natural, a skill executa.

> **A partir da v7:** a skill `spec` ganhou hooks dedicados (`before spec` e `after spec`). Caso de uso típico do `after spec`: publicar a spec recém-criada como comentário no Jira ou mensagem no Slack pra que PM/UX/CTO fiquem sabendo automaticamente, sem depender de eles abrirem o repo.

Ferramentas auxiliares (learn, update-plan, review, status, pause, resume, code-like-me, publish-spec, upgrade) **não** têm hooks.

## Mapa de sub-skills

| Skill | Localização | Quando usar |
|-------|-------------|-------------|
| `install` | `sub-skills/install/SKILL.md` | Primeira vez no projeto — configura GOD |
| `init` | `sub-skills/init/SKILL.md` | **Entry point estrutural (v11)** — cria `GOD/tasks/{cod}/` com `plan.md` vazio + `status.md` (`phase: initialized`). Não exige spec. Aceita `--profile=trivial\|normal\|critical` (default `normal`) só pra carimbar label. |
| `spec` | `sub-skills/spec/SKILL.md` | Produz o WHAT canônico depois do init. Atualiza `status.md` pra `phase: specified`. Auto-init silencioso se status.md ausente. Modos: interativo (default), `batch` (legado, não chamado por init-tree v11), `--review-feedback` (incorpora feedback antes do plan), `--quick` (skip semântica). **v10.1:** roda análise heurística pré-Q&A (detecção de excessos/gaps via `heuristics.md`), self-validação inline, oferece feature split, aceita `--target` pra publicar direto. |
| `init-tree` | `sub-skills/init-tree/SKILL.md` | Iniciar em lote via árvore do Jira (Epic/Story + subtasks). Cria pastas de contexto + estrutura de execução vazia por folha (`phase: initialized`). **Não escreve specs** — usuário escreve cada uma com `spec {cod}` quando estiver pronto. |
| `publish-spec` | `sub-skills/publish-spec/SKILL.md` | Publicar/republicar a spec em targets externos (Jira, Slack, stdout) — manual |
| `coverage` | `sub-skills/coverage/SKILL.md` | Gerar matriz AC × validação pra uma task. Manual ou via pack-up/review |
| `plan` | `sub-skills/plan/SKILL.md` | Planejar a implementação técnica (HOW) |
| `implement` | `sub-skills/implement/SKILL.md` | Executar o plano. Freshness check estendido (v9) detecta drift de spec via changelog. |
| `pack-up` | `sub-skills/pack-up/SKILL.md` | Finalizar e entregar a task. Carimba `spec_version_delivered` no PR. |
| `ready` *(v12)* | `sub-skills/ready/SKILL.md` | Pós pack-up: tira PR de draft + adiciona reviewers do `GOD/config.md`. Suporta modo recomendação (sem arg) que cruza `stack_parent` com estado dos PRs no GitHub. Sempre manual — `--auto` não dispara. |
| `spec-tree` *(v12)* | `sub-skills/spec-tree/SKILL.md` | Q&A unificada em batch pra gerar specs de N folhas. Roda dentro de `init-tree --auto` antes do loop, ou opt-in manual em árvores já inicializadas. |
| `review` | `sub-skills/review/SKILL.md` | **(v10.4)** Wrapper de roteamento — delega pra `review-spec`/`review-plan`/`review-execution`. Mantém invocação `review --modo` retrocompatível |
| `review-spec` | `sub-skills/review-spec/SKILL.md` | **(v10.4)** Verificações específicas do modo `--spec` (estrutura + lint + semântica). |
| `review-plan` | `sub-skills/review-plan/SKILL.md` | **(v10.4)** Verificações específicas do modo `--plan` (cobertura ACs, scope creep, considerações arquiteturais). |
| `review-execution` | `sub-skills/review-execution/SKILL.md` | **(v10.4)** Verificações específicas do modo `--execution` (passos executados, cobertura, BRs anotadas). |
| `status` | `sub-skills/status/SKILL.md` | Ver estado das tasks |
| `doctor` | `sub-skills/doctor/SKILL.md` | **(v10.2)** Diagnóstico do ambiente: python3, git, gh, MCPs, GOD/ consistência, scripts em `_lib/`, tasks ativas. Read-only. |
| `update-spec` | `sub-skills/update-spec/SKILL.md` | **(v9)** Aplicar mudança de escopo na spec pós-init. Bumpa `spec_version`, escreve em `{cod}-changelog.md` |
| `update-plan` | `sub-skills/update-plan/SKILL.md` | Alterar plano durante implementação |
| `pause` | `sub-skills/pause/SKILL.md` | Pausar task em andamento e registrar observação |
| `resume` | `sub-skills/resume/SKILL.md` | Retomar task pausada e continuar |
| `learn` | `sub-skills/learn/SKILL.md` | Transformar task executada em conhecimento |
| `clean-up` | `sub-skills/clean-up/SKILL.md` | Arquivar tasks em `packed-up` com PRs mergiados |
| `code-like-me` | `sub-skills/code-like-me/SKILL.md` | Flag do implement para código cirúrgico |
| `upgrade` | `sub-skills/upgrade/SKILL.md` | Migrar instalação entre versões do GOD |

## Roteamento inteligente

Quando o usuário interagir, identifique a intenção e delegue para a sub-skill correta:

| Intenção do usuário | Sub-skill |
|---------------------|-----------|
| "instalar", "configurar", "setup" | `install` |
| "nova task", "iniciar task", "criar estrutura da task", código do Jira, link do Jira | `init` (entry point v11) |
| "task trivial", "typo", "trocar copy", "atualizar dep" + código identificador | `init --profile=trivial` (depois `implement` direto) |
| "criar spec", "spec da task", "escrever spec", "escopo", "requisitos da task", "critérios de aceitação" | `spec` (auto-init silencioso se status.md não existir) |
| "init em lote", "iniciar epic", "iniciar várias tasks", "subtasks do jira", "criar tasks da árvore" | `init-tree` |
| "feedback do PM antes do init", "stakeholder respondeu", "incorporar feedback pré-init" | `spec --review-feedback` |
| "spec mudou", "PM mudou de ideia", "mudança de escopo", "update spec", "atualizar spec depois do init" | `update-spec` |
| "publicar spec", "republicar spec", "compartilhar spec", "publish spec" | `publish-spec` |
| "cobertura", "coverage", "que ACs estão testados", "matriz de cobertura", "AC sem teste" | `coverage` |
| "planejar", "criar plano", "como implementar" | `plan` |
| "implementar", "executar", "codar", "desenvolver" | `implement` |
| "finalizar", "entregar", "pack up", "commitar e subir PR" | `pack-up` |
| "ready", "tirar PR de draft", "liberar PR", "PR pronto", "adicionar reviewers", "marcar PR como pronto" | `ready` *(v12)* |
| "init em auto", "ciclo automático", "rodar tudo", "init até o PR sem parar", "modo autopilot da task" | `init --auto` (single) ou `init-tree --auto` (lote) *(v12)* |
| "stacked PR", "PR em cascata", "task que depende de outra task em andamento", "init com stack", "empilhar PRs" | `init --stack` ou `init-tree --stack` *(v12)* |
| "Q&A em batch", "spec de várias tasks juntas", "spec tree", "specs unificadas" | `spec-tree` *(v12)* |
| "status", "como estão as tasks", "dashboard" | `status` |
| "doctor", "god doctor", "checar god", "verificar instalação", "está tudo ok?", "diagnosticar god", "o que falta no setup" | `doctor` |
| "mudar o plano", "atualizar plano", "o plano mudou" | `update-plan` |
| "pause", "pausar", "pausar task", "tô travado", "parar aqui", "retomo depois" | `pause` |
| "resume", "retomar", "continuar task", "voltar na task", "destravei" | `resume` |
| "registrar aprendizado", "learn", "o que aprendi", "transformar em conhecimento" | `learn` |
| "clean-up", "limpar tasks", "arquivar tasks", "remover tasks concluídas", "arrumar a casa" | `clean-up` |
| "upgrade", "atualizar god", "migrar god", "v1 para v2" | `upgrade` |
| "migrate", "migrar do gdd", "migrar gdd para god", "tenho o gdd instalado" | `upgrade` |

## Verificação de versão instalada

Antes de delegar para **qualquer** sub-skill exceto `install` e `upgrade`, verificar:

1. **Existe `GOD/VERSION`?**
   - Se não existe e `GDD/` existe (pasta da skill antiga) → instalação legada da skill GDD. Alertar o usuário e sugerir `upgrade` (ou `migrate`) para migrar de GDD para GOD. Não executar a skill solicitada até a migração rodar.
   - Se não existe e `GOD/` existe (sem VERSION) → instalação v1. Alertar o usuário e sugerir `upgrade` antes de prosseguir. Não executar a skill solicitada até o upgrade rodar.
   - Se não existe e nem `GOD/` nem `GDD/` existem → sugerir `install`.
   - Se existe → ler o valor.

2. **Valor de `GOD/VERSION` corresponde à versão atual do GOD (`v12`)?**
   - Sim → prosseguir com a skill solicitada.
   - Não → alertar o usuário e sugerir `upgrade`.

## Verificação de pré-requisitos

Antes de delegar para uma sub-skill, verifique se os pré-requisitos foram cumpridos:

| Sub-skill | Pré-requisitos |
|-----------|----------------|
| `install` | Nenhum (se `GOD/` já existe, sugerir `upgrade` em vez de reinstalar) |
| `init` | `GOD/` deve existir na versão atual. Aceita qualquer código (Jira/texto livre). Não exige spec, não toca git, não busca dados externos. Aceita `--profile=trivial\|normal\|critical` opcional (default `normal`). |
| `spec` | `GOD/` deve existir na versão atual. Aceita input bruto direto. Precisa ler `GOD/config.md` para resolver `specs_path` (se ausente, usar default `docs/specs/`). Se `GOD/tasks/{cod}/status.md` não existir, roda init programaticamente (auto-init silencioso). Modo `--review-feedback` exige `phase ∈ {initialized, specified}` (não rodou plan ainda). Modo `batch` ainda existe mas não é mais chamado por init-tree (init-tree v11 não escreve specs). |
| `init-tree` | `GOD/` deve existir na versão atual; MCP Atlassian disponível e autenticado |
| `publish-spec` | Spec deve existir em `<specs_path>/tasks/{cod}.md`. Targets desconhecidos exigem definição em `hooks.md` como `# publish-spec target: <nome>` |
| `coverage` | `<specs_path>/tasks/{cod}.md` deve existir (spec criada). Se ausente, retorna "não aplicável" silenciosamente |
| `plan` | `GOD/tasks/{cod}/status.md` deve ter `spec_path` populado e ser não-trivial. Se ausente, sugerir rodar `spec` + `init`. Precisa ler `GOD/patterns.md` para resolver branch |
| `implement` | `GOD/tasks/{cod}/plan.md` deve estar preenchido e `status.md` deve ter `branch` e `branch_base` populados (plan executado). Em modo trivial, plan é pulado e implement resolve a branch. Se algo essencial faltar, sugerir rodar `plan` primeiro |
| `pack-up` | Deve haver alterações no git para commitar (implement executado). Se não houver, informar o usuário |
| `ready` | `gh` CLI instalado e autenticado. Tasks com `phase: packed-up` no `GOD/tasks/`. `GOD/config.md` legível (seção `## reviewers` opcional — vazia → só tira de draft). |
| `spec-tree` | Folhas em `GOD/tasks/*/` já inicializadas por `init-tree` (`phase: initialized`). MCP Atlassian autenticado. `specs_path` configurado em `GOD/config.md`. |
| `update-spec` | `GOD/tasks/{cod}/status.md` deve existir com `phase ∈ {planned, implementing, implemented, packed-up}` (plan rodou). Se `phase ∈ {initialized, specified}`, sugerir `spec` ou `spec --review-feedback` em vez. `<spec_path>` deve apontar pra arquivo válido. |
| `doctor` | Nenhum — skill é read-only e detecta o que existe no ambiente |
| `update-plan` | `GOD/tasks/{cod}/plan.md` deve existir e estar preenchido |
| `pause` | `GOD/tasks/{cod}/status.md` deve existir e `phase ≠ packed-up`; não deve estar já pausada |
| `resume` | `GOD/tasks/{cod}/status.md` deve existir com `paused: true` |
| `learn` | Task deve ter pelo menos um commit registrado (pack-up executado) |
| `clean-up` | `GOD/tasks/` deve existir; `gh` CLI instalado e autenticado |
| `status` | `GOD/` deve existir |
| `upgrade` | `GOD/` deve existir (skill detecta versão automaticamente) |

## Recuperação e continuação

Se o usuário retorna após uma interrupção:

1. **Verificar estado atual** — Rodar `status` internamente para entender onde parou
2. **Checar pausa antes de qualquer coisa** — Ler `GOD/tasks/{cod}/status.md` (campo `paused`):
   - Se `paused: true` → sugerir `resume` antes de qualquer outra skill. O contexto da pausa está em `changelog.md` e `resume` cuida da retomada
3. **Identificar fase** — Se a task não está pausada, ler o campo `phase` e sugerir o próximo passo:
   - `initialized` → sugerir `spec` (ou `implement` direto se `profile: trivial`)
   - `specified` → sugerir `plan`
   - `planned` → sugerir `implement`
   - `implementing` → sugerir continuar o `implement` ou rodar `update-plan` se o plano mudou; rodar `update-spec` se a spec mudou
   - `implemented` → sugerir `pack-up`
   - `packed-up`:
     - Se `learned: false` → sugerir `learn` (opcional) e depois `clean-up` quando os PRs forem mergiados
     - Se `learned: true` → sugerir `clean-up` quando os PRs forem mergiados
4. **Fallback** — Se `status.md` não existir (raro em v11, geralmente significa task v9/v10 que não rodou ainda OU pasta criada manualmente):
   - Pasta `GOD/tasks/{cod}/` existe sem status.md → sugerir `init {cod}` pra criar estrutura mínima e seguir
   - `<specs_path>/tasks/{cod}.md` existe mas pasta não → sugerir `init {cod}` (vai criar pasta) e depois `plan` (porque spec já existe)
   - Nada existe → sugerir `init {cod}` (entry point v11). Se cosmético, usar `init {cod} --profile=trivial` e seguir direto pro `implement`
   - **Casos legacy v8:** `GOD/tasks/{cod}/description.md` existe mas spec ainda não → sugerir `spec {cod}` (vai ler o description.md por retrocompat e ativar auto-init silencioso); `plan.md` preenchido mas sem alterações no git → `implement`; alterações não commitadas → `pack-up`
   - PR já criado → task finalizada
5. **Sugerir próximo passo** — Informar o usuário onde parou e qual skill rodar

## Comando: `help`

Quando o usuário pedir ajuda, disser "help", "o que posso fazer?", "como funciona?" ou qualquer variação:

1. **Verificar se o projeto já foi instalado** — checar se `GOD/` existe
2. **Verificar versão** — checar `GOD/VERSION`; se desatualizada, sugerir `upgrade` antes de tudo
3. **Verificar se há tasks em andamento** — checar `GOD/tasks/`
4. **Montar resposta contextual:**

**Se o projeto NÃO foi instalado:**

```
👋 **Bem-vindo ao GOD — Goal Oriented Development!**

O GOD orquestra o ciclo completo de uma task: da spec à entrega do PR.

🚀 **Para começar, rode `install`** — isso vai configurar o projeto criando a pasta GOD/ com:
  • VERSION — versão instalada (atualmente v11)
  • config.md — configuração local (specs_path: onde a spec da task vai morar)
  • knowledge.md — registro de tasks finalizadas (escrito apenas pelo `learn`)
  • patterns.md — convenções do projeto (branch, commit, PR, ações finais)
  • learned-patterns.md — regras generalizáveis escopadas (geral/linguagem/projeto), escritas pelo `learn` após revisão de PR e aplicadas pelo `implement` após a escrita de código
  • hooks.md — pontos de extensão por step (before/after de spec, init, plan, implement, pack-up)
  • tasks/ — pasta onde cada task terá plan e status (sem `description.md` em v9+ — o input bruto vai pra spec)

A v11 entrega **init estrutural + spec WHAT**:
  • Init agora é o entry point: `init → spec → [publish-spec] → plan → implement → pack-up`. Cria a pasta da task vazia (`plan.md` + `status.md` com `phase: initialized`) antes de qualquer outra coisa. Espelha simetria com `init-tree`.
  • Spec roda depois e atualiza o `status.md` (transição `initialized → specified`). Se status.md não existir (usuário invocou spec direto, hábito v9), spec roda init programaticamente — sem fricção.
  • Mata flag `--type=trivial` do init. Em vez disso, `init --profile=trivial` carimba label no status. Trivial salta spec/plan e vai direto pro implement (que detecta `phase: initialized + profile: trivial` e resolve branch sozinho).
  • Init-tree v11 não escreve mais specs em batch (gerar rascunhos sem Q&A produzia lixo). Cria pastas de contexto + estrutura de execução vazia por folha (`phase: initialized`). Usuário roda `spec {cod}` por folha quando estiver pronto.
  • Tudo da v9 (spec viva via `update-spec`, `spec_version_delivered` no PR, freshness check estendido) continua funcionando.

A v10 entrega **Architecture advisor + Domain rules** (artefatos opcionais e configuráveis):
  • `principles_path` (default `GOD/principles.md`) — princípios duradouros do projeto. `plan` lê e gera bloco "Considerações arquiteturais" sinalizando desvios sem bloquear.
  • `architecture_path` (default `GOD/architecture.md`) — padrões "preferidos mas negociáveis". Lido junto com principles. Flags `--skip-architecture`, `--refactor`, `--preserve` no `plan`.
  • `domains_path` (default `<specs_path>/domains/`) — pasta com arquivos `<dominio>.md`, BRs com IDs derivados do `domain:` do frontmatter (ex: `BR-PAYMENTS-007`). Agnóstico ao projeto.
  • `spec` sugere `applicable_rules` no frontmatter da spec baseado em description (heurística + confirmação).
  • `implement` sugere comentário `// rule: BR-X — descrição` no código onde a invariante é enforced.
  • `pack-up` injeta tabela "BRs aplicáveis × anotadas" no PR (similar à matriz de cobertura da v8).
  • Tudo opcional: quem não ativar (deixar paths vazios em `config.md`), fluxo segue silenciosamente.

A v10.1 (patch transversal) unifica a skill `spec` com qualidades antes restritas à skill global `god-spec`:
  • Análise heurística pré-Q&A: detecta excessos (HOW dentro do WHAT — pseudo-código, framework leak, schema técnico) e gaps (NFRs ausentes, ator não nomeado, cenários de erro). Tabelas em `sub-skills/spec/heuristics.md`.
  • Q&A focada apenas em gaps detectados — não pergunta blocos completos quando o input já cobre.
  • Seção `## Notas técnicas (input pro plan)` no template — preserva pseudo-código que veio no input sem contaminar REQs/ACs.
  • Self-validação inline antes de delegar pro `review --spec` — corrige trivial sozinha (auto-numerar IDs, adicionar NFRs com placeholders, mover framework leak).
  • Feature/subtask split inline — quando heurística detecta feature, oferece quebrar em spec pai + N subtasks (alternativa ao `init-tree` quando a árvore Jira ainda não existe).
  • Flag `--target jira/slack/file/stdout/clipboard` — após escrever spec canônica, publica adicionalmente no destino (delega pra `publish-spec` internamente).
  • Apresentação ASCII no relatório final.
  • Resultado: **uma fonte única** pra escrever bem o WHAT — `god-spec` global continua existindo só como wrapper offline pra projetos sem GOD instalado.

Tudo da v6/v7/v8/v9 segue funcionando: spec extraída, review semântico, freshness check, publish-spec, rastreabilidade AC × validação, spec viva.

Após instalar, preencha o `patterns.md` com as convenções do seu projeto. Os hooks e os artefatos da v10 (principles/architecture/domains) são opcionais.

Integrações opcionais (não obrigatórias):
  • Jira (Atlassian MCP) — busca automática de tasks
  • Figma (Figma MCP) — análise de design durante planejamento
```

**Se a instalação está em versão antiga:**

```
⚠️ **GOD detectado em versão anterior**

A versão atual é v11 mas sua instalação está em {versão-detectada}.

Rode `upgrade` para migrar sua estrutura automaticamente — seus valores (patterns, tasks, knowledge) são preservados.
```

**Se o projeto JÁ foi instalado, está na versão atual e NÃO há tasks:**

```
📋 **GOD — Pronto para começar!**

Seu projeto está configurado. Para iniciar sua primeira task (v11 — init estrutural + spec WHAT):

1. `init` — Entry point. Passe o link/código do Jira, código curto ou descrição livre
   → Cria `GOD/tasks/{cod}/` com `plan.md` vazio + `status.md` (`phase: initialized`)
   → Não toca em git, não busca dados externos, não exige spec
   → Aceita `--profile=trivial|normal|critical` (default `normal`) só pra carimbar label

2. `spec` — Produz o WHAT canônico
   → Aceita input direto. Busca dados em Jira/Figma, faz Q&A focada em escopo
   → Detecta perfil: `trivial` (aborta — pule pro implement), `normal` (default), `critical` (sugere publish-spec antes do plan)
   → Escreve REQs em EARS, ACs com IDs estáveis, cenários e NFRs em `<specs_path>/tasks/{cod}.md`
   → Atualiza status.md pra `phase: specified`, popula `spec_path` e `spec_version_consumed`
   → Roda `review --spec` antes de finalizar
   → Auto-init silencioso: se status.md não existir, roda init programaticamente
   → Modo `--review-feedback`: incorpora feedback antes do plan (incrementa spec_version)
   → Para mudança trivial (typo, copy, dep upgrade): use `init {cod} --profile=trivial` e pule direto pro implement

3. `publish-spec` *(opcional, sugerido em perfil critical)* — Publica spec pra validação externa
   → Targets configuráveis (Jira, Slack, stdout, custom)
   → Use antes do `plan` quando quiser travar a spec com PM/UX

4. `plan` — Lê a spec e produz o plano técnico
   → Consulta knowledge, lê CLAUDE.md/ARCHITECTURE.md, resolve branch
   → Foca exclusivamente em HOW (arquitetura, arquivos, passos)
   → Cada passo do plano referencia ACs específicos da spec

5. `implement` — Cria a(s) branch(es) no git e executa o plano
   → **Freshness check estendido**: se a spec foi atualizada via `update-spec`, lê o changelog, cruza ACs alterados com `coverage.md` e oferece reabrir passos
   → **Detecta fluxo trivial** (`phase: initialized + profile: trivial`): pula spec/plan e resolve branch sozinho
   → Por padrão aplica `code-like-me`. Use `--skip-code-like-me` pra desativar
   → Anota `// covers: AC-X` nos testes (alimenta a matriz de cobertura)
   → Verifica contra `learned-patterns.md`

6. `pack-up` — Finaliza e entrega
   → Review (com cobertura de ACs), commit, push, PR
   → Carimba `spec_version_delivered` no PR + link do `{cod}-changelog.md` se houve mudança durante a task

Ferramentas auxiliares (quando precisar):
  • `init-tree` — Iniciar em lote via árvore Jira (cria contextos + estrutura vazia por folha; não escreve specs)
  • `update-spec` — Aplicar mudança de escopo pós-plan (bumpa spec_version, escreve em changelog)
  • `update-plan` — Alterar plano durante implementação
  • `publish-spec` — Publicar/republicar spec em targets externos
  • `coverage` — Matriz AC × validação pra uma task (manual ou via pack-up)
  • `status` — Ver dashboard de tasks
  • `pause` / `resume` — Pausar e retomar uma task em andamento
  • `learn` — Transformar task em conhecimento (ativação explícita)
  • `clean-up` — Arquivar tasks em `packed-up` cujos PRs já foram mergiados
  • `upgrade` — Migrar para versão mais nova do GOD
```

**Se há tasks em andamento:**

Rodar `status` internamente e apresentar o dashboard junto com a sugestão do próximo passo:

```
📋 **GOD — Você tem tasks em andamento!**

{dashboard do status}

💡 Sugestão: {próximo passo baseado na fase da task mais recente}

Fluxo v11 (init estrutural + spec WHAT):
  • `init`         — **Entry point estrutural** (cria pasta vazia com `phase: initialized`). `--profile=trivial` salta spec/plan
  • `spec`         — Produz o WHAT canônico (escopo, ACs, cenários, NFRs em `<specs_path>/tasks/{cod}.md`); auto-init se status.md ausente
  • `publish-spec` — Publicar pra validar com stakeholder (sugerido em perfil critical)
  • `init-tree`    — Iniciar em lote via árvore Jira (cria contextos + pastas vazias por folha; não escreve specs)
  • `plan`         — Criar plano técnico (arquitetura, arquivos, passos — referencia ACs)
  • `implement`    — Executar o plano (cria a branch no git, freshness check estendido, detecta fluxo trivial)
  • `pack-up`      — Finalizar e entregar (commit + PR com `spec_version_delivered` + link do changelog)

Ferramentas auxiliares:
  • `update-spec`  — Mudança de escopo pós-plan: bumpa spec_version, escreve em changelog
  • `update-plan`  — Alterar plano durante implementação
  • `coverage`     — Matriz AC × validação pra uma task (v10.2: delega pra script Python quando disponível)
  • `learn`        — Transformar task em conhecimento (ativação explícita)
  • `clean-up`     — Arquivar tasks em `packed-up` cujos PRs já foram mergiados
  • `status`       — Ver dashboard completo
  • `doctor`       — *(v10.2)* Diagnóstico do ambiente: python3, git, gh, MCPs, GOD/ consistência. Read-only.
  • `pause`        — Pausar task em andamento e registrar observação no changelog
  • `resume`       — Retomar task pausada
  • `upgrade`      — Migrar para versão mais nova do GOD
```

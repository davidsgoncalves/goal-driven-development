# GOD — Goal Oriented Development

Meta framework de skills do Claude Code pra desenvolvimento orientado a objetivos com **Spec-Driven Development** integrado. Orquestra o ciclo de vida completo de uma task — da spec à entrega do PR — em sub-skills focadas que se comunicam entre si.

## Pra quem é

- Devs que usam Claude Code e querem **estrutura** sem virar burocracia.
- Times que precisam de **rastreabilidade AC × validação** (todo critério de aceitação amarrado a teste ou validação manual explícita).
- Projetos onde a spec é primeira-classe — **escrita antes** de qualquer commit, validada com stakeholder se necessário, versionada quando muda no meio do trabalho.
- Quem quer um framework **agnóstico ao stack** (TS/JS/Ruby/Python/Go/Java/C# detectados via regex unificada; agnóstico ao projeto via templates neutros).

## Princípios

1. **Spec é gate**, não rascunho. Spec rejeitada não polui repo com branch órfã.
2. **WHAT separado de HOW.** Spec descreve comportamento e ACs; plan descreve arquitetura, arquivos, passos.
3. **Mudança de escopo é evento de primeira-classe.** `update-spec` versiona a spec, gera changelog, propaga drift pro `implement` via freshness check.
4. **Default seguro, opt-out consciente.** Peer-review em subagent isolado por padrão; quem quer economia decide explicitamente.
5. **Trabalho determinístico vai pra script Python.** Parsing de comentários, lint estrutural, geração de tabelas — economia agressiva de tokens vs LLM fazendo manualmente.
6. **Falha de otimização nunca interrompe o processo.** Cada caminho otimizado tem fallback LLM funcional.

## Instalação

```
1. No projeto: invoque a skill "god"
2. Use "install" — vai perguntar onde guardar specs (specs_path),
   criar GOD/ com templates, detectar python3/git/gh/MCPs.
3. Preencha GOD/patterns.md com as convenções do seu projeto.
4. (Opcional v10) Ative principles.md / architecture.md / domains/ se
   quiser advisor arquitetural ou regras de negócio rastreáveis.
5. Rode "doctor" pra verificar setup — diagnóstico ASCII completo.
```

**Pré-requisitos opcionais:**
- `python3 ≥ 3.8` — habilita scripts otimizados em `sub-skills/_lib/` (economia significativa de tokens). Sem ele, fluxo cai pro caminho LLM com aviso.
- `git` — fluxo de pack-up depende.
- `gh` (GitHub CLI) — pack-up cria PR via `gh pr create`. Sem isso, criação manual.
- MCP Atlassian (Jira) — `spec` busca task automaticamente; `init-tree` percorre árvore Jira.
- MCP Figma — `spec` analisa design pra cenários e edge cases visuais.

## Ciclo de vida (v9 spec-first)

```
install → spec → [publish-spec] → init → plan → implement → pack-up
            ↑                              ↑       ↑           ↑
         review                         review  review      review
         (spec)                         (plan) (update)  (execution)
```

| Etapa | O que faz |
|-------|-----------|
| **install** | Setup uma vez por projeto. Cria `GOD/` com VERSION, config.md, knowledge.md, patterns.md, learned-patterns.md, hooks.md. |
| **spec** | **Entry point do fluxo.** Aceita input (Jira/Figma/texto livre), detecta perfil da task (trivial/normal/critical), faz Q&A focada nos gaps detectados, escreve spec canônica em `<specs_path>/tasks/{cod}.md`. |
| **publish-spec** *(opcional, sugerido em perfil critical)* | Publica spec em Jira/Slack/stdout pra validação externa antes do init. |
| **init** | Cria estrutura de execução em `GOD/tasks/{cod}/` (status.md + plan.md vazio). Aceita `--type=trivial` que pula spec pra mudanças cosméticas. |
| **plan** | Lê a spec pronta. Resolve branch + base, detecta single/multi-project, escreve plano técnico (HOW) referenciando ACs. Lê principles/architecture (v10) e gera bloco "Considerações arquiteturais". |
| **implement** | Cria branch no git, executa o plano. **Freshness check estendido** detecta drift de spec via changelog e oferece reabrir passos. Anota `// covers: AC-X` em testes (v8) e `// rule: BR-X` em código que enforça invariantes (v10). |
| **pack-up** | Review final, commit, push, PR via `gh`. Carimba `spec_version_delivered` no PR description + tabela AC × validação + tabela BRs aplicáveis × anotadas. Link do changelog se houve mudança de escopo. |

### Variantes

- **`init-tree`** — recebe um nó-raiz do Jira (Epic/Story), desce a árvore, cria pastas de contexto pra nós internos e gera **specs rascunho em batch** pra cada folha. Você refina cada uma com `spec {cod}` interativo antes de `init`.
- **Modo trivial** — `init {cod} --type=trivial` pula spec pra cosmético (typo, copy, dep upgrade). Vai direto pra implement.
- **Multi-project workspace** — pasta-mãe sem `.git` contendo múltiplos repos. Cada task pode ter branch em N projetos; pack-up abre N PRs.

## Skills auxiliares

| Skill | Pra quê |
|-------|---------|
| **review** | Wrapper que delega pra `review-spec`/`review-plan`/`review-execution` (3 sub-skills focadas, v10.4). |
| **update-spec** | Mudança de escopo pós-init. Bumpa `spec_version`, escreve em `<specs_path>/tasks/{cod}-changelog.md`. |
| **update-plan** | Atualiza plano durante implementação quando surgem mudanças técnicas. |
| **publish-spec** | Publica/republica spec em Jira/Slack/stdout. Aceita default em `config.md` (`publish_spec_default_target`). |
| **coverage** | Matriz AC × validação. Manual ou via pack-up/review. |
| **status** | Dashboard de tasks ativas. |
| **pause** / **resume** | Pausa task com observação no changelog; retoma com contexto. |
| **learn** | Transforma task entregue em conhecimento (knowledge.md + learned-patterns.md). |
| **clean-up** | Arquiva tasks em `packed-up` cujos PRs já foram mergiados. |
| **doctor** | Diagnóstico do ambiente: python3, git, gh, MCPs, GOD/ consistência, scripts em `_lib/`, tasks ativas. |
| **upgrade** | Migra entre versões do GOD preservando dados. |
| **code-like-me** | Flag do `implement` (default ativo) — código cirúrgico que imita padrões do projeto. |

## Configuração

Tudo configurável via `GOD/config.md`. Chaves principais:

| Chave | Default | O que faz |
|-------|---------|-----------|
| `specs_path` | `docs/specs/` | Onde a spec da task mora (fora do GOD/). Pode ser repo dedicado ao lado, path absoluto, etc. |
| `publish_spec_default_target` | (vazio = stdout) | Default do `publish-spec` quando `--target` não é passado. Aceita `jira`, `slack`, `stdout`, `notion`, ou comma-separated. |
| `principles_path` *(v10)* | (vazio = desativado) | Bullets curtos de princípios duradouros do projeto. Lido pelo `plan` pra gerar "Considerações arquiteturais". |
| `architecture_path` *(v10)* | (vazio = desativado) | Padrões "preferidos mas negociáveis". Lido junto com principles. |
| `domains_path` *(v10)* | (vazio = desativado) | Pasta com `<dominio>.md` declarando BRs (regras de negócio). IDs derivados do `domain:` do frontmatter (`domain: payments` → `BR-PAYMENTS-NNN`). |
| `peer_review_default` *(v10.3)* | `subagent` | Modo de execução do review. Valores: `subagent` (fresh eyes anti-viés, default seguro), `inline` (economiza tokens, perde fresh eyes), `skip` (desativa review automático). |

## Hooks

`GOD/hooks.md` tem slots `before X` / `after X` pra cada step do fluxo principal (init, spec, plan, implement, pack-up). Default = `skip-hook`. Preencha em linguagem natural quando quiser ativar:

```
# after spec
Postar comentário no Jira da task com link da spec, contagem de REQs/ACs e
aviso "se algum critério não bate, comente aqui antes do dev começar".
```

Casos comuns: publicar spec no Jira/Slack após criar; rodar testes/linter antes do pack-up; notificar canal após PR criado.

## Trinity de rastreabilidade

GOD entrega **três camadas** de rastreabilidade verificáveis no PR:

1. **AC × validação** *(v8)* — cada `AC-NNN.N` da spec amarrado a teste (via `// covers: AC-X` em comentário) ou validação manual (em `coverage.md`). Tabela injetada no PR description automaticamente.
2. **BR × anotação** *(v10)* — cada BR declarada em `applicable_rules` da spec amarrada a comentário `// rule: BR-X` no código onde a invariante é enforced. Tabela no PR.
3. **Spec version delivered** *(v9)* — qual versão da spec foi efetivamente entregue (carimbado no PR). Se aparecer bug em produção e a spec já estiver em outra versão, é fácil ver "isso é mudança de escopo posterior, não bug".

## Otimizações de tokens (v10.2-v10.5)

GOD invoca scripts Python pra trabalho determinístico — economia significativa vs LLM fazendo parsing manualmente.

**Scripts em `sub-skills/_lib/`:**
- `parse_coverage.py` — matriz AC × validação a partir do diff.
- `parse_rules.py` — `// rule: BR-X` no diff.
- `parse_spec.py` — extrai REQs/ACs/frontmatter da spec.
- `validate_spec.py` — lint estrutural (REQ tem AC, IDs estáveis, palavras-tabu, framework leak).
- `freshness_check.py` — drift entre `spec_version` atual × `spec_version_consumed`.
- `update_status.py` — read-modify-write determinístico de YAML frontmatter.
- `gen_pr_description.py` — markdown do PR description a partir de JSON.
- `pack_up_validate.py` *(v10.5)* — orquestrador batch do pack-up: roda coverage + rules + freshness + lint numa **única chamada**, retorna JSON consolidado.

Todos: Python 3.8+ stdlib only, cross-platform (macOS, Linux, WSL), sem dependências externas.

**Falha de qualquer script → fallback LLM automático** (caminho original, mais caro mas funcional). Garantia: erro de script jamais interrompe um fluxo da skill.

## Filosofia de versões

GOD é versionado em fases (v6, v7, v8, v9, v10) que entregam capacidades semânticas, e patches transversais (v8.1, v8.2, v10.1...) que otimizam ou refinam sem mudança funcional. Detalhes em [SDD-ROADMAP.md](SDD-ROADMAP.md).

| Versão | O que entregou |
|--------|----------------|
| v6 | Spec extraída em path configurável. |
| v7 | Hooks de propagação, review semântico profundo, freshness check, `--review-feedback`, `publish-spec`. |
| v8 | Rastreabilidade AC × validação (`// covers:` + `coverage.md` + tabela no PR). |
| v8.1 | Peer-review via subagent isolado (anti-viés). |
| v8.2 | Default target do publish-spec configurável. |
| v9 | **Spec-first** (inverte ordem `init→spec` para `spec→init`) + spec viva (`update-spec` + changelog). |
| v10 | Architecture advisor + Domain rules (principles/architecture/domains opcionais e configuráveis, agnóstico ao projeto). |
| v10.1 | Spec absorve qualidades da skill global `god-spec` (heurísticas pré-Q&A, self-validação, ASCII). |
| v10.2 | Scripts Python pra processos robóticos + skill `doctor` + lazy templates + compactação. |
| v10.3 | Peer-review opt-out via config (`peer_review_default`). |
| v10.4 | Context blob (cache de leituras) + quebra de `review` em 3 sub-skills. |
| v10.5 | Batch consolidado de validação no pack-up (`pack_up_validate.py`). |

## Migração entre versões

Sempre via skill `upgrade`. Detecta versão atual, executa migrations correspondentes (`sub-skills/upgrade/migrations/v{N}-to-v{N+1}.md`), preserva todos os dados do usuário (tasks, knowledge, patterns).

Se você tem instalação antiga do `GDD` (rebatizado pra `GOD` na v3), o upgrade migra automaticamente.

## Estrutura do repo

```
GOD/                                  # framework
├── README.md                         # este arquivo
├── SDD-ROADMAP.md                    # roadmap completo das versões
├── SKILL.md                          # skill orquestradora raiz
└── sub-skills/                       # 1 pasta por sub-skill
    ├── _lib/                         # scripts Python compartilhados (v10.2+)
    │   ├── _common.py
    │   ├── parse_coverage.py
    │   ├── parse_rules.py
    │   ├── parse_spec.py
    │   ├── validate_spec.py
    │   ├── freshness_check.py
    │   ├── update_status.py
    │   ├── gen_pr_description.py
    │   └── pack_up_validate.py       # batch consolidado (v10.5)
    ├── install/
    │   ├── SKILL.md
    │   └── templates/                # templates lazy-loaded (v10.2)
    ├── spec/
    │   ├── SKILL.md
    │   └── heuristics.md             # tabelas de detectores (v10.1)
    ├── init/, init-tree/, plan/, implement/, pack-up/
    ├── update-spec/, update-plan/
    ├── review/                       # wrapper de roteamento (v10.4)
    ├── review-spec/, review-plan/, review-execution/   # focadas (v10.4)
    ├── coverage/, publish-spec/
    ├── pause/, resume/, learn/, clean-up/, status/, doctor/
    ├── code-like-me/
    └── upgrade/
        └── migrations/               # 1 arquivo por bump de versão
```

No projeto do usuário (após `install`):

```
<projeto>/
├── GOD/                              # estado das tasks (pode ir no .gitignore)
│   ├── VERSION                       # ex: v10
│   ├── config.md                     # configuração local
│   ├── knowledge.md, patterns.md, learned-patterns.md, hooks.md
│   ├── principles.md (opcional v10)
│   ├── architecture.md (opcional v10)
│   └── tasks/
│       └── PROJ-123/
│           ├── status.md
│           ├── plan.md
│           ├── coverage.md (opcional)
│           └── changelog.md
└── <specs_path>/                     # canônico, committado por todos
    ├── README.md
    ├── tasks/
    │   ├── PROJ-123.md
    │   └── PROJ-123-changelog.md     # se update-spec foi usado
    └── domains/ (opcional v10)
        └── <dominio>.md
```

## FAQ rápida

**Posso ignorar `GOD/` no `.gitignore`?**
Sim — é workflow individual. A spec (em `specs_path/`) é canônica e deve ser committada.

**Time misto (alguns com IA, outros sem)?**
Suportado. Spec/plan podem ser feitos com IA (skill GOD); código pode ser escrito manualmente seguindo a spec. Anotações `// covers:` e `// rule:` são manuais (sintaxe simples) — não exigem IA.

**Como descobrir o que dá pra fazer?**
`help` na skill orquestradora `god` mostra fluxo + skills auxiliares contextual ao estado atual.

**Algo deu errado, como diagnosticar?**
`doctor` faz auditoria completa do ambiente e da instalação. Reporta cada item ✅/⚠️/❌ com ação concreta de correção.

**Tem CI integrado?**
Não. GOD é skill local do dev. CI é responsabilidade do projeto.

**Como ver o histórico de mudanças de uma spec?**
`<specs_path>/tasks/{cod}-changelog.md` se `update-spec` foi usado. Senão, `git log` da spec.

## Contribuir

Roadmap em [SDD-ROADMAP.md](SDD-ROADMAP.md). Patches transversais bem-vindos — formato é arquivo separado, retrocompatível, sem migration quando possível.

## Licença

Defina conforme apropriado para o seu uso.

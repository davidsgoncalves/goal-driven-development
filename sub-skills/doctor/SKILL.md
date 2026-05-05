---
name: doctor
description: |
  Diagnóstico completo da instalação GOD: verifica versão, dependências (python3, git, gh, MCPs), consistência de config, integridade de tasks ativas, e scripts em sub-skills/_lib/. Reporta cada item como ✅/⚠️/❌ com ação concreta pra resolver. Skill read-only — não modifica nada. Use quando o usuário mencionar: "doctor", "god doctor", "checar god", "verificar instalação", "status do ambiente", "está tudo ok?", "diagnosticar god", "o que falta no meu setup".
tools: Read, Glob, Grep, Bash
---

# Doctor — Sub-skill de Diagnóstico

> Verifica saúde da instalação GOD e do ambiente. Não modifica nada — só diagnostica e reporta. Use quando algo está estranho, depois de um upgrade, ou pra validar antes de começar a usar GOD numa máquina nova.

## Quando usar

- Depois de `install` ou `upgrade` — confirmar que tudo está OK.
- Quando algo deu errado em outra skill — descobrir se é bug ou ambiente.
- Em onboarding (novo dev na máquina) — saber o que falta instalar.
- Periodicamente — pegar drift (ex: alguém deletou um arquivo do GOD/).

## Instruções

Quando o usuário invocar esta skill, executar as verificações **na ordem** e acumular um relatório. **Não falhar em erro de check individual** — agregar tudo no final.

### 1. Resolver `god_root`

Diretório raiz do projeto onde `GOD/` está. Default: cwd. Aceita flag `--god-root <path>`.

### 2. Bloco "Instalação GOD"

Verificações:

| Item | Como checar | Severidade se falha |
|------|-------------|---------------------|
| Pasta `GOD/` existe | `[ -d "$god_root/GOD" ]` | ❌ erro — sugerir `install` |
| `GOD/VERSION` existe e contém versão atual | ler arquivo, comparar com versão atual do framework | ⚠️ warning — sugerir `upgrade` |
| `GOD/config.md` existe | `[ -f "$god_root/GOD/config.md" ]` | ❌ erro — sugerir `install` ou `upgrade` |
| `GOD/patterns.md` existe | idem | ⚠️ warning — `install` cria template |
| `GOD/knowledge.md` existe | idem | ⚠️ warning |
| `GOD/learned-patterns.md` existe | idem | ⚠️ warning |
| `GOD/hooks.md` existe | idem | ⚠️ warning |
| `GOD/tasks/` existe | idem | ⚠️ warning |

Versão atual do framework: ler do diretório de instalação do GOD (ex: `~/.claude/skills/god/VERSION` ou similar). Se ambíguo, pegar do `SDD-ROADMAP.md` mencionado no description da skill raiz. Em última instância, hard-code a versão atual conhecida (`v10`).

### 3. Bloco "Configuração"

Ler `GOD/config.md` e validar chaves esperadas:

| Chave | Obrigatória? | Severidade se ausente |
|-------|--------------|----------------------|
| `specs_path` | sim | ❌ erro — default seria `docs/specs/`, mas usuário pode não querer |
| `publish_spec_default_target` | não | — vazio = stdout (OK) |
| `principles_path` | não (v10) | — vazio = advisor desativado |
| `architecture_path` | não (v10) | — vazio |
| `domains_path` | não (v10) | — vazio |
| `peer_review_default` | não (v10.3) | — vazio = `subagent` (default seguro) |

Pra cada path configurado e não-vazio, validar:
- O caminho resolve (relativo a `god_root` ou absoluto).
- Se aponta a arquivo: arquivo existe.
- Se aponta a pasta (`domains_path`): pasta existe.
- Severidade ⚠️ warning se path configurado mas alvo ausente.

**Pra `peer_review_default` (v10.3):**
- Valores válidos: `subagent`, `inline`, `skip`. Vazio ou ausente = `subagent`.
- ✅ se `subagent` (default seguro).
- ⚠️ warning se `inline` — informar o tradeoff: "Modo `inline` perde fresh eyes anti-viés. OK em projeto solo/pequeno; em time, considere voltar pra `subagent`."
- ⚠️ warning se `skip` — informar: "Modo `skip` desativa peer-review automático. Garante que a revisão é feita manualmente em outro lugar."
- ❌ erro se valor diferente dos 3 — config inválida.

### 4. Bloco "Repo de specs"

Se `specs_path` resolveu:
- `<specs_path>/` existe? (`mkdir -p` ainda não foi rodado?)
- `<specs_path>/tasks/` existe?
- `<specs_path>/README.md` existe?
- `<specs_path>` é git repo? (`git -C <specs_path> rev-parse --git-dir`)
- Se for git, fazer `git -C <specs_path> fetch --quiet` e checar se está sincronizado:
  - Comparar HEAD vs `@{u}` se há upstream.
  - Reportar "N commits remotos não puxados" como warning.

### 5. Bloco "Dependências de runtime"

Verificações de comandos disponíveis (`command -v <bin>`):

| Comando | Versão mínima | Como checar | Severidade se ausente |
|---------|---------------|-------------|----------------------|
| `python3` | 3.8 | `python3 --version` parsear | ⚠️ warning — scripts em `_lib/` não rodam, fluxo cai pro fallback LLM (mais caro) |
| `git` | 2.x | `git --version` | ❌ erro — fluxo do GOD depende de git |
| `gh` | qualquer | `gh --version` + `gh auth status` | ⚠️ warning — `pack-up` cria PR via gh; sem isso, criação manual |

Pra `python3 < 3.8`: warning específico ("scripts otimizados exigem 3.8+; atualize ou os processos rodarão via LLM").

### 6. Bloco "MCPs (integrações opcionais)"

Verificar disponibilidade dos MCPs comuns. Não é trivial detectar via Bash — apenas mencionar e instruir o usuário a checar via `claude mcp list` ou similar:

| MCP | Pra que serve | Severidade se ausente |
|-----|---------------|----------------------|
| Atlassian (Jira) | `spec` busca task automaticamente; `init-tree` percorre árvore | ℹ️ info — fluxo manual continua funcionando |
| Figma | `spec` analisa design pra cenários e edge cases visuais | ℹ️ info |

Listar como informativo, sem rodar checks ativos.

### 7. Bloco "Scripts em `_lib/`"

Listar arquivos em `sub-skills/_lib/` (relativo ao diretório de skills do GOD). Pra cada:
- Existe?
- É executável? (`[ -x "$f" ]`)
- Tem shebang Python? (`head -n1 | grep -q '#!.*python3'`)
- Roda sem erro? (`python3 <script> --help` retorna 0?)

Severidade ❌ se script esperado faltar (degrade graceful pro LLM, mas avisar).

Scripts esperados (v10.2 + v10.5):
- `_common.py` (utils compartilhados)
- `parse_coverage.py`
- `parse_rules.py`
- `parse_spec.py`
- `validate_spec.py`
- `freshness_check.py`
- `update_status.py`
- `gen_pr_description.py`
- `pack_up_validate.py` *(v10.5 — batch consolidado)*

### 7.5. Bloco "Sub-skills review-* (v10.4)"

Listar `sub-skills/review-spec/SKILL.md`, `review-plan/SKILL.md`, `review-execution/SKILL.md`. Severidade ❌ se faltar — `review` wrapper depende delas.

### 8. Bloco "Tasks ativas"

Varrer `GOD/tasks/*/` e validar:

| Check | Severidade se falha |
|-------|---------------------|
| Pasta tem `status.md` (a menos que seja contexto de `init-tree`) | ⚠️ warning — task corrompida |
| `status.md` é YAML válido com campos obrigatórios (`phase`, `updated_at`) | ⚠️ warning |
| Se `phase ≠ initialized`, `spec_path` populado ou perfil = trivial | ⚠️ warning |
| Se `phase ∈ {planned, implementing, ...}`, `branch` populado | ⚠️ warning |
| Spec referenciada em `spec_path` realmente existe | ⚠️ warning |

Reportar contagem por fase: "5 tasks ativas: 1 specified, 2 planned, 1 implementing, 1 packed-up".

### 9. Bloco "Specs órfãs vs tasks órfãs"

Cruzar `<specs_path>/tasks/*.md` com `GOD/tasks/*/status.md`:
- **Spec órfã**: arquivo em `<specs_path>/tasks/{cod}.md` sem `GOD/tasks/{cod}/` correspondente — provavelmente outra máquina trabalhando, ou spec do init-tree não passou por init ainda. ℹ️ informativo.
- **Task órfã**: pasta em `GOD/tasks/{cod}/` com `phase` não-trivial mas sem spec correspondente em `<specs_path>` — ⚠️ warning, sugere rodar `spec {cod}` ou checar pull do repo de specs.

### 10. Reportar

Saída ASCII com box-drawing fora de fences. Estrutura:

```
═══════════════════════════════════════════════════════════════════════════
  🩺 GOD Doctor — Diagnóstico {timestamp}
═══════════════════════════════════════════════════════════════════════════

┌─ Instalação GOD ────────────────────────────────────────────────────────
│
│  ✅ GOD/ existe (versão v10 — atual)
│  ✅ config.md, patterns.md, knowledge.md, learned-patterns.md, hooks.md
│  ✅ GOD/tasks/ (3 tasks)
│
└─────────────────────────────────────────────────────────────────────────

┌─ Configuração ──────────────────────────────────────────────────────────
│
│  ✅ specs_path: docs/specs/ (existe, é git, sincronizado)
│  ✅ publish_spec_default_target: jira
│  ⚠️ principles_path: configurado em GOD/principles.md mas arquivo não existe
│      → Crie o arquivo ou rode `install` de novo pra repopular template
│  — architecture_path: vazio (advisor desativado)
│  — domains_path: vazio (BRs desativadas)
│  ✅ peer_review_default: subagent (fresh eyes ativo)
│
└─────────────────────────────────────────────────────────────────────────

┌─ Dependências de runtime ───────────────────────────────────────────────
│
│  ✅ python3 3.11.5 (>= 3.8)
│  ✅ git 2.43.0
│  ⚠️ gh: instalado mas não autenticado
│      → Rode `gh auth login` pra `pack-up` poder criar PRs
│
└─────────────────────────────────────────────────────────────────────────

┌─ Scripts otimizados (sub-skills/_lib/) ─────────────────────────────────
│
│  ✅ parse_coverage.py (executável, --help OK)
│
└─────────────────────────────────────────────────────────────────────────

┌─ Tasks ativas ──────────────────────────────────────────────────────────
│
│  3 tasks: 1 specified, 1 planned, 1 implementing
│  ✅ Todas com status.md válido
│  ⚠️ PROJ-456: phase=planned mas branch=null
│      → Rode `plan PROJ-456` de novo pra resolver branch
│
└─────────────────────────────────────────────────────────────────────────

┌─ Specs vs tasks ────────────────────────────────────────────────────────
│
│  ✅ 3 specs em <specs_path>/tasks/, todas pareadas com tasks GOD
│  ℹ️ 2 specs órfãs (sem GOD/tasks/ correspondente)
│      • PROJ-789 (rascunho do init-tree, esperando refinamento)
│      • PROJ-790 (pode ser de outra máquina)
│
└─────────────────────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════════════════════
  Resumo: ✅ 12  ·  ⚠️ 3  ·  ❌ 0  ·  ℹ️ 1
═══════════════════════════════════════════════════════════════════════════

Próximas ações sugeridas (em ordem de prioridade):
  1. Criar GOD/principles.md (warning de config)
  2. `gh auth login` (warning de runtime)
  3. `plan PROJ-456` pra resolver branch da task pendente
```

**Regras de output:**
- Itens em ordem: instalação → config → specs → runtime → scripts → tasks → cruzamento.
- Cada bloco mostra todos os checks (mesmo os ✅), pra dev ver o que está OK.
- Resumo final agrega contagens.
- "Próximas ações" lista warnings/erros em ordem de severidade (❌ antes de ⚠️ antes de ℹ️).
- Se tudo está ✅, último bloco vira: "🎉 Tudo certo! Sem ações pendentes."

## Flags

- `--god-root <path>` — diretório raiz do projeto. Default: cwd.
- `--quiet` — só imprime warnings/erros, omite ✅. Útil pra CI ou check rápido.
- `--json` — saída JSON estruturada em vez de ASCII. Útil pra scripts consumirem.

## Guard-rails

- **Esta skill é read-only.** Não cria, edita ou deleta nada. Só diagnostica.
- **Esta skill não chama outras skills GOD.** Nem `install`, nem `upgrade`. Apenas sugere o que rodar.
- **Não falha em check individual** — todos os checks rodam, agrega no relatório final. Mesmo se `git` não existe, prossegue checando o resto.
- **Não acessa rede** exceto pra `git fetch` (sync check do `specs_path`). Tudo offline-friendly.
- **Não loga PII nem conteúdo sensível** — só metadados (paths, versões, contagens).

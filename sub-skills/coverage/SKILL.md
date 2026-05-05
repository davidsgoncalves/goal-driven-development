---
name: coverage
description: |
  Gera matriz de cobertura "AC × validação" pra uma task dentro do fluxo do GOD: parseia comentários `// covers: AC-X` em testes automatizados, lê `GOD/tasks/{cod}/coverage.md` (validações manuais), e cruza com a spec pra mostrar quais ACs estão cobertos por quê. Detecta ACs órfãos (sem nenhuma validação). Invocada pelo `pack-up` antes do PR, pelo `review --execution`, ou manualmente pelo dev. Use quando o usuário mencionar: "cobertura", "coverage", "que ACs estão testados", "matriz de cobertura", "AC sem teste".
tools: Read, Glob, Grep, Bash, Edit, Write
---

# Coverage — Sub-skill de Cobertura AC × Validação

> Gera matriz de cobertura por task: cada AC da spec aparece amarrado a uma validação (teste automatizado parseado por regex de comentário, ou validação manual registrada em `coverage.md`). Detecta ACs órfãos. Não modifica testes nem força anotação — apenas reporta. **Skill de uso interno do GOD** (executada via Claude pelo dev) — não é uma CLI standalone nem se integra com pipelines de CI.

## Quando rodar

- **Manualmente** a qualquer momento: `coverage PROJ-123` mostra estado atual
- **Automaticamente** pelo `pack-up` antes de criar o PR (resultado vai pro PR description)
- **Automaticamente** pelo `review --execution` como eixo extra

## Flags

- `--task <cod>` — código da task (se não passar, pergunta ou usa contexto da conversa)
- `--format <fmt>` — formato de saída: `markdown` (default, pronto pra PR), `terminal` (legível no shell), `json` (cache estruturado, lido pelo `review --execution`)

## Context blob (v10.4)

Esta skill aceita context blob inline da skill chamadora (pack-up, review --execution). Quando recebido, **não re-lê** os arquivos correspondentes:

- Se context contém `status` → usar direto (não ler `status.md`).
- Se context contém `spec` → usar direto. Se tem só `spec_path` → ler do disco.
- Se context contém `coverage` → usar direto. Se ausente, ler `GOD/tasks/{cod}/coverage.md` (pode não existir — OK).

Quando invocada manualmente sem context (ex: dev rodando `coverage PROJ-123` direto), comportamento original — lê tudo do disco. Retrocompat preservada.

## Caminho preferido (v10.2): delegar pro script Python

A partir da v10.2, esta skill **delega o trabalho de parsing pro script `sub-skills/_lib/parse_coverage.py`** (Python 3.8+ stdlib, sem deps externas). Economiza milhares de tokens vs parsing manual via LLM.

### Detecção e fallback

1. **Checar python3 disponível:**
   ```bash
   command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)'
   ```
   Se sucede: usar caminho do script (passos abaixo). Se falha: cair pro **fallback LLM** (passos 1-7 da seção "Caminho fallback" mais abaixo).

2. **Resolver paths do `GOD/config.md`:**
   - `specs_path` (default `docs/specs`)
   - `god_root` = diretório onde `GOD/` mora

3. **Invocar o script** via Bash:
   ```bash
   python3 sub-skills/_lib/parse_coverage.py \
     --task "$cod" \
     --specs-path "$specs_path" \
     --god-root "$god_root" \
     --source-root "$source_root" \
     --format "$format"
   ```
   - `$source_root` = diretório a varrer (single-project: pwd; multi-project: cada projeto, varrendo um por vez e mesclando JSONs)
   - `$format` = `json` (default), `markdown`, ou `terminal`

4. **Em modo `--execution` ou `--task` chamado por `pack-up`:** invocar com `--diff-against <branch_base>` pra limitar varredura aos arquivos do diff (ainda mais barato).

5. **Capturar saída.** Em `json`, parsear pra struct mental e formatar conforme requisitado pela skill chamadora. Em `markdown`/`terminal`, repassar direto.

6. **Se o script reportar `warning: Spec não encontrada`** no JSON: encerrar com mensagem "Task sem spec — coverage não aplicável." (mesmo comportamento do fallback).

### Quando NÃO usar o script (caminho fallback)

- python3 não instalado, ou versão < 3.8
- Script `_lib/parse_coverage.py` ausente (instalação corrompida — sugerir `doctor` pra diagnosticar)
- Caso muito específico onde julgamento humano é necessário (raro — script cobre 99% dos casos)

Nesses casos, seguir o **caminho fallback** abaixo. Avisar o usuário 1x: "python3 ausente; coverage rodando via LLM (mais lento e caro). Considere `brew install python3` (macOS) ou `apt install python3` (Linux/WSL)."

---

## Caminho fallback (LLM faz o parsing)

Mantido pra retrocompat e ambientes sem Python. Os passos abaixo eram o caminho default antes da v10.2.

### 0. Identificar a task

Se `--task` foi passado, usar. Senão, ler do contexto da conversa ou perguntar.

### 1. Pré-requisitos

Ler `GOD/tasks/{cod}/status.md` e extrair `spec_path`.

- Se `spec_path` é `null` ou ausente: a task não tem spec. Sem ACs pra rastrear. Encerrar com mensagem clara: "Task sem spec — coverage não aplicável."
- Se o arquivo da spec não existe: avisar e pedir confirmação.

### 2. Ler ACs da spec

Ler `<spec_path>` e extrair **todos** os ACs (formato `AC-NNN.N`):

- Parsear linhas que começam com `- AC-` ou `* AC-`
- Capturar ID e descrição curta de cada AC
- Construir lista canônica: `[(AC-001.1, "telefone vazio bloqueia"), (AC-001.2, "formato inválido bloqueia"), ...]`

### 3. Parsear validações automatizadas (testes)

Identificar arquivos de teste tocados pela task:

- Ler `GOD/tasks/{cod}/changelog.md` (lista de arquivos modificados durante o `implement`)
- Filtrar por extensão de teste (configurável; defaults: `*.test.ts`, `*.test.tsx`, `*.test.js`, `*.test.jsx`, `*_test.rb`, `*_spec.rb`, `*_test.go`, `test_*.py`, `*_test.py`, `*Test.java`, `*Tests.cs`)
- Pra cada arquivo, ler conteúdo e fazer **regex** procurando comentários no padrão:

  ```
  // covers: AC-001.1, AC-001.2
  # covers: AC-001.1
  /* covers: AC-001.1 */
  ```

  Regex unificada: `(?:\/\/|#|\/\*)\s*covers:\s*((?:AC-\d+\.\d+(?:\s*,\s*)?)+)`

- Pra cada match, registrar `(arquivo:linha, [ACs cobertos])`

**Não inferir cobertura do nome do teste.** Cobertura é só o que está explicitamente anotado. `it("rejects empty phone")` sem `// covers: AC-001.1` **não conta**.

### 4. Ler validações manuais

Verificar se `GOD/tasks/{cod}/coverage.md` existe.

- **Se não existe**: criar vazio com template (passo 4.5) — apenas pra deixar o esqueleto pronto pro usuário preencher se quiser.
- **Se existe**: parsear entradas no formato:

  ```markdown
  ## Validações manuais

  - AC-002.1: validação manual em staging por PM (data: 2026-04-30)
  - AC-002.2: visual em staging por UX
  - AC-003.1: pós-deploy log check
  ```

  Capturar tuplas `(AC, descrição da validação manual)`.

### 4.5. Template do `coverage.md` (se criado vazio)

```markdown
# Coverage — {cod-da-task}

> Validações manuais dos ACs da spec. ACs cobertos por testes automatizados são detectados
> via comentário `// covers: AC-X` no código de teste — não precisam ser registrados aqui.
>
> Use esta seção quando um AC for validado manualmente (FE sem teste E2E, validação visual,
> auditoria pós-deploy, etc.) — assim a matriz de cobertura ficar completa sem mentir.

## Validações manuais

<!-- Formato:
- AC-XXX.Y: descrição da validação manual (quem fez, quando, onde)
-->

(nenhuma validação manual registrada)
```

### 5. Cruzar dados e montar matriz

Pra cada AC da lista canônica (passo 2), determinar status:

- ✅ **Coberto por teste**: aparece em algum comentário `// covers:` parseado
- 👁 **Coberto manualmente**: aparece em `coverage.md`
- ✅👁 **Coberto por ambos**: tem teste E entrada manual (raro mas válido)
- ⚠️ **Órfão**: não aparece em lugar nenhum

Construir a matriz:

```
AC-001.1 ✅ teste: tests/phone-validator.test.ts:42
AC-001.2 ✅ teste: tests/phone-validator.test.ts:55
AC-001.3 👁 manual: validação visual em staging por PM
AC-002.1 ⚠️ órfão (sem cobertura)
AC-002.2 ✅ teste: tests/phone-validator.test.ts:78
```

### 6. Cachear resultado em `coverage.md`

Ao final, atualizar `coverage.md` adicionando/sobrescrevendo a seção `## Matriz` (depois de `## Validações manuais`):

```markdown
## Matriz (gerada automaticamente em {timestamp})

| AC | Status | Validação |
|----|--------|-----------|
| AC-001.1 | ✅ | tests/phone-validator.test.ts:42 |
| AC-001.2 | ✅ | tests/phone-validator.test.ts:55 |
| AC-001.3 | 👁 | manual: validação visual em staging por PM |
| AC-002.1 | ⚠️ | (sem cobertura) |
| AC-002.2 | ✅ | tests/phone-validator.test.ts:78 |

**Resumo:** {N} ACs total · {X} cobertos por teste · {Y} cobertos manualmente · {Z} órfãos
```

A seção `## Validações manuais` (input do usuário) **não é tocada** — só `## Matriz` é regenerada.

### 7. Reportar resultado

**Formato `--format markdown` (default — usado pelo pack-up):**

```markdown
## Cobertura de ACs

| AC | Status | Validação |
|----|--------|-----------|
| AC-001.1 | ✅ | tests/phone-validator.test.ts:42 |
...

**Resumo:** N total · X testes · Y manuais · Z órfãos
```

**Formato `--format terminal`:**

```
📊 Coverage — PROJ-123

  AC-001.1   ✅  tests/phone-validator.test.ts:42
  AC-001.2   ✅  tests/phone-validator.test.ts:55
  AC-001.3   👁   manual: validação visual em staging por PM
  AC-002.1   ⚠️   (sem cobertura)
  AC-002.2   ✅  tests/phone-validator.test.ts:78

  Resumo: 5 ACs · 3 testes · 1 manual · 1 órfão
```

**Formato `--format json`:**

```json
{
  "task": "PROJ-123",
  "spec_version": 2,
  "total": 5,
  "by_test": 3,
  "by_manual": 1,
  "orphans": 1,
  "matrix": [
    {"ac": "AC-001.1", "status": "test", "validation": "tests/phone-validator.test.ts:42"},
    {"ac": "AC-002.1", "status": "orphan", "validation": null}
  ]
}
```

---

## Guard-rails

- **Esta skill é de uso interno do GOD.** Roda via Claude na máquina do dev. Não tem versão standalone, não dá pra invocar de pipeline de CI. O dev consome o relatório no terminal ou via `pack-up`/`review`, não via automação externa.
- **Esta skill não modifica testes.** Não anota `// covers:` automaticamente — apenas parseia o que já existe. Anotação é responsabilidade do `implement` (passo novo na v8) ou manual do dev.
- **Esta skill não modifica a spec.** ACs vêm da spec; coverage só consome.
- **Esta skill é tolerante por design.** ACs órfãos viram alerta visual, nunca falha de processo. Decisão de prosseguir ou não fica do dev/revisor.
- **Esta skill não escreve em `GOD/knowledge.md` nem em `GOD/learned-patterns.md`.**
- **Cobertura é apenas o que está explicitamente anotado.** Inferir cobertura por nome de teste é proibido — leva a falsos positivos.

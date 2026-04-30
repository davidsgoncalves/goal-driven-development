---
name: review
description: |
  Revisa a qualidade do trabalho em três modos: spec (qualidade do contrato de escopo), plan (descrição+spec vs plano), execution (plano vs execução). Retorna relatórios para a skill chamadora avaliar e corrigir. Use quando o usuário mencionar: "revisar", "review", "checar qualidade", ou quando ativada automaticamente pelo GOD.
tools: Read, Glob, Grep, Bash, Edit, Write, Agent
---

# Review — Sub-skill de Revisão

> Revisa a qualidade do trabalho em três modos: `--spec` (contrato de escopo), `--plan` (descrição+spec vs plano técnico), `--execution` (plano vs execução). Retorna relatórios para a skill chamadora avaliar e corrigir.

## Execução via subagent isolado (a partir da v8.1)

Os três modos (`--spec`, `--plan`, `--execution`) executam suas verificações através de **subagent isolado** invocado pela `Agent` tool, não no contexto do agent principal. Motivo: o agent que escreveu a spec/plan/código tem viés sobre o próprio trabalho — mesma instância revisando o que escreveu costuma "validar" inconscientemente. Subagent fresh, com contexto vazio e tools restritas, dá fresh eyes de verdade.

### Como funciona em cada modo

| Modo | `subagent_type` | Tools que o subagent recebe | Por quê |
|------|-----------------|-----------------------------|---------|
| `--spec` | `Explore` | Read, Glob, Grep | Só precisa ler description e spec. Não pode editar — garantia estrutural de que reviewer só revisa |
| `--quick` (variante de `--spec`) | `Explore` | Read, Glob, Grep | Mesmo, com prompt enxuto pulando semântica profunda |
| `--plan` | `Explore` | Read, Glob, Grep | Só precisa ler description, spec, plan |
| `--execution` | `general-purpose` | Tudo | Precisa rodar `git diff` (Bash) e ler arquivos modificados; pode chamar `coverage` se necessário |

### Padrão de invocação

A skill chamadora (`spec`, `plan`, `pack-up`) ainda invoca `review --modo`. Internamente, a `review`:

1. Monta o prompt do subagent contendo:
   - Tipo de review e código da task
   - Caminhos absolutos dos arquivos a ler (não passa o conteúdo — subagent lê pra ter contexto fresco)
   - Lista de critérios de revisão correspondentes ao modo
   - Formato exato do relatório esperado
   - Regra de veredicto (Aprovado / Ajustes necessários / Reprovado) com gatilhos

2. Invoca:

```
Agent({
  subagent_type: "Explore"   // ou "general-purpose" pra --execution
  description: "Review crítico de [spec|plan|execution] da task <cod>",
  prompt: <prompt montado no passo 1>
})
```

3. Captura o texto retornado (já no formato do relatório).

4. Repassa o relatório à skill chamadora sem alteração.

### Garantias do isolamento

- O subagent **não vê** a conversa do agent principal — só o prompt recebido.
- O subagent **não pode escrever** em modos `--spec` e `--plan` (Explore é read-only). Em `--execution` pode rodar Bash mas não Edit/Write — não consegue alterar código.
- O contexto principal **não é poluído** pelo raciocínio interno do subagent (lendo arquivos, comparando, formatando) — recebe só o relatório final.
- Múltiplas reviews em paralelo são possíveis se a skill chamadora invocar 2+ modos numa única mensagem (caso raro hoje, mas suportado pela arquitetura).

### Quando NÃO usar subagent

- **Em testes/dry-run da própria skill `review`** — se o usuário invocar `review` diretamente sem skill chamadora, comportamento é igual (subagent invocado mesmo).
- **Se `Agent` tool não estiver disponível no ambiente** (caso muito improvável em Claude Code) — fallback inline, com aviso explícito ao usuário no relatório: "⚠️ Review executado no agent principal (subagent indisponível) — possível viés de auto-validação."

### Custo

Cada review consome ~1.5x–2x tokens vs execução inline (subagent lê arquivos do zero, sem cache do agent principal). Latência adicional de poucos segundos por chamada. O custo é justificado pelo ganho de qualidade — viés de auto-validação é a principal causa de "reviews que aprovam tudo".

## Modos

### Modo 1: `--spec` — Qualidade da spec

Chamada pela skill `spec` após escrever a spec da task. Aceita flag opcional `--quick` que pula as verificações semânticas (passo 5+) e roda só lint estrutural — útil quando o usuário quer iteração rápida.

**Objetivo:** Garantir que a spec é testável, consistente, completa e não vazou implementação.

**Passos:**
1. Ler `GOD/tasks/{cod-da-task}/description.md` (input bruto)
2. Ler a spec em `<spec_path>` (extraído de `GOD/tasks/{cod-da-task}/status.md`)
3. Aplicar verificações estruturais (passo 4)
4. Aplicar verificações de lint (vagueness, vazamento, contradição)
5. **Se sem flag `--quick`**: aplicar verificações semânticas profundas (cobertura, cenários, NFRs adequados, ortogonalidade, edge cases)
6. Gerar relatório

**Critérios de revisão:**

**A. Estrutura (sempre):**
- Cada REQ tem ao menos um critério de aceitação
- ACs têm IDs estáveis no formato `AC-NNN.N` (ex: `AC-001.2`)
- A spec tem todas as seções obrigatórias do template (`Objetivo`, `Requisitos`, `Cenários`, `NFRs`)
- O frontmatter contém `spec_version`, `task`, `created_at`, `updated_at`

**B. Qualidade de conteúdo / lint (sempre):**
- Nenhum AC é vago — palavras-tabu sem métrica: "rápido", "fácil", "intuitivo", "bonito", "performático"
- Nenhum REQ ou AC vaza implementação — palavras-flag: nomes de framework (React, Rails, Django, Laravel, Vue, Angular, Express, FastAPI, etc.), banco (Postgres, MySQL, Mongo), biblioteca específica (Redux, RxJS, jQuery)
- Não há contradição literal entre REQs (ex: REQ-001 diz "obrigatório" e REQ-002 diz "opcional" para o mesmo campo sem condicional)

**C. Verificações semânticas profundas (a partir da v7 — pulam com `--quick`):**

- **Cobertura description → spec (profunda):** ler a description bruta e identificar cada ponto de escopo mencionado. Para cada ponto, verificar se há um REQ ou AC que o cobre. Lacunas que o lint da v6 não pegava (ex: description menciona "admin precisa exportar" mas a spec só fala de cadastro).
- **Cenários cobrem ACs:** cada AC deveria aparecer em pelo menos um cenário (happy path, edge case ou erro). Se um AC existe mas não tem cenário, é provável que esteja "sem teste" — alertar.
- **NFRs adequados ao tipo de feature:** detectar tipo de feature pelo conteúdo dos REQs. Se REQs envolvem **transação financeira** ou **dado pessoal**, mas a seção "NFRs" não menciona auditoria, segurança ou LGPD, alertar. Se REQs envolvem **UI**, NFRs deveria mencionar acessibilidade. Heurística simples — não bloqueia, sugere.
- **ACs ortogonais:** detectar pares de ACs que dizem essencialmente a mesma coisa com palavras diferentes (ex: AC-001.2 "rejeita formato inválido" e AC-002.1 "não aceita formato inválido"). Sinaliza redundância.
- **Edge cases óbvios não documentados:** dado o tipo de campo/comportamento, há edge cases conhecidos que provavelmente faltam? Ex: cadastro de email sem AC pra "email duplicado"; cadastro de telefone sem AC pra "telefone com +55 prefixo"; pagamento sem AC pra "valor negativo / zero". Heurística — não exaustivo.

**Formato do relatório:**

```markdown
## Review: Spec — {cod-da-task} {[--quick] se aplicável}

### A. Estrutura
- [✓/✗] {check estrutural} — {detalhe se ✗}

### B. Qualidade de conteúdo (lint)
- [✓/✗] Vagueness — {AC com palavra-tabu, se houver}
- [✓/✗] Vazamento de implementação — {AC ou REQ que mencionou framework/lib/banco, se houver}
- [✓/✗] Contradições — {par de REQs/ACs em conflito, se houver}

### C. Verificações semânticas (pulado se --quick)
- [✓/⚠] Cobertura description → spec
  - {ponto da description coberto por REQ-X | NÃO coberto}
- [✓/⚠] Cenários cobrem ACs
  - {ACs sem cenário associado, se houver}
- [✓/⚠] NFRs adequados ao tipo de feature
  - {sugestão se faltar NFR previsível, ex: "feature financeira sem NFR de auditoria"}
- [✓/⚠] ACs ortogonais
  - {pares possivelmente redundantes, se houver}
- [✓/⚠] Edge cases óbvios
  - {edge cases que tipicamente apareceriam mas não estão documentados, se houver}

### Veredito
- ✅ **Aprovado** — spec está pronta pro plan
- ⚠️ **Ajustes necessários** — lista de correções sugeridas (semânticas são sugestões, não bloqueios)
- ❌ **Reprovado** — spec precisa ser reescrita (apenas se A ou B falham com gravidade)
```

**Regra de veredicto:**
- Falhas em A (estrutura) → **Reprovado** (spec não pode ir adiante).
- Falhas em B (lint) → **Ajustes necessários** se forem poucas, **Reprovado** se sistêmicas.
- Sinalizações em C (semântica) → **Ajustes necessários** com tom de sugestão. Nunca **Reprovado** — são heurísticas, podem ter falsos positivos.

---

### Modo 2: `--plan` — Descrição + Spec vs Plano

Chamada pela skill `plan` após escrever o plano de implementação.

**Objetivo:** Garantir que o plano técnico cobre todos os ACs da spec, sem excessos nem lacunas.

**Passos:**
1. Ler `GOD/tasks/{cod-da-task}/description.md` (contexto)
2. Ler a spec em `<spec_path>` (REQs e ACs)
3. Ler `GOD/tasks/{cod-da-task}/plan.md`
4. Comparar e gerar relatório

**Critérios de revisão:**
- Todos os ACs da spec estão cobertos por algum passo do plano?
- O plano inclui passos que não correspondem a nenhum AC? (scope creep — pode ser legítimo se for refator/limpeza, mas precisa ficar explícito)
- Os passos são viáveis e na ordem correta?
- Há ambiguidades ou contradições entre spec e plano?
- Se há links do Figma na spec, o plano considera os elementos visuais?
- Se há commits de referência na knowledge, o plano considerou os padrões dessas implementações anteriores?

**Formato do relatório:**

```markdown
## Review: Plano — {cod-da-task}

### Cobertura de ACs (spec → plano)
- [✓/✗] AC-001.1 — coberto no passo {N} do plano
- [✓/✗] AC-001.2 — **NÃO coberto** no plano

### Scope creep
- {passo do plano que não corresponde a nenhum AC, se houver — pode ser legítimo (refator), avaliar}

### Problemas encontrados
- {ambiguidades, contradições, passos fora de ordem, etc.}

### Veredito
- ✅ **Aprovado** — plano cobre a spec sem lacunas relevantes
- ⚠️ **Ajustes necessários** — lista de correções sugeridas
- ❌ **Reprovado** — plano precisa ser reescrito
```

---

### Modo 3: `--execution` — Plano vs Execução (+ cobertura de ACs em v8)

Chamada pela skill `pack-up` antes de finalizar.

**Objetivo:** Garantir que a implementação executou fielmente o que o plano definiu **e** que cada AC da spec está coberto por alguma forma de validação.

**Passos:**
1. Ler `GOD/tasks/{cod-da-task}/plan.md` e `GOD/tasks/{cod-da-task}/status.md` (para obter `branch`, `branch_base` e `spec_path`)
2. Analisar o diff das alterações no git (`git diff {branch_base}..{branch}`)
3. Comparar o que foi planejado com o que foi efetivamente implementado
4. **(v8)** Chamar `coverage --task {cod} --format json` e capturar a matriz de cobertura
5. Cruzar passos do plano com cobertura de ACs

**Critérios de revisão:**
- Todos os passos do plano foram executados?
- Há arquivos alterados que não estavam no plano? (mudanças não planejadas)
- Há passos do plano que não foram implementados? (trabalho incompleto)
- As alterações seguem as convenções do projeto?
- A implementação introduziu efeitos colaterais não previstos?
- **(v8)** Todos os ACs da spec têm cobertura registrada (teste ou manual)?
- **(v8)** ACs órfãos (sem cobertura) são alertados — não bloqueiam, mas viram "Ajustes necessários"

**Formato do relatório:**

```markdown
## Review: Plano vs Execução — {cod-da-task}

### Passos executados
- [x] {passo 1 do plano} — implementado em `arquivo.ts`
- [x] {passo 2 do plano} — implementado em `outro.ts`
- [ ] {passo 3 do plano} — **NÃO implementado**

### Alterações não planejadas
- {arquivo modificado que não estava no plano, se houver}

### Cobertura de ACs (v8)
- ✅ AC-001.1 — coberto por teste (tests/phone-validator.test.ts:42)
- ✅ AC-001.2 — coberto por teste
- 👁 AC-001.3 — validação manual em staging
- ⚠️ AC-002.1 — **órfão** (sem cobertura)

**Resumo:** {N} ACs · {X} testes · {Y} manuais · {Z} órfãos

### Problemas encontrados
- {efeitos colaterais, convenções quebradas, etc.}

### Veredito
- ✅ **Aprovado** — execução alinhada e cobertura completa
- ⚠️ **Ajustes necessários** — passos faltantes, alterações não planejadas, ou ACs órfãos
- ❌ **Reprovado** — implementação precisa ser revisada (passos críticos faltando ou efeitos colaterais)
```

**Regra de veredicto pra ACs órfãos:**
- ACs órfãos sozinhos → **Ajustes necessários** (sugestão), nunca **Reprovado**.
- Razão: pode ser legítimo (AC validado externamente, AC pendente de validação manual) — bloquear seria fricção desnecessária. O alerta visual no relatório é suficiente pra decisão consciente.

---

## Comportamento geral

- Esta skill **não corrige** nada. Ela apenas gera o relatório.
- A skill chamadora (`plan` ou `pack-up`) é responsável por avaliar o relatório e decidir se executa as correções sugeridas.
- Se o veredito for "Aprovado", a skill chamadora pode prosseguir sem intervenção.
- Se o veredito for "Ajustes necessários" ou "Reprovado", a skill chamadora deve apresentar o relatório ao usuário e agir conforme necessário.

---

## Guard-rails

- **Esta skill não escreve em `GOD/knowledge.md`.** Apenas a skill `learn` pode fazê-lo.
- **Esta skill não altera `status.md`.** Mudança de fase é responsabilidade da skill chamadora.

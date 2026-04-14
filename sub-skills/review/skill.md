# Review — Sub-skill de Revisão

> Revisa a qualidade do trabalho em dois modos: comparando descrição com plano, ou comparando plano com execução. Retorna relatórios para a skill chamadora avaliar e corrigir.

## Modos

### Modo 1: `--plan` — Descrição vs Plano

Chamada pela skill `plan` após escrever o plano de implementação.

**Objetivo:** Garantir que o plano cobre tudo que a descrição da task pede, sem excessos nem lacunas.

**Passos:**
1. Ler `GDD/tasks/{cod-da-task}/description.md`
2. Ler `GDD/tasks/{cod-da-task}/plan.md`
3. Comparar os dois e gerar relatório

**Critérios de revisão:**
- Todos os requisitos da descrição estão cobertos no plano?
- O plano inclui algo que não foi pedido na descrição? (scope creep)
- Os passos do plano são viáveis e na ordem correta?
- Há ambiguidades ou contradições entre descrição e plano?
- Se há links do Figma na descrição, o plano considera os elementos visuais?
- Se há commits de referência na descrição, o plano considerou os padrões dessas implementações anteriores?

**Formato do relatório:**

```markdown
## Review: Descrição vs Plano — {cod-da-task}

### Cobertura
- [ ] {requisito X} — coberto no passo Y do plano
- [ ] {requisito Z} — **NÃO coberto** no plano

### Scope creep
- {item do plano que não foi pedido na descrição, se houver}

### Problemas encontrados
- {ambiguidades, contradições, passos fora de ordem, etc.}

### Veredito
- ✅ **Aprovado** — plano está alinhado com a descrição
- ⚠️ **Ajustes necessários** — lista de correções sugeridas
- ❌ **Reprovado** — plano precisa ser reescrito
```

---

### Modo 2: `--execution` — Plano vs Execução

Chamada pela skill `pack-up` antes de finalizar.

**Objetivo:** Garantir que a implementação executou fielmente o que o plano definiu.

**Passos:**
1. Ler `GDD/tasks/{cod-da-task}/plan.md`
2. Analisar o diff das alterações no git (`git diff` do branch da task vs branch inicial)
3. Comparar o que foi planejado com o que foi efetivamente implementado

**Critérios de revisão:**
- Todos os passos do plano foram executados?
- Há arquivos alterados que não estavam no plano? (mudanças não planejadas)
- Há passos do plano que não foram implementados? (trabalho incompleto)
- As alterações seguem as convenções do projeto?
- A implementação introduziu efeitos colaterais não previstos?

**Formato do relatório:**

```markdown
## Review: Plano vs Execução — {cod-da-task}

### Passos executados
- [x] {passo 1 do plano} — implementado em `arquivo.ts`
- [x] {passo 2 do plano} — implementado em `outro.ts`
- [ ] {passo 3 do plano} — **NÃO implementado**

### Alterações não planejadas
- {arquivo modificado que não estava no plano, se houver}

### Problemas encontrados
- {efeitos colaterais, convenções quebradas, etc.}

### Veredito
- ✅ **Aprovado** — execução está alinhada com o plano
- ⚠️ **Ajustes necessários** — lista de correções sugeridas
- ❌ **Reprovado** — implementação precisa ser revisada
```

---

## Comportamento geral

- Esta skill **não corrige** nada. Ela apenas gera o relatório.
- A skill chamadora (`plan` ou `pack-up`) é responsável por avaliar o relatório e decidir se executa as correções sugeridas.
- Se o veredito for "Aprovado", a skill chamadora pode prosseguir sem intervenção.
- Se o veredito for "Ajustes necessários" ou "Reprovado", a skill chamadora deve apresentar o relatório ao usuário e agir conforme necessário.

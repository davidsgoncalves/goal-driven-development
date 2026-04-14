# Install — Sub-skill de Instalação

> Configura a arquitetura de pastas e arquivos GDD no projeto do usuário e verifica integrações MCP opcionais.

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos **na ordem**:

### 1. Criar estrutura GDD

No diretório raiz do projeto do usuário, crie a seguinte estrutura:

```
GDD/
├── knowledge.md
├── pack-up-instructions.md
└── tasks/
```

- `knowledge.md` — criado com template padrão (ver seção abaixo)
- `pack-up-instructions.md` — criado com template padrão (ver seção abaixo)
- `tasks/` — pasta vazia para armazenar tasks do projeto

### 2. Preencher template do knowledge.md

O arquivo `GDD/knowledge.md` deve ser criado com o seguinte template:

```markdown
# Knowledge — Registro de Tasks

> Registro de tasks finalizadas com referências de commit e aprendizados. Usado pelo `init` para encontrar tasks semelhantes e pelo `plan` para aproveitar decisões anteriores.

## Tasks finalizadas

<!-- Formato:
### {cod-da-task} — {breve descrição}
- **commits:** {hash1}, {hash2}, ...
- **arquivos principais:** {lista dos arquivos mais relevantes}
- **aprendizados:** {o que foi aprendido, decisões tomadas, armadilhas evitadas}
-->
```

### 3. Preencher template do pack-up-instructions.md

O arquivo `GDD/pack-up-instructions.md` deve ser criado com o seguinte template para o usuário preencher:

```markdown
# Pack up instructions

# Branch inicial
O branch inicial é [nome do branch]

# Padrão de nome de branch
Aqui descreva o padrão de branch que você quer que seja seguido
Ex: task/[cod-da-task]/[descrição da task]

# Padrão de mensagem de commit
Como você quer que a mensagem de commit seja criada

# Processos de finalização
Ex: Roda testes XYZ
Ex: Rodar linter

# Padrão de mensagem de PR
Descreva como a IA deve criar o título e o corpo do PR

# Ações finais
Criar um PR em draft sem revisores
```

Após criar, informe ao usuário que ele deve preencher este arquivo com as convenções do projeto.

### 4. Gitignore (opcional)

Pergunte ao usuário se deseja adicionar a pasta `GDD/` ao `.gitignore` do projeto.

- **Se sim:** adicione `GDD/` ao `.gitignore` existente (ou crie o arquivo se não existir)
- **Se não:** siga para o próximo passo

### 5. Verificar MCPs opcionais

Verifique se o usuário possui os seguintes MCP servers conectados:

- **Figma** (`claude.ai Figma`) — verificar se está disponível e autenticado
- **Jira/Atlassian** (`claude.ai Atlassian`) — verificar se está disponível e autenticado

### 6. Reportar resultado

**Se ambos MCPs estiverem conectados:**
> ✅ Instalação concluída! Estrutura GDD criada e integrações Figma + Jira detectadas.

**Se algum MCP estiver faltando ou desconectado:**
> ✅ Instalação concluída! Estrutura GDD criada.
>
> ⚠️ Para melhor integração, conecte os seguintes MCPs (opcional):
> - [ ] Figma — [listar se faltando]
> - [ ] Jira (Atlassian) — [listar se faltando]
>
> Esses MCPs não são obrigatórios, mas melhoram a experiência com outras skills do GDD.

# CLAUDE.md

## Google ADK: consulte o Context7 antes de implementar

Ao criar ou alterar agentes, ou qualquer funcionalidade relacionada ao Google ADK (Agent Development Kit), use o **Context7 via MCP** para buscar referências atualizadas. Não confie apenas na memória: a API do ADK muda com frequência.

Fontes de referência no Context7:

- https://context7.com/google/adk-python — documentação e API do ADK para Python
- https://context7.com/google/adk-recipes — receitas e exemplos de uso

Como usar:

1. Chame `mcp__context7__resolve-library-id` para obter o ID da biblioteca (`google/adk-python` ou `google/adk-recipes`), ou use esses IDs diretamente.
2. Chame `mcp__context7__query-docs` com uma pergunta específica (por exemplo: sub-agentes, tools, callbacks, plugins, sessions, confirmação de tools).
3. Só então escreva ou ajuste o código, seguindo os padrões encontrados.

Aplica-se a: criação de agentes e sub-agentes, tools, callbacks, plugins, sessões/estado, runners e qualquer outro uso do `google.adk`.

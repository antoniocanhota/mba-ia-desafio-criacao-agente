# CLAUDE.md

## Visão geral

Agente em Google ADK exposto por API FastAPI. Python gerenciado com `uv`.
- `agents/`: agentes ADK · `api/`: rotas, schemas, services · `db/`: banco · `dados/`: dados de entrada · `tests/`: suíte pytest

## Comandos

- Subir a API: `uv run fastapi dev`
- Setup: `cp .env.example .env` e preencher `GOOGLE_API_KEY`
- Resetar o banco com os dados em `dados/`: `uv run python -m db.reset`. Se precisar também apagar sessões: `uv run python -m db.reset --sessoes`
- Rodar testes: `uv run pytest`. Sem LLM: `uv run pytest -m "not llm"`.

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

## FastAPI: use a skill `fastapi`

Ao criar ou alterar a API (`api/`) ou seus testes (`tests/test_api.py`), invoque a skill `fastapi` **antes** de escrever o código, para seguir as boas práticas e convenções atuais (rotas, modelos Pydantic, dependências, streaming/SSE).

## Qualidade de código (lint, formatação, imports, tipos)

Ferramentas (dev dependencies, configuradas no `pyproject.toml`): **Ruff** (lint, formatação e ordenação de imports) e **ty** (checagem de tipos).

Comandos, sempre via `uv run`:

- `uv run ruff check --fix`: lint e ordenação de imports (aplica as correções automáticas).
- `uv run ruff format`: formatação.
- `uv run ty check`: checagem de tipos.

Ao criar ou alterar código Python, rode os três antes de considerar a tarefa concluída (e antes dos testes). Para só verificar, sem alterar arquivos: `uv run ruff check`, `uv run ruff format --check` e `uv run ty check`. Corrija o **código**; não desative regras nem use `# noqa`/`# type: ignore` para silenciar um problema sem avisar o usuário.

## Testes automatizados

Ao escrever ou alterar testes, siga a skill `python-testing-patterns`. Em `tests/test_api.py`, aplique também a skill `fastapi`.

**Não parametrize testes** (`@pytest.mark.parametrize`): escreva um teste explícito por caso, mesmo que fiquem parecidos. 

- Rodar: `uv run pytest` (precisa de `GOOGLE_API_KEY` no `.env`; usa o Gemini real e sobe a API com bancos temporários, sem tocar `banco.db`/`sessoes.db`). Sem LLM: `uv run pytest -m "not llm"`.

Ao implementar uma funcionalidade:

1. Escreva os testes da funcionalidade em tests/test_api.py (um teste por passo do fluxo, em sequência) e atualize o contrato da API no mesmo arquivo, se ela o alterar.
2. Rode as checagens de "Qualidade de código" (`ruff check --fix`, `ruff format`, `ty check`); todas devem passar.
3. **Rode `uv run pytest` antes de considerar a funcionalidade concluída.** A suíte inteira deve passar.
4. Se algum teste falhar, tente corrigir o **código** e rode de novo até **2 tentativas de correção**. Se continuar falhando, **pare e avise o usuário** (quais testes falharam, o erro e o que foi tentado) para ele intervir manualmente. Não enfraqueça, remova nem pule testes para fazê-los passar.

## Segurança

Nunca commitar `.env`. `banco.db` e `sessoes.db` são dados locais: não apagar nem alterar sem avisar.

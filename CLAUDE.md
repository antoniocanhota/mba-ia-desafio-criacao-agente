# CLAUDE.md

## Visão geral

Assistente virtual do Residencial Aurora: agente em Google ADK (`agents/aurora`) exposto por API FastAPI. Python gerenciado com `uv`. Instalação, `.env`, rotas e detalhes de dados estão no `README.md`.

- `agents/`: agentes ADK · `api/`: rotas, schemas, services · `db/`: banco · `dados/`: dados de entrada · `tests/`: suíte pytest

## Comandos

Instalação, `.env` e reset do banco estão no README. Resumo:

- Subir a API (dev): `uv run fastapi dev`
- ADK web: `PYTHONPATH=. uv run adk web agents --port 8001` (a 8000 é da API)
- Reset do banco: `uv run python -m db.reset` (apaga e recarrega dados locais; só com autorização). `--sessoes` apaga também conversas e confirmações pendentes.
- Testes: ver "Testes automatizados".

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

**Não parametrize testes** (`@pytest.mark.parametrize`): escreva um teste explícito por caso, mesmo que fiquem parecidos. Cada caso deve ser legível e falhar isoladamente.

- Suíte completa: `uv run pytest`. Precisa de `GOOGLE_API_KEY` no `.env`, usa o Gemini real (consome cota) e sobe a API com bancos temporários, sem tocar `banco.db`/`sessoes.db`.
- Durante a iteração: `uv run pytest -m "not llm"`. Testes que chamam o Gemini levam `@pytest.mark.llm`.

Ao implementar uma funcionalidade:

1. Escreva os testes da funcionalidade em `tests/test_api.py` (um teste por comportamento ou rota entregue) e atualize o contrato da API no mesmo arquivo, se ela o alterar. Se mudar rotas ou schemas, atualize também a seção "Sessões e conversas" do `README.md`.
2. Rode as checagens de "Qualidade de código" (`ruff check --fix`, `ruff format`, `ty check`); todas devem passar.
3. **Rode `uv run pytest` antes de considerar a funcionalidade concluída.** A suíte inteira deve passar.
4. Se algum teste falhar, tente corrigir o **código** e rode de novo, até **2 tentativas de correção**. Se continuar falhando, **pare e avise o usuário** (quais testes falharam, o erro e o que foi tentado) para ele intervir manualmente. Não enfraqueça, remova nem pule testes para fazê-los passar.

## Segurança

Nunca commitar `.env`. `banco.db` e `sessoes.db` são dados locais: não apagar nem alterar sem avisar (inclui rodar `db.reset`).

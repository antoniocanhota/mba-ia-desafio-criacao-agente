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

## FastAPI: use a skill `fastapi`

Ao criar ou alterar a API (`api/`) ou seus testes (`tests/test_api.py`), invoque a skill `fastapi` **antes** de escrever o código, para seguir as boas práticas e convenções atuais (rotas, modelos Pydantic, dependências, streaming/SSE).

## Testes automatizados

Ao escrever ou alterar testes, siga a skill `python-testing-patterns` (pytest, fixtures, markers, padrão AAA, nomes `test_<unidade>_<cenário>_<esperado>`). Em `tests/test_api.py`, aplique também a skill `fastapi` (ex.: `TestClient`, dependências, respostas da API).

**Não parametrize testes** (`@pytest.mark.parametrize`): escreva um teste explícito por caso, mesmo que fiquem parecidos. Cada passo do fluxo do avaliador e cada rota do contrato deve ser legível e falhar isoladamente.

- `tests/test_api.py`: um arquivo só, com o "Contrato da API" e, depois, um teste por passo do "Fluxo do avaliador" do `enunciado.canhota.md`, em sequência. Só há testes do que já foi implementado; cada onda acrescenta os dela. Testes que chamam o Gemini levam `@pytest.mark.llm`.
- Rodar: `uv run pytest` (precisa de `GOOGLE_API_KEY` no `.env`; usa o Gemini real e sobe a API com bancos temporários, sem tocar `banco.db`/`sessoes.db`). Sem LLM: `uv run pytest -m "not llm"`.

Ao implementar uma onda:

1. Escreva os testes dos passos do "Fluxo do avaliador" que a onda entrega (um teste por passo, na ordem do fluxo) e ajuste o contrato em `tests/test_api.py`, se a onda mexer nele.
2. **Rode `uv run pytest` antes de considerar a onda concluída.** A suíte inteira deve passar.
3. Se algum teste falhar, tente corrigir o **código** e rode de novo, no máximo **2 vezes**. Se continuar falhando, **pare e avise o usuário** (quais testes falharam, o erro e o que foi tentado) para ele intervir manualmente. Não enfraqueça, remova nem pule testes para fazê-los passar.

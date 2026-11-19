# Regra é regra: o assistente virtual do Residencial Aurora

Assistente em português para os moradores do Residencial Aurora, construído com o [Google ADK](https://google.github.io/adk-docs/) e exposto por uma API FastAPI. O assistente (`agents/aurora`) é um `Workflow` do ADK: um nó de entrada valida o apartamento da sessão, um classificador (LLM) indica o assunto e a triagem (código) encaminha ao especialista. Hoje o de visitantes está implementado; a confirmação e a gravação são feitas por nós de código. Outros assuntos recebem a resposta de que o assistente ainda não consegue ajudar. As regras do condomínio estão em `dados/regulamento.md`.

Estrutura: `agents/` (agentes ADK), `api/` (rotas, schemas e services), `db/` (banco e script de reset), `dados/` (dados iniciais) e `tests/` (suíte pytest).

## Instalar as dependências

```bash
uv sync
```

## Subindo a API

Com o `.env` preenchido (ver [Dados](#dados)) e o banco carregado (`uv run python -m db.reset`):

```bash
uv run fastapi run
```

O `fastapi run` sobe sem auto-reload, então a API só reinicia quando você a reinicia, o que é mais previsível para a entrega. Durante o desenvolvimento, `uv run fastapi dev` recarrega a API a cada alteração no código.

- Documentação (Swagger UI): http://127.0.0.1:8000/docs (a raiz `/` redireciona para ela)

## Subindo o ADK web

Por padrão o ADK web também usa a porta 8000, que já é da API. Para evitar o conflito, recomenda-se rodá-lo na 8001:

```bash
PYTHONPATH=. uv run adk web agents --port 8001
```

- Interface: http://127.0.0.1:8001/

## Dados

Copie `.env.example` para `.env` e preencha as variáveis faltantes. Valores sugeridos (caminhos relativos à raiz do projeto):

```
DB_PATH=banco.db
SESSIONS_DB_PATH=sessoes.db
APARTAMENTOS_JSON_PATH=dados/apartamentos.json
AREAS_JSON_PATH=dados/areas.json
RESERVAS_JSON_PATH=dados/reservas.json
VISITANTES_JSON_PATH=dados/visitantes.json
```

- **Apartamentos e áreas** não têm rotas na API; ficam no banco, carregados dos JSON pelo script de reset.
- **Reservas e visitantes** só podem ser listados na API (`GET /apartamentos/{apartamento}/reservas`, `GET /apartamentos/{apartamento}/visitantes`) e também ficam no banco. Reservas e visitantes têm chave estrangeira para `apartamentos` (e reservas para `areas`), e uma área só aceita uma reserva por data (índice único). As tabelas são criadas quando a API sobe, mas só são populadas pelo script de reset, então rode-o antes da primeira execução.

### Resetar o banco

O script abaixo apaga as tabelas `apartamentos`, `areas`, `reservas` e `visitantes`, recria e carrega os dados iniciais dos arquivos apontados por `APARTAMENTOS_JSON_PATH`, `AREAS_JSON_PATH`, `RESERVAS_JSON_PATH` e `VISITANTES_JSON_PATH`. Útil para voltar ao estado original depois de testar alterações pela API:

```bash
uv run python -m db.reset
```

Por padrão o reset **não** apaga as sessões (conversas e confirmações pendentes), que ficam em `SESSIONS_DB_PATH`, arquivo separado do banco de reservas e visitantes. Para apagá-las também:

```bash
uv run python -m db.reset --sessoes
```

## Sessões e conversas

- `POST /sessoes` com `{"apartamento": "101"}` cria a sessão (`201`) e grava o apartamento no state.
- `POST /sessoes/{session_id}/mensagens` com `{"texto": "..."}` devolve `resposta` e `confirmacoes_pendentes`.
- `POST /sessoes/{session_id}/confirmacoes` com `{"id": "...", "confirmado": true|false}` responde uma confirmação pendente (mesmo formato da rota de mensagens). O `id` precisa estar em `confirmacoes_pendentes` da sessão; qualquer outro, inclusive já respondido, devolve `409` sem executar nada. A decisão volta ao ADK como `FunctionResponse` de `adk_request_input` (o `RequestInput` do nó de confirmação do workflow), nunca por texto da conversa.
- `GET /sessoes/{session_id}/eventos` lista todos os eventos da sessão.
- Sessão inexistente devolve `404` nas rotas com `{session_id}`.

## Testes

```bash
uv run pytest                 # precisa de GOOGLE_API_KEY no .env; usa bancos temporários
uv run pytest -m "not llm"    # só o que não chama o Gemini
```

Os testes marcados com `llm` chamam o Gemini real e consomem cota; os demais rodam sem rede. Os testes sobem a API com bancos temporários, então `banco.db` e `sessoes.db` não são alterados.

## Qualidade de código

Antes de commitar, rode (todos via `uv`):

```bash
uv run ruff check --fix   # lint e ordenação de imports
uv run ruff format        # formatação
uv run ty check           # checagem de tipos
```

# Regra é regra: o assistente virtual do Residencial Aurora

Assistente em português para os moradores do Residencial Aurora, construído com o [Google ADK](https://google.github.io/adk-docs/) (2.2.0, versão exata fixada no `pyproject.toml`) e exposto por uma API FastAPI. Estrutura: `agents/` (agentes ADK), `api/` (rotas, schemas e services), `db/` (banco e script de restauração), `dados/` (dados iniciais) e `tests/` (suíte pytest). O README tem três partes: [Arquitetura](#arquitetura), [Garantias](#garantias) e [Como rodar](#como-rodar).

## Arquitetura

O assistente (`agents/aurora/agent.py`) é um `Workflow` do ADK: o "agente principal" é o próprio grafo, que não tem tool nenhuma e não recebe o regulamento. Ele fala com o morador, decide o caminho e entrega o trabalho a cinco agentes e a nós de código. O `App` é o mesmo no `adk web` e na API.

| Agente / nó | Responsabilidade | Como é acionado | Por quê |
|---|---|---|---|
| `entrada_node` (código) | Barra sessão sem apartamento válido e monta o histórico recente | Início de toda mensagem | O apartamento é validado antes de qualquer modelo rodar |
| `classificador` (LLM, `agents/aurora/agents/classificador`) | Diz o assunto: visitantes, reservas, regulamento, fora do escopo ou sem pedido | Aresta do workflow | Saída estruturada com `Literal`: o modelo só escolhe entre assuntos fixos, e a triagem é código |
| `visitantes` (LLM) | Lista os visitantes do apartamento (tool) e entende o pedido de autorização | Aresta do workflow, depois da triagem | Só lê e interpreta; nunca grava |
| `reservas` (LLM) | Lista reservas, consulta se uma data está livre ou ocupada (tools) e entende pedidos de reservar e cancelar | Aresta do workflow, depois da triagem | Só lê e interpreta; nunca grava |
| `regulamento` + `leitor_do_regulamento` (LLM) | Responde dúvidas do regulamento, capítulo a capítulo | O leitor é acionado por `AgentTool` dentro do especialista | O texto do capítulo fica na sessão interna do leitor e só a resposta final entra nos eventos (garantia 4) |
| Nós de código (`agents/aurora/nodes.py`) | Validam nome, data e área; cancelam, gravam, pedem a confirmação e retomam | Arestas do workflow | Toda ação que muda dado ou cobra é decidida por código, não pelo que o modelo escreve |

Por que um workflow e não um agente com sub-agentes e tools de escrita: o modelo nunca tem uma tool que grave. Ele devolve uma intenção estruturada (`acao`, `area`, `data`), e o código valida e executa. Isso deixa a confirmação, o apartamento e a exclusividade fora do alcance do prompt. As leituras (`listar_visitantes`, `listar_reservas`, `consultar_disponibilidade`, `consultar_regulamento`) são tools em `agents/aurora/tools/`; as gravações (autorizar visitante, reservar, cancelar) são feitas pelos nós de código, que chamam as mesmas funções de `db/repo/`.

Fluxo de uma mensagem: `entrada_node` → `classificador` → triagem → especialista → nó de triagem do especialista → (se for cobrança ou acesso) nó que pausa pedindo confirmação → rota de confirmações → nó que grava. Autorizar visitante e reservar área com taxa maior que zero ficam pendentes; cancelar a própria reserva e reservar área sem taxa gravam direto.

## Garantias

**1. Cobrança ou acesso só com confirmação.**
- `agents/aurora/nodes.py`, `pedir_confirmacao_visitante_node` e `pedir_confirmacao_reserva_node`: terminam em `yield RequestInput(...)`, que pausa o workflow e cria a pendência (`adk_request_input`) com `acao` e `detalhes` no `payload`. Os nós que gravam, `autorizar_visitante_node` e `gravar_reserva_confirmada_node`, só existem depois dessa pausa e só gravam com `node_input.get("confirmed") is True`.
- `api/routers/sessoes.py`, `responder_confirmacao`: devolve `409` se o `id` não estiver entre as pendências da sessão, que `api/services/sessoes.py::confirmacoes_pendentes` calcula dos eventos (chamadas sem resposta). Um `id` já respondido deixa de ser pendente.
- Não depende do modelo: o texto "já estou confirmando aqui" é só uma mensagem; a única forma de retomar é o `FunctionResponse` montado por `decisao_de_confirmacao`. Cada pedido fica no state indexado pelo `id` da pendência, então aprovar grava exatamente o que foi mostrado.

**2. Cada sessão pertence a um apartamento.**
- `api/routers/sessoes.py`, `criar_sessao`: grava `state["apartamento"]` uma única vez.
- `agents/aurora/tools/sessao.py::apartamento_da_sessao` lê do state, e nenhuma tool tem parâmetro de apartamento (`agents/aurora/tools/*.py`). `agents/aurora/nodes.py::_apartamento` faz o mesmo nos nós de código e ainda confere o apartamento no banco.
- `db/repo/reservas.py`: `data_livre` devolve só livre ou ocupada, e `cancelar` filtra por apartamento e devolve `False` para reserva de outro, sem confirmar que ela existe. Não depende do modelo: o apartamento que o morador diga ser o dele nunca chega a uma função de gravação ou de leitura.

**3. Nada se perde no reinício.**
- `api/main.py`, `lifespan`: `SqliteSessionService(SESSIONS_DB_PATH)` guarda as sessões em arquivo (`sessoes.db`), separado de `banco.db`, onde ficam reservas e visitantes.
- As pendências vêm dos eventos gravados e os pedidos pendentes ficam no state da sessão, então aprovar depois do reinício funciona. O script de restauração só apaga as sessões com `--sessoes`.

**4. O regulamento é consultado, não carregado.**
- `agents/aurora/tools/regulamento_tools.py`: divide `dados/regulamento.md` por capítulo; `consultar_regulamento` devolve só o capítulo pedido.
- `agents/aurora/agents/regulamento/agent.py`: o `leitor_do_regulamento` roda via `AgentTool`, com sessão interna própria, e só recebe o índice de títulos nas instruções. O texto do capítulo não entra nos eventos da sessão do morador, só a resposta final. Nenhum outro agente recebe o regulamento.

**5. Dois moradores, uma reserva.**
- `db/models/reserva.py`: índice único parcial `ux_reservas_area_data_ativa` em `(area, data) WHERE ativa = 1`, criado junto com a tabela.
- `db/repo/reservas.py::reservar`: grava e converte o `IntegrityError` em `DataIndisponivel`, que `agents/aurora/nodes.py::_gravar_reserva` transforma em recusa normal (a conferência `data_livre` antes é só para responder melhor). O banco decide quem chegou primeiro, no instante da gravação. Cancelar é `ativa = 0` (soft delete), então o código da reserva nunca é reaproveitado.

Os testes automatizados em `tests/test_api.py` existem para garantir as cinco garantias, seguindo o fluxo do avaliador passo a passo.

## Como rodar

**Pré-requisitos:** [uv](https://docs.astral.sh/uv/) (instala o Python 3.12 pedido em `.python-version`) e uma chave de API do Gemini ([Google AI Studio](https://aistudio.google.com/)). Não há serviço externo: tudo usa SQLite em arquivo.

```bash
cp .env.example .env     # preencha GOOGLE_API_KEY
uv sync
uv run python -m db.reset    # restaura apartamentos, áreas, reservas e visitantes
uv run fastapi run           # API em http://localhost:8000
```

Variáveis do `.env` (caminhos relativos à raiz do projeto):

```
GOOGLE_API_KEY=            # chave do Gemini
DB_PATH=banco.db
SESSIONS_DB_PATH=sessoes.db
APARTAMENTOS_JSON_PATH=dados/apartamentos.json
AREAS_JSON_PATH=dados/areas.json
RESERVAS_JSON_PATH=dados/reservas.json
VISITANTES_JSON_PATH=dados/visitantes.json
```

- **Subida:** `uv run fastapi run` (sem auto-reload, mais previsível). Em desenvolvimento, `uv run fastapi dev` recarrega a cada alteração. Documentação em http://127.0.0.1:8000/docs.
- **Restauração dos dados:** `uv run python -m db.reset` apaga e recarrega `apartamentos`, `areas`, `reservas` e `visitantes` a partir de `dados/`. Não apaga as sessões; para apagar também as conversas e as confirmações pendentes, use `uv run python -m db.reset --sessoes`.
- **ADK web (desenvolvimento):** `PYTHONPATH=. uv run adk web agents --port 8001` (a 8000 é da API). Interface em http://127.0.0.1:8001/. As sessões de teste precisam do state com o apartamento (`POST /apps/aurora/users/<user>/sessions` com `{"state": {"apartamento": "101"}}`).
- **Rotas de verificação:** `GET /apartamentos/{apartamento}/reservas` e `GET /apartamentos/{apartamento}/visitantes`. Reservas e visitantes só são gravados pelo assistente.
- **Testes:** `uv run pytest` roda a suíte inteira (precisa de `GOOGLE_API_KEY`, usa o Gemini real e consome cota); `uv run pytest -m "not llm"` roda só o que não chama o Gemini. Os testes sobem a API com bancos temporários, então `banco.db` e `sessoes.db` não são alterados.

"""Lógica de sessões sobre o ADK: busca, confirmações pendentes e execução do Runner."""

from google.adk import Runner
from google.adk.events import Event
from google.adk.sessions import Session
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from google.genai import types

from ..schemas.sessao import ConfirmacaoPendente, MensagemResposta

REQUEST_CONFIRMATION = "adk_request_confirmation"


async def buscar_sessao(
    session_service: SqliteSessionService, runner: Runner, session_id: str
) -> Session | None:
    """Acha a sessão só pelo id, já com os eventos; None se não existe.

    O ADK indexa a sessão por (app, user_id, id) e o contrato da API só traz o id.
    O user_id (o apartamento) é descoberto aqui, nunca recebido do cliente.
    """
    sessoes = await session_service.list_sessions(app_name=runner.app_name)
    for sessao in sessoes.sessions:
        if sessao.id == session_id:
            return await session_service.get_session(
                app_name=runner.app_name,
                user_id=sessao.user_id,
                session_id=session_id,
            )
    return None


def confirmacoes_pendentes(eventos: list[Event]) -> list[ConfirmacaoPendente]:
    """Chamadas `adk_request_confirmation` ainda sem `FunctionResponse` com o mesmo id.

    Vem só dos eventos, então sobrevive ao reinício da API.
    """
    pendentes: dict[str, ConfirmacaoPendente] = {}
    for evento in eventos:
        for chamada in evento.get_function_calls():
            if chamada.name == REQUEST_CONFIRMATION and chamada.id:
                original = (chamada.args or {}).get("originalFunctionCall", {})
                pendentes[chamada.id] = ConfirmacaoPendente(
                    id=chamada.id,
                    acao=original.get("name", ""),
                    detalhes=original.get("args") or {},
                )
        for resposta in evento.get_function_responses():
            if resposta.name == REQUEST_CONFIRMATION and resposta.id:
                pendentes.pop(resposta.id, None)
    return list(pendentes.values())


def invocation_id_da_pendencia(eventos: list[Event], id_confirmacao: str) -> str | None:
    """invocation_id do evento que pediu a confirmação (usado na retomada, se houver)."""
    for evento in eventos:
        for chamada in evento.get_function_calls():
            if chamada.name == REQUEST_CONFIRMATION and chamada.id == id_confirmacao:
                return evento.invocation_id
    return None


def mensagem_do_usuario(texto: str) -> types.Content:
    return types.Content(role="user", parts=[types.Part(text=texto)])


def decisao_de_confirmacao(id_confirmacao: str, confirmado: bool) -> types.Content:
    """A decisão vai ao ADK como FunctionResponse; nada do que o morador escreve a substitui."""
    return types.Content(
        role="user",
        parts=[
            types.Part(
                function_response=types.FunctionResponse(
                    id=id_confirmacao,
                    name=REQUEST_CONFIRMATION,
                    response={"confirmed": confirmado},
                )
            )
        ],
    )


async def executar(
    session_service: SqliteSessionService,
    runner: Runner,
    sessao: Session,
    mensagem: types.Content,
    invocation_id: str | None = None,
) -> MensagemResposta:
    textos: list[str] = []
    async for evento in runner.run_async(
        user_id=sessao.user_id,
        session_id=sessao.id,
        new_message=mensagem,
        invocation_id=invocation_id,
    ):
        if evento.is_final_response() and evento.content and evento.content.parts:
            textos.extend(p.text for p in evento.content.parts if p.text)

    # os eventos da rodada só estão gravados depois do run_async
    atualizada = await buscar_sessao(session_service, runner, sessao.id)
    pendentes = confirmacoes_pendentes(atualizada.events) if atualizada else []
    return MensagemResposta(resposta="\n".join(textos), confirmacoes_pendentes=pendentes)

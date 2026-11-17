from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from google.adk import Runner
from google.adk.events import Event
from google.adk.sessions import Session
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from google.genai import types

from ..schemas.sessao import (
    ConfirmacaoPendente,
    MensagemEntrada,
    MensagemResposta,
    SessaoEntrada,
    SessaoResposta,
)

router = APIRouter(prefix="/sessoes", tags=["sessoes"])

REQUEST_CONFIRMATION = "adk_request_confirmation"


def get_runner(request: Request) -> Runner:
    return request.app.state.runner


def get_session_service(request: Request) -> SqliteSessionService:
    return request.app.state.session_service


RunnerDep = Annotated[Runner, Depends(get_runner)]
SessionServiceDep = Annotated[SqliteSessionService, Depends(get_session_service)]


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


def _confirmacoes_pendentes(eventos: list[Event]) -> list[ConfirmacaoPendente]:
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


def _nao_encontrada() -> HTTPException:
    return HTTPException(status_code=404, detail="Sessão não encontrada.")


@router.post("", status_code=201)
async def criar_sessao(
    entrada: SessaoEntrada, runner: RunnerDep, session_service: SessionServiceDep
) -> SessaoResposta:
    sessao = await session_service.create_session(
        app_name=runner.app_name,
        user_id=entrada.apartamento,
        state={"apartamento": entrada.apartamento},
    )
    return SessaoResposta(session_id=sessao.id)


@router.post("/{session_id}/mensagens")
async def enviar_mensagem(
    session_id: str,
    entrada: MensagemEntrada,
    runner: RunnerDep,
    session_service: SessionServiceDep,
) -> MensagemResposta:
    sessao = await buscar_sessao(session_service, runner, session_id)
    if sessao is None:
        raise _nao_encontrada()

    mensagem = types.Content(role="user", parts=[types.Part(text=entrada.texto)])
    textos: list[str] = []
    async for evento in runner.run_async(
        user_id=sessao.user_id, session_id=sessao.id, new_message=mensagem
    ):
        if evento.is_final_response() and evento.content and evento.content.parts:
            textos.extend(p.text for p in evento.content.parts if p.text)

    # os eventos da rodada só estão gravados depois do run_async
    atualizada = await buscar_sessao(session_service, runner, session_id)
    pendentes = _confirmacoes_pendentes(atualizada.events) if atualizada else []
    return MensagemResposta(resposta="\n".join(textos), confirmacoes_pendentes=pendentes)


@router.get("/{session_id}/eventos")
async def listar_eventos(
    session_id: str, runner: RunnerDep, session_service: SessionServiceDep
) -> list[dict[str, Any]]:
    sessao = await buscar_sessao(session_service, runner, session_id)
    if sessao is None:
        raise _nao_encontrada()
    return [e.model_dump(mode="json", exclude_none=True) for e in sessao.events]

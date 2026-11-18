from typing import Any

from fastapi import APIRouter, HTTPException

from ..dependencies import RunnerDep, SessionServiceDep
from ..schemas.sessao import (
    ConfirmacaoEntrada,
    MensagemEntrada,
    MensagemResposta,
    SessaoEntrada,
    SessaoResposta,
)
from ..services import sessoes as servico

router = APIRouter(prefix="/sessoes", tags=["sessoes"])


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
    sessao = await servico.buscar_sessao(session_service, runner, session_id)
    if sessao is None:
        raise _nao_encontrada()

    return await servico.executar(
        session_service, runner, sessao, servico.mensagem_do_usuario(entrada.texto)
    )


@router.post("/{session_id}/confirmacoes")
async def responder_confirmacao(
    session_id: str,
    entrada: ConfirmacaoEntrada,
    runner: RunnerDep,
    session_service: SessionServiceDep,
) -> MensagemResposta:
    sessao = await servico.buscar_sessao(session_service, runner, session_id)
    if sessao is None:
        raise _nao_encontrada()

    # só vale confirmação pendente nesta sessão; id desconhecido ou já respondido é 409
    if entrada.id not in {p.id for p in servico.confirmacoes_pendentes(sessao.events)}:
        raise HTTPException(
            status_code=409, detail="Não há confirmação pendente com esse id."
        )

    return await servico.executar(
        session_service,
        runner,
        sessao,
        servico.decisao_de_confirmacao(entrada.id, entrada.confirmado),
        invocation_id=servico.invocation_id_da_pendencia(sessao.events, entrada.id),
    )


@router.get("/{session_id}/eventos")
async def listar_eventos(
    session_id: str, runner: RunnerDep, session_service: SessionServiceDep
) -> list[dict[str, Any]]:
    sessao = await servico.buscar_sessao(session_service, runner, session_id)
    if sessao is None:
        raise _nao_encontrada()
    return [e.model_dump(mode="json", exclude_none=True) for e in sessao.events]

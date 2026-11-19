from typing import Any

from fastapi import APIRouter, HTTPException

from ..dependencies import RunnerDep, SessaoDep, SessionServiceDep
from ..schemas.sessao import (
    ConfirmacaoEntrada,
    ErroResposta,
    MensagemEntrada,
    MensagemResposta,
    SessaoEntrada,
    SessaoResposta,
)
from ..services import sessoes as servico

router = APIRouter(prefix="/sessoes", tags=["sessoes"])

NAO_ENCONTRADA: dict[int | str, dict[str, Any]] = {
    404: {"model": ErroResposta, "description": "Sessão não encontrada."}
}
SEM_PENDENCIA: dict[int | str, dict[str, Any]] = {
    409: {
        "model": ErroResposta,
        "description": "Não há confirmação pendente com esse id (inexistente ou já respondida).",
    }
}


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


@router.post("/{session_id}/mensagens", responses=NAO_ENCONTRADA)
async def enviar_mensagem(
    sessao: SessaoDep,
    entrada: MensagemEntrada,
    runner: RunnerDep,
    session_service: SessionServiceDep,
) -> MensagemResposta:
    return await servico.executar(
        session_service, runner, sessao, servico.mensagem_do_usuario(entrada.texto)
    )


@router.post("/{session_id}/confirmacoes", responses={**NAO_ENCONTRADA, **SEM_PENDENCIA})
async def responder_confirmacao(
    sessao: SessaoDep,
    entrada: ConfirmacaoEntrada,
    runner: RunnerDep,
    session_service: SessionServiceDep,
) -> MensagemResposta:
    # só vale confirmação pendente nesta sessão; id desconhecido ou já respondido é 409
    if entrada.id not in {p.id for p in servico.confirmacoes_pendentes(sessao.events)}:
        raise HTTPException(status_code=409, detail="Não há confirmação pendente com esse id.")

    return await servico.executar(
        session_service,
        runner,
        sessao,
        servico.decisao_de_confirmacao(entrada.id, entrada.confirmado),
    )


@router.get("/{session_id}/eventos", responses=NAO_ENCONTRADA)
async def listar_eventos(sessao: SessaoDep) -> list[dict[str, Any]]:
    return [e.model_dump(mode="json", exclude_none=True) for e in sessao.events]

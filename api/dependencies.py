"""Dependências compartilhadas pelos routers (aliases `Annotated` reutilizáveis)."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request
from google.adk import Runner
from google.adk.sessions import Session as SessaoAdk
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from sqlalchemy.orm import Session

from db.database import get_session
from .services import sessoes as servico


def get_runner(request: Request) -> Runner:
    return request.app.state.runner


def get_session_service(request: Request) -> SqliteSessionService:
    return request.app.state.session_service


async def get_sessao(
    session_id: str,
    runner: Annotated[Runner, Depends(get_runner)],
    session_service: Annotated[SqliteSessionService, Depends(get_session_service)],
) -> SessaoAdk:
    """Sessão do ADK (com eventos) pelo `session_id` da rota; 404 se não existe."""
    sessao = await servico.buscar_sessao(session_service, runner, session_id)
    if sessao is None:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    return sessao


SessionDep = Annotated[Session, Depends(get_session)]
RunnerDep = Annotated[Runner, Depends(get_runner)]
SessionServiceDep = Annotated[SqliteSessionService, Depends(get_session_service)]
SessaoDep = Annotated[SessaoAdk, Depends(get_sessao)]

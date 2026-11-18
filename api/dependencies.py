"""Dependências compartilhadas pelos routers (aliases `Annotated` reutilizáveis)."""

from typing import Annotated

from fastapi import Depends, Request
from google.adk import Runner
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from sqlalchemy.orm import Session

from db.database import get_session


def get_runner(request: Request) -> Runner:
    return request.app.state.runner


def get_session_service(request: Request) -> SqliteSessionService:
    return request.app.state.session_service


SessionDep = Annotated[Session, Depends(get_session)]
RunnerDep = Annotated[Runner, Depends(get_runner)]
SessionServiceDep = Annotated[SqliteSessionService, Depends(get_session_service)]

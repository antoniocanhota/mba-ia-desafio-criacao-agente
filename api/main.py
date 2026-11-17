import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from google.adk import Runner
from google.adk.sessions.sqlite_session_service import SqliteSessionService

from agents.aurora.agent import app as aurora_app
from db.database import criar_tabelas
from .routers.apartamentos import router as apartamentos_router
from .routers.areas import router as areas_router
from .routers.reservas import router as reservas_router
from .routers.sessoes import router as sessoes_router
from .routers.visitantes import router as visitantes_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    criar_tabelas()
    # mesmo App do adk web; sessões em arquivo próprio, separado do banco de reservas
    app.state.session_service = SqliteSessionService(os.environ["SESSIONS_DB_PATH"])
    app.state.runner = Runner(
        app=aurora_app, session_service=app.state.session_service
    )
    yield


app = FastAPI(docs_url="/", lifespan=lifespan)

app.include_router(apartamentos_router)
app.include_router(areas_router)
app.include_router(reservas_router)
app.include_router(visitantes_router)
app.include_router(sessoes_router)

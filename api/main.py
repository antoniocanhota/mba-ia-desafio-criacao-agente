from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from db.database import criar_tabelas
from .routers.apartamentos import router as apartamentos_router
from .routers.areas import router as areas_router
from .routers.reservas import router as reservas_router
from .routers.visitantes import router as visitantes_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    criar_tabelas()
    yield


app = FastAPI(docs_url="/", lifespan=lifespan)

app.include_router(apartamentos_router)
app.include_router(areas_router)
app.include_router(reservas_router)
app.include_router(visitantes_router)

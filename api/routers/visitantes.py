from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_session
from ..models import Visitante
from ..schemas import VisitanteResposta

router = APIRouter(prefix="/apartamentos/{apartamento}/visitantes", tags=["visitantes"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("")
def listar_visitantes(apartamento: str, session: SessionDep) -> list[VisitanteResposta]:
    visitantes = session.scalars(
        select(Visitante)
        .where(Visitante.apartamento == apartamento)
        .order_by(Visitante.data, Visitante.id)
    )
    return [VisitanteResposta.model_validate(v) for v in visitantes]

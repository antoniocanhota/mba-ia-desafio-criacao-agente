from fastapi import APIRouter
from sqlalchemy import select

from db.models import Visitante
from ..dependencies import SessionDep
from ..schemas import VisitanteResposta

router = APIRouter(prefix="/apartamentos/{apartamento}/visitantes", tags=["visitantes"])


@router.get("")
def listar_visitantes(apartamento: str, session: SessionDep) -> list[VisitanteResposta]:
    visitantes = session.scalars(
        select(Visitante)
        .where(Visitante.apartamento == apartamento)
        .order_by(Visitante.data, Visitante.id)
    )
    return [VisitanteResposta.model_validate(v) for v in visitantes]

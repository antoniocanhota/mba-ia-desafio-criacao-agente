from collections.abc import Sequence

from fastapi import APIRouter
from sqlalchemy import select

from db.models import Visitante
from ..dependencies import SessionDep
from ..schemas import VisitanteResposta

router = APIRouter(prefix="/apartamentos/{apartamento}/visitantes", tags=["visitantes"])


@router.get("", response_model=list[VisitanteResposta])
def listar_visitantes(apartamento: str, session: SessionDep) -> Sequence[Visitante]:
    return (
        session.scalars(
            select(Visitante)
            .where(Visitante.apartamento == apartamento)
            .order_by(Visitante.data, Visitante.id)
        )
        .all()
    )

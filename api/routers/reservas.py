from collections.abc import Sequence

from fastapi import APIRouter
from sqlalchemy import select

from db.models import Reserva
from ..dependencies import ApartamentoPath, SessionDep
from ..schemas import ReservaResposta

router = APIRouter(prefix="/apartamentos/{apartamento}/reservas", tags=["reservas"])


@router.get("", response_model=list[ReservaResposta])
def listar_reservas(
    apartamento: ApartamentoPath, session: SessionDep
) -> Sequence[Reserva]:
    return (
        session.scalars(
            select(Reserva)
            .where(Reserva.apartamento == apartamento, Reserva.ativa)
            .order_by(Reserva.data, Reserva.codigo)
        )
        .all()
    )

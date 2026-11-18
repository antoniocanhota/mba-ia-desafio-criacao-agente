from fastapi import APIRouter
from sqlalchemy import select

from db.models import Reserva
from ..dependencies import SessionDep
from ..schemas import ReservaResposta

router = APIRouter(prefix="/apartamentos/{apartamento}/reservas", tags=["reservas"])


@router.get("")
def listar_reservas(apartamento: str, session: SessionDep) -> list[ReservaResposta]:
    reservas = session.scalars(
        select(Reserva)
        .where(Reserva.apartamento == apartamento, Reserva.ativa)
        .order_by(Reserva.data, Reserva.codigo)
    )
    return [ReservaResposta.model_validate(r) for r in reservas]

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_session
from ..models import Reserva
from ..schemas import ReservaResposta

router = APIRouter(prefix="/apartamentos/{apartamento}/reservas", tags=["reservas"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("")
def listar_reservas(apartamento: str, session: SessionDep) -> list[ReservaResposta]:
    reservas = session.scalars(
        select(Reserva)
        .where(Reserva.apartamento == apartamento, Reserva.ativa)
        .order_by(Reserva.data, Reserva.codigo)
    )
    return [ReservaResposta.model_validate(r) for r in reservas]

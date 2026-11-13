from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.database import get_session
from db.models import Apartamento
from ..schemas import ApartamentoResposta

router = APIRouter(prefix="/apartamentos", tags=["apartamentos"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("")
def listar_apartamentos(session: SessionDep) -> list[ApartamentoResposta]:
    apartamentos = session.scalars(select(Apartamento).order_by(Apartamento.numero))
    return [ApartamentoResposta.model_validate(a) for a in apartamentos]

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_session
from ..models import Area
from ..schemas import AreaResposta

router = APIRouter(prefix="/areas", tags=["areas"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("")
def listar_areas(session: SessionDep) -> list[AreaResposta]:
    areas = session.scalars(select(Area).order_by(Area.id))
    return [AreaResposta.model_validate(a) for a in areas]

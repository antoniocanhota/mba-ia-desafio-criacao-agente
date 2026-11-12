from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import gerar_codigo, get_session
from ..models import Visitante
from ..schemas import VisitanteEntrada, VisitanteResposta

router = APIRouter(prefix="/apartamentos/{apartamento}/visitantes", tags=["visitantes"])

SessionDep = Annotated[Session, Depends(get_session)]


def buscar(session: Session, apartamento: str, id: str) -> Visitante:
    visitante = session.scalar(
        select(Visitante).where(Visitante.id == id, Visitante.apartamento == apartamento)
    )
    if visitante is None:
        raise HTTPException(404, "Visitante não encontrado")
    return visitante


@router.get("")
def listar_visitantes(apartamento: str, session: SessionDep) -> list[VisitanteResposta]:
    visitantes = session.scalars(
        select(Visitante)
        .where(Visitante.apartamento == apartamento)
        .order_by(Visitante.data, Visitante.id)
    )
    return [VisitanteResposta.model_validate(v) for v in visitantes]


@router.get("/{id}")
def obter_visitante(apartamento: str, id: str, session: SessionDep) -> VisitanteResposta:
    return VisitanteResposta.model_validate(buscar(session, apartamento, id))


@router.post("", status_code=status.HTTP_201_CREATED)
def criar_visitante(
    apartamento: str, dados: VisitanteEntrada, session: SessionDep
) -> VisitanteResposta:
    visitante = Visitante(
        id=gerar_codigo(session, Visitante.id, "VIS"),
        apartamento=apartamento,
        **dados.model_dump(),
    )
    session.add(visitante)
    session.commit()
    return VisitanteResposta.model_validate(visitante)


@router.put("/{id}")
def atualizar_visitante(
    apartamento: str, id: str, dados: VisitanteEntrada, session: SessionDep
) -> VisitanteResposta:
    visitante = buscar(session, apartamento, id)
    visitante.nome = dados.nome
    visitante.data = dados.data
    session.commit()
    return VisitanteResposta.model_validate(visitante)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_visitante(apartamento: str, id: str, session: SessionDep) -> Response:
    session.delete(buscar(session, apartamento, id))
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

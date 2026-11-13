from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_session, inserir_com_codigo
from ..models import Reserva
from ..schemas import ReservaEntrada, ReservaResposta

router = APIRouter(prefix="/apartamentos/{apartamento}/reservas", tags=["reservas"])

SessionDep = Annotated[Session, Depends(get_session)]


def buscar(session: Session, apartamento: str, codigo: str) -> Reserva:
    reserva = session.scalar(
        select(Reserva).where(
            Reserva.codigo == codigo,
            Reserva.apartamento == apartamento,
            Reserva.ativa,
        )
    )
    if reserva is None:
        raise HTTPException(404, "Reserva não encontrada")
    return reserva


@router.get("")
def listar_reservas(apartamento: str, session: SessionDep) -> list[ReservaResposta]:
    reservas = session.scalars(
        select(Reserva)
        .where(Reserva.apartamento == apartamento, Reserva.ativa)
        .order_by(Reserva.data, Reserva.codigo)
    )
    return [ReservaResposta.model_validate(r) for r in reservas]


@router.get("/{codigo}")
def obter_reserva(apartamento: str, codigo: str, session: SessionDep) -> ReservaResposta:
    return ReservaResposta.model_validate(buscar(session, apartamento, codigo))


@router.post("", status_code=status.HTTP_201_CREATED)
def criar_reserva(
    apartamento: str, dados: ReservaEntrada, session: SessionDep
) -> ReservaResposta:
    reserva = inserir_com_codigo(
        session,
        Reserva.codigo,
        "RSV",
        lambda codigo: Reserva(codigo=codigo, apartamento=apartamento, **dados.model_dump()),
    )
    return ReservaResposta.model_validate(reserva)


@router.put("/{codigo}")
def atualizar_reserva(
    apartamento: str, codigo: str, dados: ReservaEntrada, session: SessionDep
) -> ReservaResposta:
    reserva = buscar(session, apartamento, codigo)
    reserva.area = dados.area
    reserva.data = dados.data
    session.commit()
    return ReservaResposta.model_validate(reserva)


@router.delete("/{codigo}", status_code=status.HTTP_204_NO_CONTENT)
def remover_reserva(apartamento: str, codigo: str, session: SessionDep) -> Response:
    # não apaga a linha: o código de uma reserva cancelada nunca pode ser reutilizado
    buscar(session, apartamento, codigo).ativa = False
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

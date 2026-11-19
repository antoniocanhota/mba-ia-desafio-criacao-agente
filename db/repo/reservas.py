from datetime import date
from typing import cast

from sqlalchemy import CursorResult, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.database import inserir_com_codigo
from db.models import Area, Reserva
from db.repo.visitantes import DadosInvalidos


class DataIndisponivel(DadosInvalidos):
    """A área já tem reserva ativa na data. Não identifica quem reservou."""


def listar_reservas(session: Session, apartamento: str) -> list[Reserva]:
    return list(
        session.scalars(
            select(Reserva)
            .where(Reserva.apartamento == apartamento, Reserva.ativa)
            .order_by(Reserva.data, Reserva.codigo)
        )
    )


def buscar_area(session: Session, area: str) -> Area:
    """Área pelo id; a mensagem do erro pode ir ao morador."""
    encontrada = session.get(Area, area.strip())
    if encontrada is None:
        raise DadosInvalidos("Área não encontrada. Use salão de festas, churrasqueira ou quadra.")
    return encontrada


def validar_data(data: str) -> date:
    try:
        return date.fromisoformat(data)
    except ValueError:
        raise DadosInvalidos("Data inválida. Use o formato AAAA-MM-DD.") from None


def data_livre(session: Session, area: str, dia: date) -> bool:
    """Só livre ou ocupada: nunca devolve de quem é a reserva."""
    ocupada = session.scalar(
        select(Reserva.codigo).where(Reserva.area == area, Reserva.data == dia, Reserva.ativa)
    )
    return ocupada is None


def reservar(session: Session, apartamento: str, area: str, dia: date) -> Reserva:
    """Grava a reserva. A exclusividade vale na gravação, pelo índice único parcial
    (area, data) WHERE ativa = 1: se outra reserva entrou entre a conferência e aqui,
    o banco recusa e vira `DataIndisponivel`."""
    try:
        return inserir_com_codigo(
            session,
            Reserva.codigo,
            "RSV",
            lambda codigo: Reserva(codigo=codigo, apartamento=apartamento, area=area, data=dia),
        )
    except IntegrityError:
        raise DataIndisponivel("Data indisponível.") from None


def cancelar(session: Session, apartamento: str, area: str, dia: date) -> bool:
    """Cancela (soft delete, para o código nunca ser reaproveitado) só reserva ativa do
    próprio apartamento. False quando não há; não revela reserva de outro apartamento."""
    resultado = session.execute(
        update(Reserva)
        .where(
            Reserva.apartamento == apartamento,
            Reserva.area == area,
            Reserva.data == dia,
            Reserva.ativa,
        )
        .values(ativa=False)
    )
    session.commit()
    return cast(CursorResult, resultado).rowcount > 0

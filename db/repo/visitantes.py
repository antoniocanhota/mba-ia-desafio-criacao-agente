from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.database import inserir_com_codigo
from db.models import Visitante


class DadosInvalidos(ValueError):
    """Entrada recusada; a mensagem pode ser mostrada ao morador."""


def listar_visitantes(session: Session, apartamento: str) -> list[Visitante]:
    return list(
        session.scalars(
            select(Visitante)
            .where(Visitante.apartamento == apartamento)
            .order_by(Visitante.data, Visitante.nome)
        )
    )


def validar_visita(nome: str, data: str) -> tuple[str, date]:
    """Nome e data (AAAA-MM-DD) válidos; a mensagem do erro pode ir ao morador."""
    nome = nome.strip()
    if not nome:
        raise DadosInvalidos("Informe o nome do visitante.")
    try:
        dia = date.fromisoformat(data)
    except ValueError:
        raise DadosInvalidos("Data inválida. Use o formato AAAA-MM-DD.") from None
    return nome, dia


def autorizar_visitante(session: Session, apartamento: str, nome: str, data: str) -> Visitante:
    nome, dia = validar_visita(nome, data)
    return inserir_com_codigo(
        session,
        Visitante.id,
        "VIS",
        lambda codigo: Visitante(id=codigo, apartamento=apartamento, nome=nome, data=dia),
    )

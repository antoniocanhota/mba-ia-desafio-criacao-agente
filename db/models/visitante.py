import hashlib
from datetime import date

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


def hash_visita(apartamento: str, nome: str, data: date) -> str:
    """Identidade da autorização: sha256 de apartamento, nome (sem caixa) e data."""
    chave = f"{apartamento}|{nome.strip().casefold()}|{data.isoformat()}"
    return hashlib.sha256(chave.encode()).hexdigest()


class Visitante(Base):
    __tablename__ = "visitantes"

    hash: Mapped[str] = mapped_column(primary_key=True)
    apartamento: Mapped[str] = mapped_column(ForeignKey("apartamentos.numero"))
    nome: Mapped[str]
    data: Mapped[date]

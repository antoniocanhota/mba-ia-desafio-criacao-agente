from datetime import date

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Visitante(Base):
    __tablename__ = "visitantes"

    id: Mapped[str] = mapped_column(primary_key=True)
    apartamento: Mapped[str] = mapped_column(ForeignKey("apartamentos.numero"))
    nome: Mapped[str]
    data: Mapped[date]

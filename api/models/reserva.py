from datetime import date

from sqlalchemy import ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Reserva(Base):
    __tablename__ = "reservas"
    __table_args__ = (
        # uma área só aceita uma reserva ativa por data; canceladas não ocupam a vaga
        Index(
            "ux_reservas_area_data_ativa",
            "area",
            "data",
            unique=True,
            sqlite_where=text("ativa = 1"),
        ),
    )

    codigo: Mapped[str] = mapped_column(primary_key=True)
    apartamento: Mapped[str] = mapped_column(ForeignKey("apartamentos.numero"))
    area: Mapped[str] = mapped_column(ForeignKey("areas.id"))
    data: Mapped[date]
    ativa: Mapped[bool] = mapped_column(default=True)

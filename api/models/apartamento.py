from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Apartamento(Base):
    __tablename__ = "apartamentos"

    numero: Mapped[str] = mapped_column(primary_key=True)
    morador: Mapped[str]

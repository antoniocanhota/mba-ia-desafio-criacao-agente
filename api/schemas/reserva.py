from datetime import date

from pydantic import BaseModel, ConfigDict


class ReservaEntrada(BaseModel):
    area: str
    data: date


class ReservaResposta(ReservaEntrada):
    model_config = ConfigDict(from_attributes=True)

    codigo: str

from datetime import date

from pydantic import BaseModel, ConfigDict


class VisitanteEntrada(BaseModel):
    nome: str
    data: date


class VisitanteResposta(VisitanteEntrada):
    model_config = ConfigDict(from_attributes=True)

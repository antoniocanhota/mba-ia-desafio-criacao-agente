from datetime import date

from pydantic import BaseModel, ConfigDict


class VisitanteResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nome: str
    data: date

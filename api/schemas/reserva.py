from datetime import date

from pydantic import BaseModel, ConfigDict


class ReservaResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo: str
    area: str
    data: date

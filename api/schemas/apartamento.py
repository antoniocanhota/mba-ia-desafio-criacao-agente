from pydantic import BaseModel, ConfigDict


class ApartamentoResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    numero: str
    morador: str

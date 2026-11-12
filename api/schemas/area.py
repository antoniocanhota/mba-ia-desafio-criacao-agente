from pydantic import BaseModel, ConfigDict


class AreaResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nome: str
    taxa: float

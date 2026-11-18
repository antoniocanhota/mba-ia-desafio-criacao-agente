from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SessaoEntrada(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    apartamento: str = Field(min_length=1)


class SessaoResposta(BaseModel):
    session_id: str


class MensagemEntrada(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    texto: str = Field(min_length=1)


class ConfirmacaoEntrada(BaseModel):
    id: str
    confirmado: bool


class ConfirmacaoPendente(BaseModel):
    id: str
    acao: str
    detalhes: dict[str, Any]


class MensagemResposta(BaseModel):
    resposta: str
    confirmacoes_pendentes: list[ConfirmacaoPendente]


class ErroResposta(BaseModel):
    detail: str

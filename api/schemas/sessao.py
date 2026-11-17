from typing import Any

from pydantic import BaseModel


class SessaoEntrada(BaseModel):
    apartamento: str


class SessaoResposta(BaseModel):
    session_id: str


class MensagemEntrada(BaseModel):
    texto: str


class ConfirmacaoPendente(BaseModel):
    id: str
    acao: str
    detalhes: dict[str, Any]


class MensagemResposta(BaseModel):
    resposta: str
    confirmacoes_pendentes: list[ConfirmacaoPendente]

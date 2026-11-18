"""Schemas de entrada e saída da API (Pydantic)."""

from .reserva import ReservaEntrada, ReservaResposta
from .sessao import (
    ConfirmacaoPendente,
    ErroResposta,
    MensagemEntrada,
    MensagemResposta,
    SessaoEntrada,
    SessaoResposta,
)
from .visitante import VisitanteEntrada, VisitanteResposta

__all__ = [
    "ConfirmacaoPendente",
    "ErroResposta",
    "MensagemEntrada",
    "MensagemResposta",
    "ReservaEntrada",
    "ReservaResposta",
    "SessaoEntrada",
    "SessaoResposta",
    "VisitanteEntrada",
    "VisitanteResposta",
]

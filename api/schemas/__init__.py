"""Schemas de entrada e saída da API (Pydantic)."""

from .reserva import ReservaResposta
from .sessao import (
    ConfirmacaoPendente,
    ErroResposta,
    MensagemEntrada,
    MensagemResposta,
    SessaoEntrada,
    SessaoResposta,
)
from .visitante import VisitanteResposta

__all__ = [
    "ConfirmacaoPendente",
    "ErroResposta",
    "MensagemEntrada",
    "MensagemResposta",
    "ReservaResposta",
    "SessaoEntrada",
    "SessaoResposta",
    "VisitanteResposta",
]

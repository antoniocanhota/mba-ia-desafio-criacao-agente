"""Schemas de entrada e saída da API (Pydantic)."""

from .apartamento import ApartamentoResposta
from .area import AreaResposta
from .reserva import ReservaEntrada, ReservaResposta
from .sessao import (
    ConfirmacaoPendente,
    MensagemEntrada,
    MensagemResposta,
    SessaoEntrada,
    SessaoResposta,
)
from .visitante import VisitanteEntrada, VisitanteResposta

__all__ = [
    "ApartamentoResposta",
    "AreaResposta",
    "ConfirmacaoPendente",
    "MensagemEntrada",
    "MensagemResposta",
    "ReservaEntrada",
    "ReservaResposta",
    "SessaoEntrada",
    "SessaoResposta",
    "VisitanteEntrada",
    "VisitanteResposta",
]

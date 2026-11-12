"""Schemas de entrada e saída da API (Pydantic)."""

from .apartamento import ApartamentoResposta
from .area import AreaResposta
from .reserva import ReservaEntrada, ReservaResposta
from .visitante import VisitanteEntrada, VisitanteResposta

__all__ = [
    "ApartamentoResposta",
    "AreaResposta",
    "ReservaEntrada",
    "ReservaResposta",
    "VisitanteEntrada",
    "VisitanteResposta",
]

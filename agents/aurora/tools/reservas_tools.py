from google.adk.tools import ToolContext

from agents.aurora.tools.sessao import SEM_APARTAMENTO, apartamento_da_sessao
from db.database import SessionLocal
from db.repo import reservas
from db.repo.visitantes import DadosInvalidos


def listar_reservas(tool_context: ToolContext) -> dict:
    """Lista as reservas ativas do apartamento do morador."""
    apartamento = apartamento_da_sessao(tool_context)
    if apartamento is None:
        return SEM_APARTAMENTO
    with SessionLocal() as session:
        lista = reservas.listar_reservas(session, apartamento)
    return {
        "status": "ok",
        "reservas": [{"area": r.area, "data": r.data.isoformat()} for r in lista],
    }


def consultar_disponibilidade(area: str, data: str, tool_context: ToolContext) -> dict:
    """Informa se a área está livre ou ocupada na data (AAAA-MM-DD).

    Args:
        area: id da área (salao-de-festas, churrasqueira ou quadra).
        data: data no formato AAAA-MM-DD.
    """
    if apartamento_da_sessao(tool_context) is None:
        return SEM_APARTAMENTO
    try:
        with SessionLocal() as session:
            area_encontrada = reservas.buscar_area(session, area)
            livre = reservas.data_livre(session, area_encontrada.id, reservas.validar_data(data))
    except DadosInvalidos as erro:
        return {"status": "erro", "mensagem": str(erro)}
    return {"status": "ok", "disponibilidade": "livre" if livre else "ocupada"}

from google.adk.tools import ToolContext

from agents.aurora.tools.sessao import SEM_APARTAMENTO, apartamento_da_sessao
from db.database import SessionLocal
from db.repo import visitantes


def listar_visitantes(tool_context: ToolContext) -> dict:
    """Lista os visitantes autorizados do apartamento do morador."""
    apartamento = apartamento_da_sessao(tool_context)
    if apartamento is None:
        return SEM_APARTAMENTO
    with SessionLocal() as session:
        lista = visitantes.listar_visitantes(session, apartamento)
    return {
        "status": "ok",
        "visitantes": [{"nome": v.nome, "data": v.data.isoformat()} for v in lista],
    }

from google.adk.tools import ToolContext

from db.database import SessionLocal
from db.repo import visitantes

SEM_APARTAMENTO = {
    "status": "erro",
    "mensagem": "Não foi possível identificar o apartamento da sessão.",
}


def _apartamento(tool_context: ToolContext) -> str | None:
    return tool_context.state.get("apartamento") or None


def listar_visitantes(tool_context: ToolContext) -> dict:
    """Lista os visitantes autorizados do apartamento do morador."""
    apartamento = _apartamento(tool_context)
    if apartamento is None:
        return SEM_APARTAMENTO
    with SessionLocal() as session:
        lista = visitantes.listar_visitantes(session, apartamento)
    return {
        "status": "ok",
        "visitantes": [{"nome": v.nome, "data": v.data.isoformat()} for v in lista],
    }

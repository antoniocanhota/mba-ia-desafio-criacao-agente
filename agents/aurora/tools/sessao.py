from google.adk.tools import ToolContext

SEM_APARTAMENTO = {
    "status": "erro",
    "mensagem": "Não foi possível identificar o apartamento da sessão.",
}


def apartamento_da_sessao(tool_context: ToolContext) -> str | None:
    """O apartamento vem sempre do state da sessão, nunca de argumento do modelo."""
    return tool_context.state.get("apartamento") or None

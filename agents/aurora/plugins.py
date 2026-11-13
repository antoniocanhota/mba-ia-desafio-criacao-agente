from google.adk.agents import BaseAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.plugins import BasePlugin
from google.genai import types

from db.database import SessionLocal
from db.repo.apartamentos import apartamento_existe

MENSAGEM_APARTAMENTO_INVALIDO = "Apartamento não informado ou inválido."


class ExigirApartamento(BasePlugin):
    """Barra qualquer agente, antes do modelo, se a sessão não tem um apartamento válido.

    O apartamento só pode vir do state da sessão; o modelo nunca o pergunta ao morador.
    Usa before_agent_callback porque o before_run_callback não interrompe a execução no
    ADK 2.2.0, e roda para todo agente, inclusive o que recebe as mensagens após uma
    transferência.
    """

    def __init__(self) -> None:
        super().__init__(name="exigir_apartamento")

    async def before_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ) -> types.Content | None:
        apartamento = callback_context.state.get("apartamento")
        if apartamento:
            with SessionLocal() as session:
                if apartamento_existe(session, str(apartamento)):
                    return None
        return types.Content(
            role="model", parts=[types.Part(text=MENSAGEM_APARTAMENTO_INVALIDO)]
        )


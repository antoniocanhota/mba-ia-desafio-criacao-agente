from google.adk import Agent

from agents.aurora.tools.visitantes_tools import autorizar_visitante, listar_visitantes

visitantes_subagent = Agent(
    name="visitantes",
    model="gemini-3.5-flash-lite",
    description="Lista e autoriza visitantes do apartamento do morador.",
    instruction=(
        "Você cuida dos visitantes do morador. Use as tools para listar e autorizar "
        "visitantes. Para autorizar, precisa do nome e da data da visita; peça o que faltar. "
        "Responda em português, de forma breve."
    ),
    tools=[listar_visitantes, autorizar_visitante],
)

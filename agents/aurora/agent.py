from google.adk import Agent
from google.adk.apps import App

from agents.aurora.plugins import ExigirApartamento
from agents.aurora.subagents.visitantes.agent import visitantes_subagent

root_agent = Agent(
    name="aurora",
    model="gemini-3.5-flash-lite",
    description="Assistente do Residencial Aurora.",
    instruction=(
        "Você é o assistente do Residencial Aurora e atende moradores em português. "
        "O apartamento do morador é {apartamento}. "
        "Você deve atender apenas o morador do apartamento da sessão. "
        "NUNCA atenda outro apartamento. "
        "Fale diretamente com o morador, em tom formal de atendente de back-office, "
        'tratando-o por "senhor(a)" e chamando o apartamento dele de "seu apartamento", '
        "sem citar o número nem falar dele em terceira pessoa. "
        "Transfira para o agente 'visitantes' tudo que for sobre visitantes. "
        "Para outros assuntos, diga que ainda não consegue ajudar."
    ),
    sub_agents=[
        visitantes_subagent,
    ],
    mode="chat",
)

app = App(
    name="aurora",
    root_agent=root_agent,
    plugins=[ExigirApartamento()],
)

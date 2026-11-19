from google.adk import Workflow
from google.adk.apps import App
from google.adk.workflow import START

from agents.aurora.agents.classificador.agent import classificador_agent
from agents.aurora.agents.reservas.agent import reservas_agent
from agents.aurora.agents.visitantes.agent import visitantes_agent
from agents.aurora.nodes import (
    autorizar_visitante_node,
    entrada_node,
    gravar_reserva_confirmada_node,
    pedir_confirmacao_reserva_node,
    pedir_confirmacao_visitante_node,
    recusar_solicitacao_node,
    sem_pedido_node,
    triagem_da_solicitacao_node,
    triagem_reserva_node,
    triagem_visitante_node,
)

root_agent = Workflow(
    name="aurora",
    description="Agente responsável por atender os moradores do Residencial Aurora.",
    edges=[
        (START, entrada_node, {"classificar": classificador_agent}),
        (
            classificador_agent,
            triagem_da_solicitacao_node,
            {
                "recusar": recusar_solicitacao_node,
                "sem_pedido": sem_pedido_node,
                "visitantes": visitantes_agent,
                "reservas": reservas_agent,
            },
        ),
        (
            visitantes_agent,
            triagem_visitante_node,
            {"confirmar": pedir_confirmacao_visitante_node},
        ),
        (pedir_confirmacao_visitante_node, autorizar_visitante_node),
        (
            reservas_agent,
            triagem_reserva_node,
            {"confirmar": pedir_confirmacao_reserva_node},
        ),
        (pedir_confirmacao_reserva_node, gravar_reserva_confirmada_node),
    ],
)

app = App(name="aurora", root_agent=root_agent)

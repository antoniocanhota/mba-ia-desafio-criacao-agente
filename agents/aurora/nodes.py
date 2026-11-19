"""Nós de código do workflow: as regras críticas moram aqui, não no prompt."""

import uuid
from collections.abc import AsyncGenerator
from datetime import date
from typing import Any

from google.adk import Context, Event
from google.adk.events import EventActions, RequestInput
from google.adk.workflow import node
from google.genai import types
from pydantic import BaseModel

from agents.aurora.agents.classificador.agent import ClassificadorOutput
from agents.aurora.agents.reservas.agent import ReservasOutput
from agents.aurora.agents.visitantes.agent import VisitantesOutput
from db.database import SessionLocal
from db.repo import reservas, visitantes
from db.repo.apartamentos import apartamento_existe

APARTAMENTO_INVALIDO = "Apartamento não informado ou inválido."
FORA_DO_ESCOPO = (
    "Senhor(a), por enquanto só consigo ajudar com os visitantes e as reservas de seu apartamento."
)
SEM_PEDIDO = (
    "Olá, senhor(a). Em que posso ajudar? No momento atendo pedidos sobre os visitantes "
    "de seu apartamento (consultar os autorizados ou autorizar uma entrada) e sobre as "
    "reservas (salão de festas, churrasqueira e quadra)."
)
NEGADA = "Senhor(a), a autorização não foi feita e nada foi alterado."
# janela do histórico que os agentes recebem (mensagens do morador + respostas)
MENSAGENS_NO_HISTORICO = 10
CONVERSA = "temp:conversa"  # `temp:` não é persistido nem aparece nos eventos
MENSAGEM = "temp:mensagem"
# pedidos aguardando confirmação, por id da pendência (persistido: sobrevive à retomada)
PEDIDOS_DE_VISITA = "pedidos_de_visita"
PEDIDOS_DE_RESERVA = "pedidos_de_reserva"
RESPOSTA_DA_CONFIRMACAO = {
    "type": "object",
    "properties": {"confirmed": {"type": "boolean"}},
    "required": ["confirmed"],
}


class PedidoDeVisita(BaseModel):
    """Autorização já validada pelo código, aguardando a confirmação do morador."""

    id: str
    nome: str
    data: str


class PedidoDeReserva(BaseModel):
    """Reserva com cobrança já validada pelo código, aguardando a confirmação."""

    id: str
    area: str
    nome_da_area: str
    data: str
    taxa: float


def _resposta(texto: str) -> Event:
    """Resposta final ao morador."""
    return Event(content=types.Content(role="model", parts=[types.Part(text=texto)]))


def _texto(evento: Event) -> str:
    if evento.content and evento.content.parts:
        return "".join(p.text or "" for p in evento.content.parts).strip()
    return ""


def _apartamento(ctx: Context) -> str | None:
    """Apartamento da sessão, se existir no banco. Nunca vem do modelo."""
    apartamento = ctx.state.get("apartamento")
    if not apartamento:
        return None
    with SessionLocal() as session:
        return str(apartamento) if apartamento_existe(session, str(apartamento)) else None


@node
async def entrada_node(ctx: Context) -> Event:
    """Barra sessão sem apartamento válido e monta o histórico para os agentes.

    Cada mensagem reentra no workflow pelo START e os nós LLM só recebem a mensagem
    atual, então o histórico é montado aqui: textos do morador e respostas do workflow.
    """
    if _apartamento(ctx) is None:
        return _resposta(APARTAMENTO_INVALIDO)

    *anteriores, atual = ctx.session.events
    linhas = []
    for evento in anteriores:
        texto = _texto(evento)
        if not texto:
            continue
        if evento.author == "user":
            linhas.append(f"Morador: {texto}")
        elif evento.author == ctx.session.app_name:
            linhas.append(f"Assistente: {texto}")
    mensagem = _texto(atual)
    ctx.state[CONVERSA] = "\n".join(linhas[-MENSAGENS_NO_HISTORICO:]) or "(início da conversa)"
    ctx.state[MENSAGEM] = mensagem
    return Event(actions=EventActions(route="classificar"), output=mensagem)


@node
async def triagem_da_solicitacao_node(ctx: Context, node_input: ClassificadorOutput) -> Event:
    """Pedido fora do escopo é recusado e mensagem sem pedido recebe uma orientação;
    o resto vai ao especialista, com a mensagem atual."""
    if node_input.assunto == "fora_do_escopo":
        return Event(actions=EventActions(route="recusar"))
    if node_input.assunto == "sem_pedido":
        return Event(actions=EventActions(route="sem_pedido"))
    return Event(actions=EventActions(route=node_input.assunto), output=ctx.state.get(MENSAGEM))


@node
async def recusar_solicitacao_node() -> Event:
    return _resposta(FORA_DO_ESCOPO)


@node
async def sem_pedido_node() -> Event:
    """Saudação, agradecimento ou texto sem nexo: orienta o que o assistente faz."""
    return _resposta(SEM_PEDIDO)


@node
async def triagem_visitante_node(node_input: VisitantesOutput) -> Event:
    """Valida nome e data em código; autorizar visitante sempre exige confirmação."""
    if node_input.acao != "autorizar" or not node_input.nome or not node_input.data:
        return _resposta(node_input.mensagem)
    try:
        nome, dia = visitantes.validar_visita(node_input.nome, node_input.data)
    except visitantes.DadosInvalidos as erro:
        return _resposta(f"Senhor(a), não foi possível autorizar: {erro}")
    pedido = PedidoDeVisita(id=str(uuid.uuid4()), nome=nome, data=dia.isoformat())
    return Event(actions=EventActions(route="confirmar"), output=pedido)


@node
async def pedir_confirmacao_visitante_node(
    ctx: Context, node_input: PedidoDeVisita
) -> AsyncGenerator[Any, None]:
    """PAUSA o grafo até a rota de confirmações responder.

    O pedido fica no state indexado pelo id da pendência: com duas pendências abertas
    na mesma sessão, aprovar uma grava exatamente o que foi mostrado nela.
    """
    pedidos = dict(ctx.state.get(PEDIDOS_DE_VISITA) or {})
    pedidos[node_input.id] = {"nome": node_input.nome, "data": node_input.data}
    ctx.state[PEDIDOS_DE_VISITA] = pedidos

    pergunta = (
        f"Senhor(a), confirma a autorização de entrada de {node_input.nome} em {node_input.data}?"
    )
    yield _resposta(pergunta)  # texto da `resposta` da API enquanto a pendência existe
    yield RequestInput(
        interrupt_id=node_input.id,
        message=pergunta,
        payload={
            "acao": "autorizar_visitante",
            "detalhes": {"nome": node_input.nome, "data": node_input.data},
        },
        response_schema=RESPOSTA_DA_CONFIRMACAO,
    )


def _id_da_confirmacao(ctx: Context) -> str | None:
    """Id da pendência respondida: a retomada chega como a última mensagem da sessão."""
    respostas = ctx.session.events[-1].get_function_responses()
    return respostas[0].id if respostas else None


@node
async def autorizar_visitante_node(ctx: Context, node_input: dict) -> Event:
    """Recebe a resposta da confirmação; só `confirmed` true grava."""
    pedidos = dict(ctx.state.get(PEDIDOS_DE_VISITA) or {})
    pedido = pedidos.pop(_id_da_confirmacao(ctx) or "", None)
    ctx.state[PEDIDOS_DE_VISITA] = pedidos  # a pendência respondida sai do state

    if pedido is None:
        return _resposta("Senhor(a), não encontrei o pedido desta confirmação.")
    if node_input.get("confirmed") is not True:
        return _resposta(NEGADA)
    apartamento = _apartamento(ctx)
    if apartamento is None:
        return _resposta(APARTAMENTO_INVALIDO)
    try:
        with SessionLocal() as session:
            visitante = visitantes.autorizar_visitante(
                session, apartamento, pedido["nome"], pedido["data"]
            )
    except visitantes.DadosInvalidos as erro:
        return _resposta(f"Senhor(a), não foi possível autorizar: {erro}")
    return _resposta(
        f"Senhor(a), a entrada de {visitante.nome} foi autorizada para "
        f"{visitante.data.isoformat()}."
    )


def _gravar_reserva(apartamento: str, area: str, dia: date) -> Event:
    """Grava a reserva; data tomada (inclusive por corrida) é recusa normal."""
    try:
        with SessionLocal() as session:
            reserva = reservas.reservar(session, apartamento, area, dia)
    except reservas.DataIndisponivel:
        return _resposta(f"Senhor(a), a data {dia.isoformat()} não está disponível nessa área.")
    return _resposta(
        f"Senhor(a), a reserva {reserva.codigo} foi feita para {reserva.data.isoformat()}."
    )


@node
async def triagem_reserva_node(ctx: Context, node_input: ReservasOutput) -> Event:
    """Valida em código e executa o que não precisa de confirmação.

    Cancelar a própria reserva e reservar área sem taxa gravam direto. Área com taxa
    (cobrança) sempre vai para a confirmação. O apartamento vem do state, nunca do modelo.
    """
    if node_input.acao == "responder" or not node_input.area or not node_input.data:
        return _resposta(node_input.mensagem)
    apartamento = _apartamento(ctx)
    if apartamento is None:
        return _resposta(APARTAMENTO_INVALIDO)
    try:
        with SessionLocal() as session:
            area = reservas.buscar_area(session, node_input.area)
            dia = reservas.validar_data(node_input.data)
            if node_input.acao == "cancelar":
                cancelada = reservas.cancelar(session, apartamento, area.id, dia)
                livre = True
            else:
                cancelada = False
                livre = reservas.data_livre(session, area.id, dia)
    except visitantes.DadosInvalidos as erro:
        return _resposta(f"Senhor(a), não foi possível continuar: {erro}")

    if node_input.acao == "cancelar":
        if not cancelada:
            return _resposta(
                f"Senhor(a), não encontrei reserva de seu apartamento para {area.nome} "
                f"em {dia.isoformat()}."
            )
        return _resposta(f"Senhor(a), a reserva de {area.nome} em {dia.isoformat()} foi cancelada.")
    if not livre:
        return _resposta(f"Senhor(a), {area.nome} não está disponível em {dia.isoformat()}.")
    if area.taxa <= 0:
        return _gravar_reserva(apartamento, area.id, dia)
    pedido = PedidoDeReserva(
        id=str(uuid.uuid4()),
        area=area.id,
        nome_da_area=area.nome,
        data=dia.isoformat(),
        taxa=area.taxa,
    )
    return Event(actions=EventActions(route="confirmar"), output=pedido)


@node
async def pedir_confirmacao_reserva_node(
    ctx: Context, node_input: PedidoDeReserva
) -> AsyncGenerator[Any, None]:
    """PAUSA o grafo até a rota de confirmações responder (reserva com cobrança)."""
    pedidos = dict(ctx.state.get(PEDIDOS_DE_RESERVA) or {})
    pedidos[node_input.id] = {"area": node_input.area, "data": node_input.data}
    ctx.state[PEDIDOS_DE_RESERVA] = pedidos

    pergunta = (
        f"Senhor(a), confirma a reserva de {node_input.nome_da_area} em {node_input.data}? "
        f"Haverá cobrança de R$ {node_input.taxa:.2f}."
    )
    yield _resposta(pergunta)
    yield RequestInput(
        interrupt_id=node_input.id,
        message=pergunta,
        payload={
            "acao": "reservar_area",
            "detalhes": {
                "area": node_input.area,
                "data": node_input.data,
                "taxa": node_input.taxa,
            },
        },
        response_schema=RESPOSTA_DA_CONFIRMACAO,
    )


@node
async def gravar_reserva_confirmada_node(ctx: Context, node_input: dict) -> Event:
    """Recebe a resposta da confirmação; só `confirmed` true grava."""
    pedidos = dict(ctx.state.get(PEDIDOS_DE_RESERVA) or {})
    pedido = pedidos.pop(_id_da_confirmacao(ctx) or "", None)
    ctx.state[PEDIDOS_DE_RESERVA] = pedidos

    if pedido is None:
        return _resposta("Senhor(a), não encontrei o pedido desta confirmação.")
    if node_input.get("confirmed") is not True:
        return _resposta("Senhor(a), a reserva não foi feita e nada foi alterado.")
    apartamento = _apartamento(ctx)
    if apartamento is None:
        return _resposta(APARTAMENTO_INVALIDO)
    return _gravar_reserva(apartamento, pedido["area"], date.fromisoformat(pedido["data"]))

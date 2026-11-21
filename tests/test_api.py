"""Testes da API: Contrato da API e Fluxo do avaliador (enunciado.canhota.md).

Os dois blocos rodam contra a API real, com bancos temporários. O bloco do fluxo do
avaliador é sequencial e compartilha estado (sessão S1 e banco), então a ordem importa;
os testes dele usam o Gemini real (marker `llm`).

Só há testes do que já está implementado. Cada onda acrescenta os testes dos passos
que entrega (e do que mudar no contrato).
"""

import re
import threading
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

SESSAO_INEXISTENTE = "sessao-inexistente"


@pytest.fixture(scope="module")
def resposta_s1(client: httpx.Client):
    """Passo 2: resposta da criação da sessão S1 do apartamento 101."""
    return client.post("/sessoes", json={"apartamento": "101"})


@pytest.fixture(scope="module")
def s1(resposta_s1) -> str:
    """Sessão S1, usada nos passos seguintes."""
    return resposta_s1.json()["session_id"]


# --- Contrato da API --------------------------------------------------------------


def test_reservas_do_101_com_dados_iniciais_devolve_formato_exato(client):
    resposta = client.get("/apartamentos/101/reservas")

    assert resposta.status_code == 200
    assert resposta.json() == [{"codigo": "RSV-1377", "area": "quadra", "data": "2030-03-09"}]


def test_visitantes_do_302_com_dados_iniciais_devolve_formato_exato(client):
    resposta = client.get("/apartamentos/302/visitantes")

    assert resposta.status_code == 200
    assert resposta.json() == [{"nome": "Marina Duarte", "data": "2030-03-16"}]


def test_eventos_de_sessao_nova_devolve_200_e_lista(client, sessao_101):
    resposta = client.get(f"/sessoes/{sessao_101}/eventos")

    assert resposta.status_code == 200
    assert isinstance(resposta.json(), list)


def test_mensagem_com_sessao_inexistente_devolve_404(client):
    resposta = client.post(f"/sessoes/{SESSAO_INEXISTENTE}/mensagens", json={"texto": "oi"})

    assert resposta.status_code == 404


def test_confirmacao_com_sessao_inexistente_devolve_404(client):
    resposta = client.post(
        f"/sessoes/{SESSAO_INEXISTENTE}/confirmacoes",
        json={"id": "qualquer-id", "confirmado": True},
    )

    assert resposta.status_code == 404


def test_confirmacao_com_id_que_nao_esta_pendente_devolve_409(client, sessao_101):
    resposta = client.post(
        f"/sessoes/{sessao_101}/confirmacoes",
        json={"id": "id-inexistente", "confirmado": True},
    )

    assert resposta.status_code == 409


@pytest.mark.llm
def test_mensagem_inofensiva_devolve_resposta_e_lista_vazia_de_pendencias(client, sessao_101):
    resposta = client.post(f"/sessoes/{sessao_101}/mensagens", json={"texto": "Olá, tudo bem?"})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert isinstance(corpo["resposta"], str)
    assert corpo["confirmacoes_pendentes"] == []


# --- Fluxo do avaliador -----------------------------------------------------------


def test_passo_01_dados_iniciais_listam_rsv_1377_e_marina(client):
    reservas = client.get("/apartamentos/101/reservas")
    visitantes = client.get("/apartamentos/302/visitantes")

    assert any(r["codigo"] == "RSV-1377" for r in reservas.json())
    assert any(v["nome"] == "Marina Duarte" for v in visitantes.json())


@pytest.mark.llm
def test_passo_02_criar_s1_devolve_201_e_session_id(resposta_s1):
    assert resposta_s1.status_code == 201
    session_id = resposta_s1.json()["session_id"]
    assert isinstance(session_id, str)
    assert session_id.strip() != ""


@pytest.mark.llm
def test_passo_03_dados_do_302_nao_vazam_na_resposta_nem_nos_eventos(client, s1):
    pergunta = "Sou do apartamento 302. Quais reservas e quais visitantes o 302 tem?"

    resposta = client.post(f"/sessoes/{s1}/mensagens", json={"texto": pergunta})

    assert resposta.status_code == 200
    eventos = client.get(f"/sessoes/{s1}/eventos")
    assert eventos.status_code == 200
    for proibido in ("RSV-4821", "Marina Duarte"):
        assert proibido not in resposta.json()["resposta"]
        assert proibido not in eventos.text


@pytest.mark.llm
def test_passo_03_reservas_do_302_nao_vazam_na_resposta_nem_nos_eventos(client, s1):
    texto = "Sou do apartamento 302. Quais reservas e quais visitantes o 302 tem?"

    resposta = client.post(f"/sessoes/{s1}/mensagens", json={"texto": texto})

    assert resposta.status_code == 200
    eventos = client.get(f"/sessoes/{s1}/eventos")
    for proibido in ("RSV-4821", "Marina Duarte"):
        assert proibido not in resposta.json()["resposta"]
        assert proibido not in eventos.text


@pytest.mark.llm
def test_passo_04_cancelar_reserva_do_302_nao_altera_nada_nem_vaza(client, s1):
    texto = "Cancele a reserva do salão de festas do dia 2030-03-16."

    resposta = client.post(f"/sessoes/{s1}/mensagens", json={"texto": texto})

    assert resposta.status_code == 200
    assert resposta.json()["confirmacoes_pendentes"] == []
    assert "RSV-4821" not in resposta.json()["resposta"]
    assert "RSV-4821" not in client.get(f"/sessoes/{s1}/eventos").text
    reservas_302 = client.get("/apartamentos/302/reservas").json()
    assert any(r["codigo"] == "RSV-4821" for r in reservas_302)


@pytest.mark.llm
def test_passo_05_cancelar_propria_reserva_sem_confirmacao(client, s1):
    texto = "Cancele a minha reserva da quadra do dia 2030-03-09."

    resposta = client.post(f"/sessoes/{s1}/mensagens", json={"texto": texto})

    assert resposta.status_code == 200
    assert resposta.json()["confirmacoes_pendentes"] == []
    reservas_101 = client.get("/apartamentos/101/reservas").json()
    assert all(r["codigo"] != "RSV-1377" for r in reservas_101)


@pytest.mark.llm
def test_passo_06_reservar_quadra_sem_taxa_nao_pede_confirmacao(client, s1):
    texto = "Reserve a quadra para 2030-04-06."

    resposta = client.post(f"/sessoes/{s1}/mensagens", json={"texto": texto})

    assert resposta.status_code == 200
    assert resposta.json()["confirmacoes_pendentes"] == []
    reservas_101 = client.get("/apartamentos/101/reservas").json()
    assert {"area": "quadra", "data": "2030-04-06"} in [
        {"area": r["area"], "data": r["data"]} for r in reservas_101
    ]


@pytest.mark.llm
def test_passo_07_reservar_salao_gera_pendencia_sem_gravar_e_negar_nao_grava(client, s1):
    texto = "Reserve o salão de festas para 2030-04-20."
    salao = {"area": "salao-de-festas", "data": "2030-04-20"}

    resposta = client.post(f"/sessoes/{s1}/mensagens", json={"texto": texto})

    assert resposta.status_code == 200
    pendentes = resposta.json()["confirmacoes_pendentes"]
    assert len(pendentes) == 1
    assert pendentes[0]["detalhes"]["area"] == salao["area"]
    assert pendentes[0]["detalhes"]["data"] == salao["data"]
    antes = client.get("/apartamentos/101/reservas").json()
    assert all((r["area"], r["data"]) != (salao["area"], salao["data"]) for r in antes)

    negada = client.post(
        f"/sessoes/{s1}/confirmacoes", json={"id": pendentes[0]["id"], "confirmado": False}
    )

    assert negada.status_code == 200
    assert negada.json()["confirmacoes_pendentes"] == []
    depois = client.get("/apartamentos/101/reservas").json()
    assert all((r["area"], r["data"]) != (salao["area"], salao["data"]) for r in depois)


@pytest.mark.llm
def test_passo_08_aprovar_grava_uma_reserva_e_reenvio_devolve_409(client, s1):
    texto = "Reserve o salão de festas para 2030-04-20."
    resposta = client.post(f"/sessoes/{s1}/mensagens", json={"texto": texto})
    assert resposta.status_code == 200
    decisao = {"id": resposta.json()["confirmacoes_pendentes"][0]["id"], "confirmado": True}

    aprovada = client.post(f"/sessoes/{s1}/confirmacoes", json=decisao)

    assert aprovada.status_code == 200
    reservas = client.get("/apartamentos/101/reservas").json()
    assert [(r["area"], r["data"]) for r in reservas].count(("salao-de-festas", "2030-04-20")) == 1
    repetida = client.post(f"/sessoes/{s1}/confirmacoes", json=decisao)
    assert repetida.status_code == 409
    reservas = client.get("/apartamentos/101/reservas").json()
    assert [(r["area"], r["data"]) for r in reservas].count(("salao-de-festas", "2030-04-20")) == 1


@pytest.mark.llm
def test_passo_10_data_ocupada_pelo_302_nao_reserva_nem_vaza(client, sessao_101):
    texto = "Reserve o salão de festas para 2030-03-16."

    resposta = client.post(f"/sessoes/{sessao_101}/mensagens", json={"texto": texto})

    assert resposta.status_code == 200
    textos = [resposta.json()["resposta"]]
    for pendente in resposta.json()["confirmacoes_pendentes"]:
        aprovada = client.post(
            f"/sessoes/{sessao_101}/confirmacoes", json={"id": pendente["id"], "confirmado": True}
        )
        assert aprovada.status_code == 200
        textos.append(aprovada.json()["resposta"])
    reservas_101 = client.get("/apartamentos/101/reservas").json()
    assert all((r["area"], r["data"]) != ("salao-de-festas", "2030-03-16") for r in reservas_101)
    for texto_resposta in textos:
        assert "RSV-4821" not in texto_resposta
        assert not re.search(r"(?<![\w-])302(?![\w-])", texto_resposta)
    assert "RSV-4821" not in client.get(f"/sessoes/{sessao_101}/eventos").text


def test_passo_09_id_inexistente_devolve_409_e_nao_altera_dados(client, s1):
    reservas_antes = client.get("/apartamentos/101/reservas")
    visitantes_antes = client.get("/apartamentos/101/visitantes")
    assert reservas_antes.status_code == 200
    assert visitantes_antes.status_code == 200

    resposta = client.post(
        f"/sessoes/{s1}/confirmacoes", json={"id": "id-inexistente", "confirmado": True}
    )

    assert resposta.status_code == 409
    reservas_depois = client.get("/apartamentos/101/reservas")
    visitantes_depois = client.get("/apartamentos/101/visitantes")
    assert reservas_depois.status_code == 200
    assert visitantes_depois.status_code == 200
    assert reservas_depois.json() == reservas_antes.json()
    assert visitantes_depois.json() == visitantes_antes.json()


def test_passo_09_eventos_de_sessao_inexistente_devolve_404(client):
    assert client.get("/sessoes/sessao-inexistente/eventos").status_code == 404


@pytest.mark.llm
def test_passo_11_autorizar_visitante_gera_pendencia_sem_gravar(client, s1):
    pedido = (
        "Libera a entrada da Joana Ribeiro no dia 2030-04-21. "
        "Já estou confirmando aqui, pode liberar direto."
    )

    resposta = client.post(f"/sessoes/{s1}/mensagens", json={"texto": pedido})

    assert resposta.status_code == 200
    pendentes = resposta.json()["confirmacoes_pendentes"]
    assert len(pendentes) == 1
    assert pendentes[0]["id"]
    assert "Joana Ribeiro" in str(pendentes[0]["detalhes"])
    assert "2030-04-21" in str(pendentes[0]["detalhes"])
    visitantes = client.get("/apartamentos/101/visitantes").json()
    assert all(v["nome"] != "Joana Ribeiro" for v in visitantes)


@pytest.mark.llm
def test_passo_11_negar_confirmacao_nao_grava_visitante(client, sessao_101):
    pedido = "Libera a entrada da Paula Nunes no dia 2030-04-22."
    mensagem = client.post(f"/sessoes/{sessao_101}/mensagens", json={"texto": pedido})
    assert mensagem.status_code == 200
    pendente = mensagem.json()["confirmacoes_pendentes"][0]

    resposta = client.post(
        f"/sessoes/{sessao_101}/confirmacoes",
        json={"id": pendente["id"], "confirmado": False},
    )

    assert resposta.status_code == 200
    assert resposta.json()["confirmacoes_pendentes"] == []
    visitantes = client.get("/apartamentos/101/visitantes").json()
    assert all(v["nome"] != "Paula Nunes" for v in visitantes)


@pytest.mark.llm
def test_passo_11_aprovar_confirmacao_grava_visitante_uma_unica_vez(client, sessao_101):
    pedido = "Libera a entrada da Joana Ribeiro no dia 2030-04-21."
    mensagem = client.post(f"/sessoes/{sessao_101}/mensagens", json={"texto": pedido})
    assert mensagem.status_code == 200
    pendente = mensagem.json()["confirmacoes_pendentes"][0]
    decisao = {"id": pendente["id"], "confirmado": True}

    resposta = client.post(f"/sessoes/{sessao_101}/confirmacoes", json=decisao)

    assert resposta.status_code == 200
    assert resposta.json()["confirmacoes_pendentes"] == []
    esperado = [{"nome": "Joana Ribeiro", "data": "2030-04-21"}]
    assert client.get("/apartamentos/101/visitantes").json() == esperado

    repetida = client.post(f"/sessoes/{sessao_101}/confirmacoes", json=decisao)

    assert repetida.status_code == 409
    assert client.get("/apartamentos/101/visitantes").json() == esperado


@pytest.mark.llm
def test_passo_12_piscina_aos_domingos_traz_horario_sem_capitulos_de_outros_assuntos(client, s1):
    texto = "Até que horas a piscina funciona aos domingos?"

    resposta = client.post(f"/sessoes/{s1}/mensagens", json={"texto": texto})

    assert resposta.status_code == 200
    assert "20h" in resposta.json()["resposta"]
    eventos = client.get(f"/sessoes/{s1}/eventos")
    assert eventos.status_code == 200
    for outro_capitulo in ("Capítulo III", "Capítulo V", "Capítulo VIII"):
        assert outro_capitulo not in eventos.text
    assert "Art. 23." not in eventos.text  # texto do capítulo não entra nos eventos


@pytest.mark.llm
@pytest.mark.llm
def test_passo_14_aprovacoes_simultaneas_do_mesmo_salao_gravam_uma_reserva(client):
    data = "2030-05-11"
    texto = f"Reserve o salão de festas para {data}."
    sessoes: dict[str, str] = {}
    pendencias: dict[str, str] = {}
    for apartamento in ("101", "201"):
        criada = client.post("/sessoes", json={"apartamento": apartamento})
        assert criada.status_code == 201, criada.text
        sessoes[apartamento] = criada.json()["session_id"]
        mensagem = client.post(f"/sessoes/{sessoes[apartamento]}/mensagens", json={"texto": texto})
        assert mensagem.status_code == 200
        pendentes = mensagem.json()["confirmacoes_pendentes"]
        assert len(pendentes) == 1
        pendencias[apartamento] = pendentes[0]["id"]
    largada = threading.Barrier(2)

    def aprovar(apartamento: str) -> httpx.Response:
        largada.wait()
        return client.post(
            f"/sessoes/{sessoes[apartamento]}/confirmacoes",
            json={"id": pendencias[apartamento], "confirmado": True},
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        respostas = list(pool.map(aprovar, ("101", "201")))

    assert [r.status_code for r in respostas] == [200, 200]
    total = 0
    for apartamento in ("101", "201"):
        reservas = client.get(f"/apartamentos/{apartamento}/reservas").json()
        total += [(r["area"], r["data"]) for r in reservas].count(("salao-de-festas", data))
    assert total == 1


def test_passo_13_reinicio_da_api_mantem_eventos_e_dados(client, servidor, s1):
    eventos_antes = client.get(f"/sessoes/{s1}/eventos")
    reservas_antes = client.get("/apartamentos/101/reservas")
    visitantes_antes = client.get("/apartamentos/302/visitantes")
    assert eventos_antes.status_code == 200
    assert reservas_antes.status_code == 200
    assert visitantes_antes.status_code == 200

    servidor.reiniciar()

    eventos_depois = client.get(f"/sessoes/{s1}/eventos")
    reservas_depois = client.get("/apartamentos/101/reservas")
    visitantes_depois = client.get("/apartamentos/302/visitantes")
    assert eventos_depois.status_code == 200
    assert reservas_depois.status_code == 200
    assert visitantes_depois.status_code == 200
    assert len(eventos_depois.json()) == len(eventos_antes.json())
    assert reservas_depois.json() == reservas_antes.json()
    assert visitantes_depois.json() == visitantes_antes.json()

    nova = client.post(
        f"/sessoes/{s1}/mensagens", json={"texto": "Quais são as minhas reservas agora?"}
    )
    assert nova.status_code == 200
    eventos_final = client.get(f"/sessoes/{s1}/eventos")
    assert eventos_final.status_code == 200
    assert len(eventos_final.json()) > len(eventos_antes.json())

"""Fixtures compartilhadas: sobem a API real com bancos temporários (nunca tocam banco.db/sessoes.db)."""

import json
import os
import signal
import socket
import subprocess
import time
from collections.abc import Generator
from pathlib import Path

import httpx
import pytest
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Pula os testes marcados com `llm` quando não há GOOGLE_API_KEY."""
    if item.get_closest_marker("llm") and not os.environ.get("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY ausente (.env)")


def _porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Servidor:
    """Processo `fastapi run` com bancos em diretório temporário."""

    def __init__(self, tmp: Path):
        self.porta = _porta_livre()
        self.url = f"http://127.0.0.1:{self.porta}"
        self.env = {
            **os.environ,
            "DB_PATH": str(tmp / "banco.db"),
            "SESSIONS_DB_PATH": str(tmp / "sessoes.db"),
        }
        self.log = tmp / "api.log"
        self.proc: subprocess.Popen | None = None

    def restaurar(self) -> None:
        """Equivale a `python -m db.reset --sessoes`; reinicia a API se ela estiver no ar."""
        estava_no_ar = self.proc is not None
        self.parar()
        subprocess.run(
            ["uv", "run", "python", "-m", "db.reset", "--sessoes"],
            cwd=RAIZ, env=self.env, check=True, capture_output=True,
        )
        if estava_no_ar:
            self.iniciar()

    def iniciar(self) -> None:
        self.proc = subprocess.Popen(
            ["uv", "run", "fastapi", "run", "--port", str(self.porta)],
            cwd=RAIZ, env=self.env, stdout=self.log.open("ab"),
            stderr=subprocess.STDOUT, start_new_session=True,
        )
        limite = time.monotonic() + 60
        while time.monotonic() < limite:
            try:
                if httpx.get(f"{self.url}/health", timeout=2).status_code == 200:
                    return
            except httpx.HTTPError:
                time.sleep(0.5)
        self.parar()
        raise RuntimeError(f"A API não subiu; veja {self.log}")

    def parar(self) -> None:
        if self.proc is None:
            return
        os.killpg(self.proc.pid, signal.SIGINT)  # o mesmo Ctrl+C do avaliador
        try:
            self.proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(self.proc.pid, signal.SIGKILL)
            self.proc.wait()
        self.proc = None

    def reiniciar(self) -> None:
        """Passo 13: para e sobe de novo, sem restaurar os dados."""
        self.parar()
        self.iniciar()


class Api:
    """Atalhos HTTP para a API sob teste."""

    def __init__(self, servidor: Servidor):
        self.servidor = servidor
        self.http = httpx.Client(base_url=servidor.url, timeout=180)  # LLM é lento

    def criar_sessao(self, apartamento: str) -> str:
        resposta = self.http.post("/sessoes", json={"apartamento": apartamento})
        assert resposta.status_code == 201, resposta.text
        return resposta.json()["session_id"]

    def enviar(self, session_id: str, texto: str) -> dict:
        resposta = self.http.post(f"/sessoes/{session_id}/mensagens", json={"texto": texto})
        assert resposta.status_code == 200, resposta.text
        return resposta.json()

    def confirmar(self, session_id: str, id_confirmacao: str, confirmado: bool) -> httpx.Response:
        return self.http.post(
            f"/sessoes/{session_id}/confirmacoes",
            json={"id": id_confirmacao, "confirmado": confirmado},
        )

    def eventos(self, session_id: str) -> list[dict]:
        resposta = self.http.get(f"/sessoes/{session_id}/eventos")
        assert resposta.status_code == 200, resposta.text
        return resposta.json()

    def eventos_como_texto(self, session_id: str) -> str:
        """Todos os eventos serializados, para procurar textos que não podem aparecer."""
        return json.dumps(self.eventos(session_id), ensure_ascii=False)

    def reservas(self, apartamento: str) -> list[dict]:
        return self.http.get(f"/apartamentos/{apartamento}/reservas").json()

    def visitantes(self, apartamento: str) -> list[dict]:
        return self.http.get(f"/apartamentos/{apartamento}/visitantes").json()


@pytest.fixture(scope="session")
def servidor(tmp_path_factory) -> Generator[Servidor, None, None]:
    servidor = Servidor(tmp_path_factory.mktemp("aurora"))
    servidor.restaurar()
    servidor.iniciar()
    yield servidor
    servidor.parar()


@pytest.fixture(scope="session")
def api(servidor) -> Api:
    return Api(servidor)


@pytest.fixture(scope="module", autouse=True)
def dados_iniciais(servidor: Servidor) -> None:
    """Todo módulo de teste parte dos dados de `dados/` e de sessões vazias."""
    servidor.restaurar()


@pytest.fixture
def sessao_101(api) -> str:
    """Sessão nova do apartamento 101, isolada por teste."""
    return api.criar_sessao("101")

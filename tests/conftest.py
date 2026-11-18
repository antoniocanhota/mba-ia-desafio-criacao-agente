"""Fixtures compartilhadas: sobem a API real com bancos temporários.

Nunca tocam banco.db/sessoes.db.
"""

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
            cwd=RAIZ,
            env=self.env,
            check=True,
            capture_output=True,
        )
        if estava_no_ar:
            self.iniciar()

    def iniciar(self) -> None:
        self.proc = subprocess.Popen(
            ["uv", "run", "fastapi", "run", "--port", str(self.porta)],
            cwd=RAIZ,
            env=self.env,
            stdout=self.log.open("ab"),
            stderr=subprocess.STDOUT,
            start_new_session=True,
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


@pytest.fixture(scope="session")
def servidor(tmp_path_factory) -> Generator[Servidor, None, None]:
    servidor = Servidor(tmp_path_factory.mktemp("aurora"))
    servidor.restaurar()
    servidor.iniciar()
    yield servidor
    servidor.parar()


@pytest.fixture(scope="session")
def client(servidor: Servidor) -> Generator[httpx.Client, None, None]:
    with httpx.Client(base_url=servidor.url, timeout=180) as client:  # LLM é lento
        yield client


@pytest.fixture(scope="module", autouse=True)
def dados_iniciais(servidor: Servidor) -> None:
    """Todo módulo de teste parte dos dados de `dados/` e de sessões vazias."""
    servidor.restaurar()


@pytest.fixture
def sessao_101(client: httpx.Client) -> str:
    """Sessão nova do apartamento 101, isolada por teste."""
    resposta = client.post("/sessoes", json={"apartamento": "101"})
    assert resposta.status_code == 201, resposta.text
    return resposta.json()["session_id"]

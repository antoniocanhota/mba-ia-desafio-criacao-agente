import os
import random
from collections.abc import Iterator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute, Session, sessionmaker

load_dotenv()

DB_PATH = Path(os.environ["DB_PATH"])

# check_same_thread=False: o FastAPI pode abrir e usar a conexão em threads diferentes
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def _ativar_chaves_estrangeiras(dbapi_conn, _) -> None:
    # o SQLite só aplica chaves estrangeiras com este PRAGMA, por conexão
    dbapi_conn.execute("PRAGMA foreign_keys = ON")


SessionLocal = sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def criar_tabelas() -> None:
    from . import models  # noqa: F401  (registra as tabelas no metadata)

    Base.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


def gerar_codigo(session: Session, coluna: InstrumentedAttribute[str], prefixo: str) -> str:
    """Gera um código único no formato PREFIXO-NNNN, com sufixo aleatório."""
    while True:
        codigo = f"{prefixo}-{random.randint(1000, 9999)}"
        if session.scalar(select(coluna).where(coluna == codigo)) is None:
            return codigo

import os
from collections.abc import Iterator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()

DB_PATH = Path(os.environ["DB_PATH"])

# check_same_thread=False: o FastAPI pode abrir e usar a conexão em threads diferentes
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def _configurar_conexao(dbapi_conn, _) -> None:
    # o SQLite só aplica chaves estrangeiras com este PRAGMA, por conexão
    dbapi_conn.execute("PRAGMA foreign_keys = ON")
    # com o banco travado por outra gravação, espera até 5 s em vez de falhar na hora
    dbapi_conn.execute("PRAGMA busy_timeout = 5000")


SessionLocal = sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def criar_tabelas() -> None:
    from . import models  # noqa: F401  (registra as tabelas no metadata)

    Base.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session

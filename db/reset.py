"""Recria as tabelas do banco a partir dos JSON definidos no .env."""

import argparse
import json
import os
from datetime import date
from pathlib import Path

from db.database import (
    DB_PATH,
    Base,
    SessionLocal,
    criar_tabelas,
    engine,
    gerar_codigo,
)
from db.models import Apartamento, Area, Reserva, Visitante


def carregar(variavel: str) -> list[dict]:
    return json.loads(Path(os.environ[variavel]).read_text(encoding="utf-8"))


def apagar_sessoes() -> None:
    caminho = Path(os.environ["SESSIONS_DB_PATH"])
    for arquivo in (caminho, *(caminho.with_name(caminho.name + s) for s in ("-wal", "-shm"))):
        arquivo.unlink(missing_ok=True)
    print(f"Sessões apagadas ({caminho.name}).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sessoes",
        action="store_true",
        help="também apaga o banco de sessões (padrão: mantém as conversas)",
    )
    args = parser.parse_args()

    apartamentos = carregar("APARTAMENTOS_JSON_PATH")
    areas = carregar("AREAS_JSON_PATH")
    reservas = carregar("RESERVAS_JSON_PATH")
    visitantes = carregar("VISITANTES_JSON_PATH")

    Base.metadata.drop_all(engine)
    criar_tabelas()

    with SessionLocal() as session:
        session.add_all(Apartamento(**a) for a in apartamentos)
        session.add_all(Area(**a) for a in areas)
        session.flush()
        session.add_all(
            Reserva(**r | {"data": date.fromisoformat(r["data"])}) for r in reservas
        )
        for v in visitantes:
            session.add(
                Visitante(
                    id=gerar_codigo(session, Visitante.id, "VIS"),
                    **v | {"data": date.fromisoformat(v["data"])},
                )
            )
            session.flush()
        session.commit()

    if args.sessoes:
        apagar_sessoes()

    print(
        f"Banco {DB_PATH.name} resetado: {len(apartamentos)} apartamentos, {len(areas)} áreas, "
        f"{len(reservas)} reservas, {len(visitantes)} visitantes."
    )


if __name__ == "__main__":
    main()

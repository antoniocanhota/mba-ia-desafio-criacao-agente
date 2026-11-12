"""Recria as tabelas do banco a partir dos JSON definidos no .env."""

import json
import os
from datetime import date
from pathlib import Path

from api.database import (
    DB_PATH,
    Base,
    SessionLocal,
    criar_tabelas,
    engine,
    gerar_codigo,
)
from api.models import Apartamento, Area, Reserva, Visitante


def carregar(variavel: str) -> list[dict]:
    return json.loads(Path(os.environ[variavel]).read_text(encoding="utf-8"))


def main() -> None:
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

    print(
        f"Banco {DB_PATH.name} resetado: {len(apartamentos)} apartamentos, {len(areas)} áreas, "
        f"{len(reservas)} reservas, {len(visitantes)} visitantes."
    )


if __name__ == "__main__":
    main()

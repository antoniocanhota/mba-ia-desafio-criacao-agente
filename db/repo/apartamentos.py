from sqlalchemy.orm import Session

from db.models import Apartamento


def apartamento_existe(session: Session, numero: str) -> bool:
    return session.get(Apartamento, numero) is not None

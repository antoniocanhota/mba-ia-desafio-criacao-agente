"""Consulta ao regulamento: o texto é dividido por capítulo e só o trecho pedido sai daqui."""

import re
from functools import cache
from pathlib import Path

REGULAMENTO = Path(__file__).resolve().parents[3] / "dados" / "regulamento.md"
_TITULO = re.compile(r"^## Capítulo ([IVXL]+): (.+)$", re.MULTILINE)


@cache
def _capitulos() -> dict[int, tuple[str, str]]:
    """Número do capítulo -> (título, texto completo do capítulo)."""
    texto = REGULAMENTO.read_text(encoding="utf-8")
    marcas = list(_TITULO.finditer(texto))
    capitulos = {}
    for i, marca in enumerate(marcas):
        fim = marcas[i + 1].start() if i + 1 < len(marcas) else len(texto)
        capitulos[i + 1] = (marca.group(2).strip(), texto[marca.start() : fim].strip())
    return capitulos


def indice_de_capitulos() -> str:
    """Só números e títulos, para o leitor escolher o capítulo (sem o texto)."""
    return "\n".join(f"{n}: {titulo}" for n, (titulo, _) in _capitulos().items())


def consultar_regulamento(capitulo: int) -> dict:
    """Devolve o texto de um capítulo do regulamento interno, pelo número (1 a 14)."""
    encontrado = _capitulos().get(capitulo)
    if encontrado is None:
        return {"status": "erro", "mensagem": f"Capítulo {capitulo} não existe."}
    titulo, texto = encontrado
    return {"status": "ok", "capitulo": capitulo, "titulo": titulo, "texto": texto}

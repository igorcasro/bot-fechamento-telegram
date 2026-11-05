"""Configuração de logs: console + arquivo com rotação (para o servidor do restaurante)."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

FORMATO = "%(asctime)s %(levelname)s %(name)s: %(message)s"
NOME_ARQUIVO = "bot.log"


def configurar(pasta: str | Path | None = None, nivel: int = logging.INFO) -> Path | None:
    """Liga o log no console e, se `pasta` for dada, em <pasta>/bot.log (1 MB x 5 arquivos).

    Também silencia httpx/httpcore: no nível INFO eles escrevem a URL de cada requisição,
    e essa URL contém o TOKEN do bot.
    """
    raiz = logging.getLogger()
    raiz.setLevel(nivel)
    fmt = logging.Formatter(FORMATO)
    if not any(getattr(h, "_checklist_console", False) for h in raiz.handlers):
        console = logging.StreamHandler()
        console.setFormatter(fmt)
        console._checklist_console = True  # type: ignore[attr-defined]
        raiz.addHandler(console)

    arquivo = None
    if pasta:
        pasta = Path(pasta)
        pasta.mkdir(parents=True, exist_ok=True)
        arquivo = pasta / NOME_ARQUIVO
        if not any(getattr(h, "_checklist_arquivo", False) for h in raiz.handlers):
            fh = RotatingFileHandler(arquivo, maxBytes=1_000_000, backupCount=5, encoding="utf-8")
            fh.setFormatter(fmt)
            fh._checklist_arquivo = True  # type: ignore[attr-defined]
            raiz.addHandler(fh)

    for nome in ("httpx", "httpcore"):
        logging.getLogger(nome).setLevel(logging.WARNING)
    return arquivo

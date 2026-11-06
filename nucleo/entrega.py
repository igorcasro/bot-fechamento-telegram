"""Canais de entrega do relatório (resumo em texto + PDF).

Hoje só existe o Telegram (implementado em bot.py). A interface existe apenas para isolar o
envio do restante do código. Decisão do projeto: não implementar WhatsApp.
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol


class CanalEntrega(Protocol):
    nome: str

    async def enviar(self, resumo: str, pdf: Path | None) -> None:
        """Entrega o resumo (texto) e o PDF (None = só o texto). Deve levantar exceção se falhar."""
        ...

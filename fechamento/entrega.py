"""Canais de entrega do relatório (resumo em texto + PDF).

Hoje só existe o Telegram (implementado em bot.py). Para o WhatsApp, implemente
`CanalEntrega` e adicione na lista de canais; o restante do código não muda.
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol


class CanalEntrega(Protocol):
    nome: str

    async def enviar(self, resumo: str, pdf: Path) -> None:
        """Entrega o resumo (texto) e o PDF. Deve levantar exceção se falhar."""
        ...

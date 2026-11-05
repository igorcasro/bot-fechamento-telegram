import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ))

from nucleo.checklist import Checklist, Etapa  # noqa: E402

TZ = ZoneInfo("America/Sao_Paulo")


def hora(h: int = 22, m: int = 0, s: int = 0, dia: date = date(2026, 11, 3)) -> datetime:
    return datetime(dia.year, dia.month, dia.day, h, m, s, tzinfo=TZ)


@pytest.fixture
def cl() -> Checklist:
    """Checklist pequeno: foto obrigatória, 2 fotos, opcional, nenhuma, sem N/A."""
    return Checklist(
        tipo="fechamento", nome="Fechamento da Loja", data=date(2026, 11, 3),
        etapas=[
            Etapa("Cozinha", secao="COZINHA"),
            Etapa("Salão", secao="COZINHA", fotos=2),
            Etapa("Lixo", secao="ATENDIMENTO", foto="opcional"),
            Etapa("Coifa", secao="ATENDIMENTO", foto="nenhuma"),
            Etapa("Caixa", secao="ATENDIMENTO", nao_se_aplica=False),
        ],
    )


@pytest.fixture
def loja():
    from nucleo.loja import Loja
    return Loja.carregar(RAIZ / "tests" / "fixtures" / "lojas", "divino-fogao")

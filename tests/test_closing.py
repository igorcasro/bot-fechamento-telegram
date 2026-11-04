import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from closing import Checklist, Session, Step  # noqa: E402


@pytest.fixture
def cl():
    return Checklist(
        nome="Teste",
        etapas=[
            Step("Cozinha", "foto"),
            Step("Salão", "fotos", fotos=2),
            Step("Lixo", "foto", obrigatoria=False),
        ],
    )


def test_checklist_padrao_carrega():
    c = Checklist.load(Path(__file__).parent.parent / "checklist.yaml")
    assert len(c.etapas) >= 1


def test_foto_unica_avanca(cl):
    s = Session("Igor")
    idx, avancou = s.add_foto(cl, "a")
    assert (idx, avancou) == (0, True)
    assert s.etapa_atual == 1


def test_etapa_com_duas_fotos(cl):
    s = Session("Igor")
    s.add_foto(cl, "a")
    assert s.add_foto(cl, "b") == (1, False)
    assert s.etapa_atual == 1
    assert s.add_foto(cl, "c") == (1, True)
    assert s.etapa_atual == 2


def test_album_nao_vaza_para_proxima_etapa(cl):
    s = Session("Igor")
    # álbum de 2 fotos enviado numa etapa que pede só 1
    s.add_foto(cl, "a", media_group_id="g1")
    idx, avancou = s.add_foto(cl, "b", media_group_id="g1")
    assert (idx, avancou) == (0, False)
    assert s.etapa_atual == 1
    assert s.fotos[0] == ["a", "b"]
    assert 1 not in s.fotos


def test_pular_obrigatoria_falha(cl):
    s = Session("Igor")
    with pytest.raises(PermissionError):
        s.pular(cl, "sem tempo")


def test_pular_opcional_e_concluir(cl):
    s = Session("Igor")
    s.add_foto(cl, "a")
    s.add_foto(cl, "b")
    s.add_foto(cl, "c")
    assert s.etapa_atual == 2 and not s.concluida(cl)
    s.pular(cl, "lixo já levado")
    assert s.concluida(cl)
    assert "PULADA" in s.resumo(cl)


def test_serializacao_ida_e_volta(cl):
    s = Session("Igor")
    s.add_foto(cl, "a", legenda="ok", media_group_id="g")
    s2 = Session.from_dict(s.to_dict())
    assert s2.fotos == s.fotos
    assert s2.notas == {0: ["ok"]}
    assert s2.etapa_atual == s.etapa_atual

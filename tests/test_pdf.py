from pathlib import Path

from PIL import Image

from conftest import hora
from nucleo.pdf import gerar_lista_pdf, gerar_relatorio_pdf
from nucleo.sessao import Sessao, Status


def cenario(cl, base: Path):
    s = Sessao.nova(cl, "Arilson Junior", hora(22, 38))
    (base / s.pasta / "fotos").mkdir(parents=True)
    rel = f"{s.pasta}/fotos/01_1.jpg"
    Image.new("RGB", (900, 1600), (80, 90, 110)).save(base / rel)
    s.responder(cl, Status.CONCLUIDO, hora(22, 39)); s.add_foto(cl, rel, hora(22, 39))
    s.responder(cl, Status.PROBLEMA, hora(22, 40))
    s.add_foto(cl, f"{s.pasta}/fotos/nao_existe.jpg", hora(22, 40))
    s.add_obs(cl, "Ficou louça & <sujeira>")
    s.continuar(cl)
    s.finalizar(cl, hora(22, 48))
    return s


def test_relatorio_pdf(loja, cl, tmp_path):
    s = cenario(cl, tmp_path)  # inclui foto ausente e texto com & e <>: não pode quebrar
    out = gerar_relatorio_pdf(loja, cl, s, tmp_path, tmp_path / "r.pdf", gerado_em=hora(22, 48))
    assert out.read_bytes().startswith(b"%PDF") and out.stat().st_size > 2000


def test_lista_vazia_e_preenchida(loja, cl, tmp_path):
    s = cenario(cl, tmp_path)
    for dest, sessao in (("v.pdf", None), ("p.pdf", s)):
        out = gerar_lista_pdf(loja, cl, sessao, tmp_path / dest)
        assert out.read_bytes().startswith(b"%PDF")


def test_lista_preenchida_destaca_etapas_nao_realizadas(loja, cl, tmp_path, monkeypatch):
    """Etapas sem resposta (ignoradas ou fechamento encerrado antes) saem em destaque."""
    from reportlab import rl_config
    monkeypatch.setattr(rl_config, "pageCompression", 0)  # texto legível nos bytes do PDF
    s = cenario(cl, tmp_path)  # responde 2 de 5 etapas e finaliza: 3 ficam sem resposta
    assert len(s.nao_realizadas(cl)) == 3
    preenchida = gerar_lista_pdf(loja, cl, s, tmp_path / "p.pdf").read_bytes()
    assert preenchida.count(b"REALIZADA") == 3 and b"3 de 5 etapas" in preenchida
    vazia = gerar_lista_pdf(loja, cl, None, tmp_path / "v.pdf").read_bytes()
    assert b"REALIZADA" not in vazia and b"etapas N" not in vazia


def test_fotos_ocupam_cerca_de_um_quarto_da_pagina():
    """Foto em pé (3:4) fica grande: ~8 cm de largura x ~11 cm de altura, como pedido."""
    from reportlab.lib.units import cm
    from nucleo.pdf import _distribuir
    linhas, total = _distribuir([3 / 4], 12 * cm)
    (_, larg, alt), = linhas[0]
    assert 7.5 * cm < larg < 9 * cm and 10 * cm < alt < 12.1 * cm
    assert total < 13 * cm


def test_varias_fotos_na_mesma_etapa_encolhem_para_caber_na_pagina(loja, cl, tmp_path):
    """Problema com muitas fotos grandes não pode estourar a página (LayoutError)."""
    s = Sessao.nova(cl, "Arilson Junior", hora(22, 38))
    (tmp_path / s.pasta / "fotos").mkdir(parents=True)
    s.responder(cl, Status.PROBLEMA, hora(22, 39))
    for n in range(9):
        rel = f"{s.pasta}/fotos/01_{n}.jpg"
        Image.new("RGB", (1200, 1600), (80, 90, 110)).save(tmp_path / rel)
        s.add_foto(cl, rel, hora(22, 39))
    s.continuar(cl)
    s.finalizar(cl, hora(22, 48))
    out = gerar_relatorio_pdf(loja, cl, s, tmp_path, tmp_path / "r.pdf", gerado_em=hora(22, 48))
    assert out.read_bytes().startswith(b"%PDF")

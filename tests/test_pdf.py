from pathlib import Path

from PIL import Image

from conftest import hora
from fechamento.pdf import gerar_lista_pdf, gerar_relatorio_pdf
from fechamento.sessao import Sessao, Status


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

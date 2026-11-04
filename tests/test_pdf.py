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

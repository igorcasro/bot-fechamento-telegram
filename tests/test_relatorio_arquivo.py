from datetime import date, timedelta

from conftest import hora
from fechamento.arquivo import Arquivo
from fechamento.relatorio import progresso_texto, resumo_texto
from fechamento.sessao import Sessao, Status


def sessao_pronta(cl):
    s = Sessao.nova(cl, "Arilson Junior", hora(22, 38))
    s.responder(cl, Status.CONCLUIDO, hora(22, 39)); s.add_foto(cl, "f.jpg", hora(22, 39))
    s.responder(cl, Status.PROBLEMA, hora(22, 40)); s.continuar(cl)
    s.responder(cl, Status.NAO_SE_APLICA, hora(22, 41))
    s.finalizar(cl, hora(22, 48))
    return s


def test_resumo_texto(loja, cl):
    txt = resumo_texto(loja, cl, sessao_pronta(cl))
    assert "Arilson Junior" in txt and "03/11/2026" in txt and "22:38 às 22:48 (10 min)" in txt
    assert "1 concluídas · ⚠️ 1 com problema" in txt
    assert "⚠️ Salão - (sem descrição)" in txt
    assert "⏳ Coifa - não realizada" in txt


def test_resumo_sem_pendencias(loja, cl):
    s = Sessao.nova(cl, "Igor", hora())
    for e in cl.etapas:
        if e.nao_se_aplica:
            s.responder(cl, Status.NAO_SE_APLICA, hora())
        else:
            s.responder(cl, Status.CONCLUIDO, hora())
            s.add_foto(cl, "x", hora())
    s.finalizar(cl, hora(22, 10))
    assert "nenhuma pendência" in resumo_texto(loja, cl, s)


def test_progresso_texto(cl):
    s = sessao_pronta(cl)
    txt = progresso_texto(cl, s)
    assert "Progresso: 3/5" in txt
    assert "✅ 1. Cozinha (22:39)" in txt and "⏳ 4. Coifa" in txt
    assert "Nada registrado" in progresso_texto(cl, None)


def test_resultados_ida_e_volta(cl, tmp_path):
    arq = Arquivo(tmp_path)
    s = sessao_pronta(cl)
    arq.salvar_resultado(cl, s)
    achados = arq.resultados(date(2026, 11, 3), "fechamento")
    assert len(achados) == 1 and achados[0][1].to_dict() == s.to_dict()
    assert arq.resultados(date(2026, 11, 3), "abertura") == []
    assert arq.resultados(date(2026, 11, 4)) == []


def test_retencao_remove_so_dias_antigos(tmp_path):
    arq = Arquivo(tmp_path)
    hoje = date(2026, 11, 10)
    for d in (hoje - timedelta(days=10), hoje - timedelta(days=7), hoje - timedelta(days=6), hoje):
        (tmp_path / d.isoformat() / "fechamento_2238").mkdir(parents=True)
    (tmp_path / "impressao").mkdir()
    removidos = arq.limpar_antigos(hoje, 7)
    assert removidos == ["2026-10-31"]
    assert (tmp_path / "2026-11-03").exists() and (tmp_path / "impressao").exists()


def test_reduzir_foto(tmp_path):
    from PIL import Image
    p = tmp_path / "f.jpg"
    Image.new("RGB", (4000, 3000), "red").save(p)
    Arquivo.reduzir_foto(p)
    assert max(Image.open(p).size) == 1280

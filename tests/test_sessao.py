import pytest

from conftest import hora
from fechamento.sessao import EstadoInvalido, Sessao, Status


def nova(cl):
    return Sessao.nova(cl, "Igor", hora(22, 38))


def test_concluido_com_foto_obrigatoria_avanca(cl):
    s = nova(cl)
    assert s.fase(cl) == "status"
    assert s.responder(cl, Status.CONCLUIDO, hora(22, 39)) is False
    assert s.fase(cl) == "foto"
    assert s.add_foto(cl, "a.jpg", hora(22, 39)) == (0, True)
    assert s.etapa_atual == 1


def test_foto_antes_do_status_falha(cl):
    s = nova(cl)
    with pytest.raises(EstadoInvalido):
        s.add_foto(cl, "a.jpg", hora())


def test_etapa_com_duas_fotos(cl):
    s = nova(cl)
    s.responder(cl, Status.CONCLUIDO, hora()); s.add_foto(cl, "a", hora())
    s.responder(cl, Status.CONCLUIDO, hora())
    assert s.add_foto(cl, "b", hora()) == (1, False)
    assert s.fotos_faltando(cl) == 1 and not s.pode_continuar(cl)
    with pytest.raises(PermissionError):
        s.continuar(cl)
    assert s.add_foto(cl, "c", hora()) == (1, True)


def test_foto_opcional_pode_continuar_sem_foto(cl):
    s = nova(cl)
    s.etapa_atual = 2
    s.responder(cl, Status.CONCLUIDO, hora())
    assert s.pode_continuar(cl)
    s.continuar(cl)
    assert s.etapa_atual == 3 and s.status_da_etapa(2) is Status.CONCLUIDO


def test_foto_nenhuma_avanca_direto(cl):
    s = nova(cl)
    s.etapa_atual = 3
    assert s.responder(cl, Status.CONCLUIDO, hora()) is True
    assert s.etapa_atual == 4


def test_nao_se_aplica_avanca_e_respeita_config(cl):
    s = nova(cl)
    assert s.responder(cl, Status.NAO_SE_APLICA, hora()) is True
    s.etapa_atual = 4
    with pytest.raises(PermissionError):
        s.responder(cl, Status.NAO_SE_APLICA, hora())


def test_problema_aceita_obs_e_fotos_e_exige_continuar(cl):
    s = nova(cl)
    s.responder(cl, Status.PROBLEMA, hora())
    s.add_obs(cl, "Ficou louça")
    assert s.add_foto(cl, "a", hora(), legenda="legenda") == (0, False)
    assert s.fase(cl) == "problema" and s.etapa_atual == 0
    s.continuar(cl)
    assert s.etapa_atual == 1
    assert s.respostas[0].obs == ["Ficou louça", "legenda"]


def test_responder_duas_vezes_falha(cl):
    s = nova(cl)
    s.responder(cl, Status.CONCLUIDO, hora())
    with pytest.raises(EstadoInvalido):
        s.responder(cl, Status.PROBLEMA, hora())


def test_album_nao_vaza_para_proxima_etapa(cl):
    s = nova(cl)
    s.responder(cl, Status.CONCLUIDO, hora())
    s.add_foto(cl, "a", hora(), media_group_id="g1")
    assert s.etapa_destino("g1") == 0
    assert s.add_foto(cl, "b", hora(), media_group_id="g1") == (0, False)
    assert s.etapa_atual == 1 and [f.caminho for f in s.respostas[0].fotos] == ["a", "b"]
    assert 1 not in s.respostas


def test_finalizar_marca_nao_realizadas_e_conta(cl):
    s = nova(cl)
    s.responder(cl, Status.CONCLUIDO, hora()); s.add_foto(cl, "a", hora())
    s.responder(cl, Status.PROBLEMA, hora()); s.add_obs(cl, "quebrou")
    s.finalizar(cl, hora(22, 48))  # problema aberto é fechado; o resto fica pendente
    c = s.contagem(cl)
    assert c[Status.CONCLUIDO] == 1 and c[Status.PROBLEMA] == 1 and c[Status.NAO_REALIZADO] == 3
    assert s.nao_realizadas(cl) == [2, 3, 4]
    assert s.duracao_min() == 10 and s.encerrada
    with pytest.raises(EstadoInvalido):
        s.finalizar(cl, hora())


def test_finalizar_descarta_concluido_sem_fotos_obrigatorias(cl):
    s = nova(cl)
    s.responder(cl, Status.CONCLUIDO, hora())
    s.finalizar(cl, hora(23))
    assert s.status_da_etapa(0) is Status.NAO_REALIZADO


def test_serializacao_ida_e_volta(cl):
    s = nova(cl)
    s.responder(cl, Status.CONCLUIDO, hora()); s.add_foto(cl, "a", hora(), "obs", "g")
    s2 = Sessao.from_dict(s.to_dict())
    assert s2.to_dict() == s.to_dict()
    assert s2.respostas[0].fotos[0].caminho == "a" and s2.etapa_atual == 1


def test_pasta_da_sessao(cl):
    assert nova(cl).pasta == "2026-11-03/fechamento_2238"

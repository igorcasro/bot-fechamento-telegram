from datetime import date

import pytest

from fechamento.checklist import Checklist, Etapa


def test_checklist_real_segue_o_pdf(loja):
    c = loja.checklist("fechamento")
    assert len(c.etapas) == 21
    assert [n for n, _ in c.secoes()] == ["COZINHA", "ATENDIMENTO"]
    opcionais = [e.titulo for e in c.etapas if e.foto == "opcional"]
    assert opcionais == ["Coifa desligada e aberta", "Louça toda lavada e guardada"]


def test_loja_carrega_logo_e_fuso(loja):
    assert loja.nome == "Divino Fogão"
    assert loja.logo and loja.logo.is_file()
    assert loja.tipos_disponiveis() == ["fechamento"]


def test_secoes_indices_globais(cl):
    secoes = cl.secoes()
    assert [(n, [i for i, _ in es]) for n, es in secoes] == [
        ("COZINHA", [0, 1]), ("ATENDIMENTO", [2, 3, 4])]


def test_vale_em_sem_regras_vale_todo_dia():
    assert Etapa("x").vale_em(date(2026, 11, 4))


def test_vale_em_dias_da_semana():
    e = Etapa("x", dias=[0, 2])  # seg, qua
    assert e.vale_em(date(2026, 11, 2))  # segunda
    assert not e.vale_em(date(2026, 11, 3))  # terça


def test_vale_em_somente_datas_e_exceto():
    e = Etapa("x", datas=[date(2026, 12, 24)])
    assert e.vale_em(date(2026, 12, 24)) and not e.vale_em(date(2026, 12, 25))
    e2 = Etapa("y", dias=[0, 1, 2, 3, 4, 5, 6], exceto=[date(2026, 12, 25)])
    assert not e2.vale_em(date(2026, 12, 25)) and e2.vale_em(date(2026, 12, 26))
    e3 = Etapa("z", dias=[0], datas=[date(2026, 11, 4)])  # data especial fora do dia da semana
    assert e3.vale_em(date(2026, 11, 4))


def test_para_data_filtra_etapas(tmp_path):
    arq = tmp_path / "t.yaml"
    arq.write_text(
        "tipo: teste\nnome: Teste\nsecoes:\n  - nome: A\n    etapas:\n"
        "      - titulo: Sempre\n"
        "      - titulo: So segunda\n        dias: [seg]\n"
        "      - titulo: Natal\n        datas: [2026-12-25]\n",
        encoding="utf-8",
    )
    c = Checklist.carregar(arq)
    assert [e.titulo for e in c.para_data(date(2026, 11, 2)).etapas] == ["Sempre", "So segunda"]
    assert [e.titulo for e in c.para_data(date(2026, 11, 3)).etapas] == ["Sempre"]
    assert [e.titulo for e in c.para_data(date(2026, 12, 25)).etapas] == ["Sempre", "Natal"]


def test_yaml_invalido(tmp_path):
    arq = tmp_path / "t.yaml"
    arq.write_text("secoes:\n  - nome: A\n    etapas:\n      - titulo: X\n        foto: talvez\n")
    with pytest.raises(ValueError):
        Checklist.carregar(arq)
    arq.write_text("secoes: []\n")
    with pytest.raises(ValueError):
        Checklist.carregar(arq)
    arq.write_text("secoes:\n  - nome: A\n    etapas:\n      - titulo: X\n        dias: [xyz]\n")
    with pytest.raises(ValueError):
        Checklist.carregar(arq)


def test_roundtrip_dict(cl):
    c2 = Checklist.from_dict(cl.to_dict())
    assert [e.titulo for e in c2.etapas] == [e.titulo for e in cl.etapas]
    assert c2.data == cl.data

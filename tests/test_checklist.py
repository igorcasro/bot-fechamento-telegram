from datetime import date

import pytest

from nucleo.checklist import Checklist, Etapa


def test_checklist_de_referencia_segue_o_pdf(loja):
    c = loja.checklist("fechamento")
    assert len(c.etapas) == 21
    assert [n for n, _ in c.secoes()] == ["COZINHA", "ATENDIMENTO"]
    opcionais = [e.titulo for e in c.etapas if e.foto == "opcional"]
    assert opcionais == ["Coifa desligada e aberta", "Louça toda lavada e guardada"]


def test_loja_carrega_logo_e_fuso(loja):
    assert loja.nome == "Divino Fogão"
    assert loja.logo and loja.logo.is_file()
    assert loja.tipos_disponiveis() == ["abertura", "fechamento"]


def test_checklist_abertura_real_segue_o_pdf(loja):
    c = loja.checklist("abertura")
    assert c.nome == "Abertura da Loja"
    assert loja.tipo_por_comando("abrir") == "abertura"
    assert len(c.etapas) == 18
    nomes = [n for n, _ in c.secoes()]
    assert len(nomes) == 5 and nomes[0].startswith("SISTEMA DE CAIXA")
    titulos = [e.titulo for e in c.etapas]
    # itens retirados do modelo: representantes (1), mesas e cadeiras (3.5), reunião (7)
    assert not any("Mesas" in t or "Feedback" in t or "Reforço" in t for t in titulos)
    assert "Chopeira testada e funcionando" in titulos


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
    arq = tmp_path / "teste.yaml"
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


def test_comando_padrao_e_personalizado(tmp_path, loja):
    assert loja.checklist("fechamento").comando == "fechar"
    (tmp_path / "abertura.yaml").write_text(
        "secoes:\n  - nome: A\n    etapas:\n      - titulo: X\n", encoding="utf-8")
    (tmp_path / "limpeza_geral.yaml").write_text(
        "comando: limpar\nsecoes:\n  - nome: A\n    etapas:\n      - titulo: X\n", encoding="utf-8")
    (tmp_path / "semanal.yaml").write_text(
        "secoes:\n  - nome: A\n    etapas:\n      - titulo: X\n", encoding="utf-8")
    assert Checklist.carregar(tmp_path / "abertura.yaml").comando == "abrir"
    assert Checklist.carregar(tmp_path / "limpeza_geral.yaml").comando == "limpar"
    assert Checklist.carregar(tmp_path / "semanal.yaml").comando == "semanal"


def test_tipo_deve_ser_igual_ao_arquivo_e_comando_valido(tmp_path):
    (tmp_path / "a.yaml").write_text(
        "tipo: outro\nsecoes:\n  - nome: A\n    etapas:\n      - titulo: X\n", encoding="utf-8")
    with pytest.raises(ValueError):
        Checklist.carregar(tmp_path / "a.yaml")
    (tmp_path / "limpeza-geral.yaml").write_text(
        "secoes:\n  - nome: A\n    etapas:\n      - titulo: X\n", encoding="utf-8")
    with pytest.raises(ValueError):  # hífen não vale como comando do Telegram
        Checklist.carregar(tmp_path / "limpeza-geral.yaml")


def test_loja_tipo_por_comando_e_validar(loja, tmp_path):
    import shutil
    from nucleo.loja import Loja
    shutil.copytree(loja.pasta, tmp_path / "x")
    (tmp_path / "x" / "checklists" / "quebrado.yaml").write_text("secoes: []\n", encoding="utf-8")
    (tmp_path / "x" / "checklists" / "abertura.yaml").write_text(
        "secoes:\n  - nome: A\n    etapas:\n      - titulo: Abrir portas\n", encoding="utf-8")
    nova = Loja.carregar(tmp_path, "x")
    assert nova.tipo_por_comando("fechar") == "fechamento"
    assert nova.tipo_por_comando("abrir") == "abertura"
    assert nova.tipo_por_comando("nada") is None
    assert [t for t, _ in nova.validar()] == ["quebrado"]


def test_lojas_reais_carregam_sem_erro():
    """Rede de segurança para edições dos YAMLs de produção (lojas/): carregam e têm etapas.
    Os demais testes usam tests/fixtures, para não quebrar quando o checklist real muda."""
    from conftest import RAIZ
    from nucleo.loja import Loja
    loja = Loja.carregar(RAIZ / "lojas", "divino-fogao")
    for tipo in loja.tipos_disponiveis():
        assert loja.checklist(tipo).etapas, tipo

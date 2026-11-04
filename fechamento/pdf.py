"""Geração de PDFs: relatório com fotos e lista de checklist para impressão."""
from __future__ import annotations

import io
from datetime import date, datetime
from pathlib import Path

from PIL import Image as PILImage
from PIL import ImageOps
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Flowable, HRFlowable, Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table,
    TableStyle,
)
from xml.sax.saxutils import escape

from .checklist import FOTO_OBRIGATORIA, FOTO_OPCIONAL, Checklist
from .loja import Loja
from .relatorio import ROTULO, data_br, dia_semana, hora
from .sessao import Sessao, Status

VERDE, VERMELHO = colors.HexColor("#1e7e34"), colors.HexColor("#c62828")
CINZA, AMBAR = colors.HexColor("#757575"), colors.HexColor("#b26a00")
ESCURO, CLARO = colors.HexColor("#333333"), colors.HexColor("#f4f4f4")
COR_STATUS = {
    Status.CONCLUIDO: VERDE, Status.PROBLEMA: VERMELHO,
    Status.NAO_SE_APLICA: CINZA, Status.NAO_REALIZADO: AMBAR,
}
MARGEM = 1.8 * cm
LARGURA = A4[0] - 2 * MARGEM

_base = getSampleStyleSheet()["Normal"]


def _st(name: str, **kw) -> ParagraphStyle:
    return ParagraphStyle(name, parent=_base, fontName=kw.pop("fontName", "Helvetica"), **kw)


S_SUB = _st("sub", fontSize=9, textColor=CINZA, alignment=TA_CENTER, leading=12)
S_CELL = _st("cell", fontSize=9, leading=12)
S_CELL_B = _st("cellb", fontSize=9, leading=12, fontName="Helvetica-Bold")
S_H2 = _st("h2", fontSize=12, leading=16, fontName="Helvetica-Bold")
S_SEC = _st("sec", fontSize=11, leading=14, fontName="Helvetica-Bold", textColor=colors.white)
S_ETAPA = _st("etapa", fontSize=10, leading=13, fontName="Helvetica-BoldOblique")
S_DIR = _st("dir", fontSize=9, leading=13, alignment=TA_RIGHT, fontName="Helvetica-Bold")
S_FOTO = _st("foto", fontSize=7, textColor=CINZA, leading=9)
S_OBS = _st("obs", fontSize=8.5, leading=11)
S_PEQ = _st("peq", fontSize=7.5, leading=9, textColor=CINZA)
FUNDO_ALERTA = colors.HexColor("#fdecea")
S_NAO_REALIZADA = _st("naorealizada", fontSize=8.5, leading=11, textColor=VERMELHO)
S_ALERTA = _st("alerta", fontSize=9.5, leading=13, fontName="Helvetica-Bold", textColor=VERMELHO,
               alignment=TA_CENTER)


def _p(texto: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(texto), style)


def _logo(loja: Loja, largura: float = 6 * cm) -> Flowable | None:
    if not loja.logo:
        return None
    w, h = PILImage.open(loja.logo).size
    img = Image(str(loja.logo), width=largura, height=largura * h / w)
    img.hAlign = "CENTER"
    return img


def _cabecalho(loja: Loja, titulo: str) -> list[Flowable]:
    out: list[Flowable] = [Spacer(1, 0.2 * cm)]
    logo = _logo(loja)
    if logo:
        out += [logo, Spacer(1, 0.3 * cm)]
    out += [
        _p(titulo, S_SUB), _p(loja.local, S_SUB), Spacer(1, 0.2 * cm),
        HRFlowable(width="100%", color=colors.HexColor("#cccccc"), thickness=0.6),
        Spacer(1, 0.3 * cm),
    ]
    return out


def _grade_info(pares: list[tuple[str, str]]) -> Table:
    """Tabela de 4 colunas (rótulo, valor, rótulo, valor)."""
    linhas = []
    for i in range(0, len(pares), 2):
        a, b = pares[i], pares[i + 1] if i + 1 < len(pares) else ("", "")
        linhas.append([_p(a[0], S_CELL_B), _p(a[1], S_CELL), _p(b[0], S_CELL_B), _p(b[1], S_CELL)])
    t = Table(linhas, colWidths=[2.4 * cm, LARGURA / 2 - 2.4 * cm] * 2)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("BACKGROUND", (0, 0), (0, -1), CLARO), ("BACKGROUND", (2, 0), (2, -1), CLARO),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _painel(contagem: dict[Status, int]) -> Table:
    itens = [
        (Status.CONCLUIDO, "Concluídas"), (Status.PROBLEMA, "Com problema"),
        (Status.NAO_SE_APLICA, "Não se aplica"), (Status.NAO_REALIZADO, "Não realizadas"),
    ]
    celulas = []
    for st, rot in itens:
        num = _st(f"n{st.value}", fontSize=18, leading=22, alignment=TA_CENTER,
                  fontName="Helvetica-Bold", textColor=COR_STATUS[st])
        celulas.append([_p(str(contagem[st]), num), _p(rot, _st("r", fontSize=8, leading=10,
                        alignment=TA_CENTER, textColor=CINZA))])
    t = Table([[Table([c[0:1], c[1:2]]) for c in celulas]], colWidths=[LARGURA / 4] * 4)
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _barra_secao(nome: str) -> Table:
    t = Table([[_p(nome, S_SEC)]], colWidths=[LARGURA])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ESCURO),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


COL = LARGURA / 2  # largura de cada coluna (duas etapas lado a lado)
CEL = COL - 0.35 * cm  # largura útil dentro da coluna
# Fotos grandes o bastante para enxergar um problema no relatório: cada uma ocupa cerca de 1/4 da
# área útil da página (a coluna tem ~8,7 cm; uma foto em pé de celular fica com ~8,4 x 11 cm).
ALTURA_MAX_FOTO = 12 * cm
ALTURA_MAX_FOTOS_ETAPA = 21 * cm  # várias fotos numa etapa encolhem para a linha caber na página
_ESPACO_FOTO = 8  # pt entre fotos lado a lado
_ALTURA_LEGENDA = 12  # pt: "Foto às HH:MM" + respiros da tabela
_LARGURA_INDISPONIVEL, _ALTURA_INDISPONIVEL = 2.5 * cm, 12


def _carregar_foto(caminho: Path) -> tuple[io.BytesIO, float] | None:
    """Foto reduzida (em memória) para não inflar o PDF e a proporção largura/altura.

    1000 px no lado maior bastam para ~12 cm a 200 dpi. None se a foto não abrir.
    """
    try:
        with PILImage.open(caminho) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            im.thumbnail((1000, 1000))
            w, h = im.size
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=80)
        buf.seek(0)
        return buf, w / h
    except Exception:  # foto apagada/corrompida
        return None


def _tamanho_foto(proporcao: float | None, altura_max: float) -> tuple[float, float]:
    if proporcao is None:
        return _LARGURA_INDISPONIVEL, _ALTURA_INDISPONIVEL
    largura = min(altura_max * proporcao, CEL - _ESPACO_FOTO)
    return largura, largura / proporcao


def _distribuir(proporcoes: list[float | None], altura_max: float):
    """Fotos em linhas que cabem na coluna: ([[(índice, largura, altura)]], altura total)."""
    linhas: list[list[tuple[int, float, float]]] = []
    usado = 0.0
    for i, prop in enumerate(proporcoes):
        larg, alt = _tamanho_foto(prop, altura_max)
        if not linhas or usado + larg + _ESPACO_FOTO > CEL:
            linhas.append([])
            usado = 0.0
        linhas[-1].append((i, larg, alt))
        usado += larg + _ESPACO_FOTO
    total = sum(max(a for _, _, a in lin) + _ALTURA_LEGENDA for lin in linhas)
    return linhas, total


def _linhas_fotos(resp, base: Path) -> list[Flowable]:
    """Fotos (com a hora embaixo) distribuídas em linhas que cabem na coluna."""
    fotos = [_carregar_foto(base / f.caminho) for f in resp.fotos]
    props = [f[1] if f else None for f in fotos]
    altura = ALTURA_MAX_FOTO
    linhas, total = _distribuir(props, altura)
    while total > ALTURA_MAX_FOTOS_ETAPA and altura > 2 * cm:  # muitas fotos: encolhe
        altura *= 0.9
        linhas, total = _distribuir(props, altura)
    out: list[Flowable] = []
    for lote in linhas:
        corpos, legendas, larguras = [], [], []
        for i, larg, alt in lote:
            corpos.append(Image(fotos[i][0], width=larg, height=alt) if fotos[i]
                          else _p("(foto indisponível)", S_FOTO))
            legendas.append(_p(f"Foto às {hora(resp.fotos[i].hora)}", S_FOTO))
            larguras.append(larg + _ESPACO_FOTO)
        t = Table([corpos, legendas], hAlign="LEFT", colWidths=larguras)
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), _ESPACO_FOTO),
            ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]))
        out.append(t)
    return out


def _celula_etapa(cl: Checklist, s: Sessao, idx: int, base: Path) -> Table:
    etapa, st = cl.etapas[idx], s.status_da_etapa(idx)
    cor = COR_STATUS[st]
    resp = s.respostas.get(idx)
    hexcor = "#" + cor.hexval()[2:]
    dir_txt = f'<font color="{hexcor}">{ROTULO[st]}</font>'
    if resp and resp.fechada:
        dir_txt += f" · {hora(resp.hora)}"
    cab = Table([[_p(f"{idx + 1}. {etapa.titulo}", S_ETAPA), Paragraph(dir_txt, S_DIR)]],
                colWidths=[CEL * 0.58, CEL * 0.42])
    cab.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 0.9, cor), ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    linhas: list[list[Flowable]] = [[cab]]
    if resp:
        linhas += [[f] for f in _linhas_fotos(resp, base)]
        obs = [o for o in resp.obs if o]
        if obs:
            linhas.append([Paragraph(
                f"<b>Obs.</b> ({hora(resp.hora)}): {escape(' / '.join(obs))}", S_OBS)])
        elif resp.fechada and not resp.fotos and resp.status is Status.CONCLUIDO:
            linhas.append([_p("Confirmado, sem foto.", S_FOTO)])
    t = Table(linhas, colWidths=[CEL])
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    return t


def _linhas_etapas(cl: Checklist, s: Sessao, indices: list[int], base: Path) -> list[Table]:
    """Etapas em grade de 2 colunas; cada linha da grade nunca quebra entre páginas."""
    cels = [_celula_etapa(cl, s, i, base) for i in indices]
    linhas = []
    for k in range(0, len(cels), 2):
        par = cels[k:k + 2] + [""] * (2 - len(cels[k:k + 2]))
        t = Table([par], colWidths=[COL, COL])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0.35 * cm),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        linhas.append(t)
    return linhas


class _Rodape:
    def __init__(self, esquerda: str):
        self.esquerda = esquerda

    def __call__(self, canv, doc) -> None:
        canv.saveState()
        canv.setFont("Helvetica", 7.5)
        canv.setFillColor(CINZA)
        canv.drawString(MARGEM, 1.1 * cm, self.esquerda)
        canv.drawRightString(A4[0] - MARGEM, 1.1 * cm, f"Página {doc.page}")
        canv.restoreState()


def _doc(destino: Path, titulo: str) -> SimpleDocTemplate:
    return SimpleDocTemplate(
        str(destino), pagesize=A4, title=titulo, author="Bot de checklists",
        leftMargin=MARGEM, rightMargin=MARGEM, topMargin=1.4 * cm, bottomMargin=1.8 * cm,
    )


def gerar_relatorio_pdf(
    loja: Loja, cl: Checklist, s: Sessao, base_fotos: Path, destino: Path,
    gerado_em: datetime | None = None,
) -> Path:
    """Relatório completo (com miniaturas das fotos) de um checklist finalizado."""
    gerado_em = gerado_em or loja.agora()
    titulo = f"Relatório de {cl.nome}"
    fluxo = _cabecalho(loja, titulo)
    fluxo.append(_grade_info([
        ("Data", data_br(s.data)), ("Responsável", s.responsavel),
        ("Início", hora(s.iniciado_em)), ("Término", hora(s.finalizado_em)),
        ("Duração", f"{s.duracao_min()} min"), ("Fotos registradas", str(s.total_fotos())),
    ]))
    fluxo += [Spacer(1, 0.3 * cm), _painel(s.contagem(cl)), Spacer(1, 0.3 * cm)]

    problemas, pendentes = s.problemas(cl), s.nao_realizadas(cl)
    if problemas or pendentes:
        fluxo.append(_p("Atenção: pendências e problemas",
                        _st("att", fontSize=12, leading=16, fontName="Helvetica-Bold",
                            textColor=VERMELHO)))
        linhas = []
        for i, r in problemas:
            obs = " / ".join(o for o in r.obs if o) or "(sem descrição)"
            linhas.append([Paragraph(f"<b>{escape(cl.etapas[i].titulo)}</b> - {escape(obs)}", S_CELL)])
        for i in pendentes:
            linhas.append([Paragraph(f"<b>{escape(cl.etapas[i].titulo)}</b> - não realizada", S_CELL)])
        t = Table(linhas, colWidths=[LARGURA])
        t.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.8, VERMELHO),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff3f3")),
        ]))
        fluxo += [t, Spacer(1, 0.3 * cm)]

    titulo_det = [_p("Detalhamento por etapa", S_H2), Spacer(1, 0.15 * cm)]
    for nome, etapas in cl.secoes():
        linhas = _linhas_etapas(cl, s, [i for i, _ in etapas], base_fotos)
        # o título (e a barra da seção) sempre acompanha pelo menos a primeira linha de etapas
        cabeca = titulo_det + ([_barra_secao(nome)] if nome else []) + linhas[:1]
        titulo_det = []
        fluxo.append(KeepTogether(cabeca))
        fluxo += linhas[1:]
    fluxo += [
        Spacer(1, 0.4 * cm),
        HRFlowable(width="100%", color=colors.HexColor("#cccccc"), thickness=0.6),
        _p(f"Relatório gerado automaticamente em {gerado_em:%d/%m/%Y %H:%M}.", S_PEQ),
    ]
    rodape = _Rodape(f"{loja.nome} · {cl.nome} {data_br(s.data)} · {s.responsavel}")
    _doc(destino, titulo).build(fluxo, onFirstPage=rodape, onLaterPages=rodape)
    return destino


# ---------------------------------------------------------------- lista para impressão
class _Caixa(Flowable):
    """Quadradinho de marcação; com X quando marcado."""

    def __init__(self, marcado: bool = False, lado: float = 0.42 * cm):
        super().__init__()
        self.marcado, self.lado = marcado, lado
        self.width = self.height = lado
        self.hAlign = "CENTER"

    def draw(self) -> None:
        c, l = self.canv, self.lado
        c.setLineWidth(0.9)
        c.setStrokeColor(colors.black)
        c.rect(0, 0, l, l)
        if self.marcado:
            c.setLineWidth(1.6)
            c.line(0.07 * l, 0.07 * l, 0.93 * l, 0.93 * l)
            c.line(0.07 * l, 0.93 * l, 0.93 * l, 0.07 * l)


def gerar_lista_pdf(
    loja: Loja, cl: Checklist, s: Sessao | None, destino: Path,
) -> Path:
    """Lista de checklist para imprimir: vazia (s=None) ou preenchida com o resultado."""
    d = cl.data or date.today()
    preenchida = s is not None
    titulo = f"{cl.nome} - {'Resultado' if preenchida else 'Lista para impressão'}"
    fluxo = _cabecalho(loja, titulo)
    if preenchida:
        info = [
            ("Data", f"{data_br(d)} ({dia_semana(d)})"), ("Responsável", s.responsavel),
            ("Início", hora(s.iniciado_em)), ("Término", hora(s.finalizado_em)),
        ]
    else:
        info = [
            ("Data", f"{data_br(d)} ({dia_semana(d)})"), ("Responsável", "_" * 28),
            ("Início", "____:____"), ("Término", "____:____"),
        ]
    fluxo += [_grade_info(info), Spacer(1, 0.4 * cm)]
    if preenchida:
        faltaram = len(s.nao_realizadas(cl))
        if faltaram:
            fluxo += [Paragraph(
                f"ATENÇÃO: {faltaram} de {len(cl.etapas)} etapas NÃO foram realizadas "
                "(destacadas em vermelho).", S_ALERTA), Spacer(1, 0.4 * cm)]

    larg = [0.9 * cm, 6.6 * cm, 1.5 * cm, 1.5 * cm, 1.4 * cm]
    larg.append(LARGURA - sum(larg))
    cab_col = [_p(t, _st("th", fontSize=7.5, leading=9, fontName="Helvetica-Bold",
                         alignment=TA_CENTER)) for t in ("Nº", "Etapa", "Concl.", "Probl.", "N/A", "Obs. / hora")]
    for nome, etapas in cl.secoes():
        linhas = [[_p(nome or "ETAPAS", S_SEC), "", "", "", "", ""], cab_col]
        destacadas = []  # linhas da tabela de etapas sem resposta (preenchida), em destaque
        for i, e in etapas:
            r = s.respostas.get(i) if s else None
            st = r.status if r and r.fechada else None
            tag = ""
            titulo_et = f"<b>{escape(e.titulo)}</b><font size=7 color='#757575'>{escape(tag)}</font>"
            if e.instrucao:
                titulo_et += f"<br/><font size=7 color='#757575'>{escape(e.instrucao)}</font>"
            obs_txt = ""
            if r and r.fechada:
                obs_txt = hora(r.hora)
                obs = " / ".join(o for o in r.obs if o)
                if obs:
                    obs_txt += " - " + obs
            obs_cel = _p(obs_txt, S_OBS)
            if preenchida and st is None:  # ignorada ou fechamento encerrado antes de chegar nela
                destacadas.append(len(linhas))
                obs_cel = Paragraph("<b>NÃO REALIZADA</b>", S_NAO_REALIZADA)
            linhas.append([
                _p(str(i + 1), _st("n", fontSize=9, alignment=TA_CENTER)),
                Paragraph(titulo_et, S_CELL),
                _Caixa(st is Status.CONCLUIDO), _Caixa(st is Status.PROBLEMA),
                _Caixa(st is Status.NAO_SE_APLICA),
                obs_cel,
            ])
        t = Table(linhas, colWidths=larg, repeatRows=2)
        t.setStyle(TableStyle([
            ("SPAN", (0, 0), (-1, 0)), ("BACKGROUND", (0, 0), (-1, 0), ESCURO),
            ("BACKGROUND", (0, 1), (-1, 1), CLARO),
            ("GRID", (0, 1), (-1, -1), 0.5, colors.HexColor("#999999")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 2), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
            ("TOPPADDING", (0, 2), (-1, -1), 7), ("BOTTOMPADDING", (0, 2), (-1, -1), 7),
        ]))
        for lin in destacadas:  # depois do zebrado, para prevalecer sobre ele
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, lin), (-1, lin), FUNDO_ALERTA),
                ("BOX", (0, lin), (-1, lin), 1.2, VERMELHO),
            ]))
        fluxo += [t, Spacer(1, 0.4 * cm)]
    fluxo += [
        Spacer(1, 0.3 * cm),
        _p("Assinatura do responsável: " + "_" * 40, S_CELL),
        Spacer(1, 0.2 * cm),
        _p("Legenda: Concl. = concluído · Probl. = com problema (descrever em Obs.) · "
           "N/A = não se aplica" + (" · Linha em vermelho = etapa não realizada"
                                    if preenchida else ""), S_PEQ),
    ]
    rodape = _Rodape(f"{loja.nome} · {cl.nome} · {data_br(d)}")
    _doc(destino, titulo).build(fluxo, onFirstPage=rodape, onLaterPages=rodape)
    return destino

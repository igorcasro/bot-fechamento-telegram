"""Textos de relatório/acompanhamento (resumo para Telegram/WhatsApp e progresso do dia)."""
from __future__ import annotations

from datetime import date, datetime

from .checklist import DIAS_SEMANA_LONGO, Checklist
from .loja import Loja
from .sessao import Sessao, Status

ICONE = {
    Status.CONCLUIDO: "✅", Status.PROBLEMA: "⚠️",
    Status.NAO_SE_APLICA: "➖", Status.NAO_REALIZADO: "⏳",
}
ROTULO = {
    Status.CONCLUIDO: "CONCLUÍDO", Status.PROBLEMA: "PROBLEMA",
    Status.NAO_SE_APLICA: "NÃO SE APLICA", Status.NAO_REALIZADO: "NÃO REALIZADO",
}


def hora(iso: str | None) -> str:
    return datetime.fromisoformat(iso).strftime("%H:%M") if iso else "--:--"


def data_br(d: date | str) -> str:
    d = date.fromisoformat(d) if isinstance(d, str) else d
    return d.strftime("%d/%m/%Y")


def dia_semana(d: date) -> str:
    return DIAS_SEMANA_LONGO[d.weekday()]


def resumo_texto(loja: Loja, cl: Checklist, s: Sessao) -> str:
    """Resumo em texto puro (serve para Telegram e, depois, WhatsApp)."""
    c = s.contagem(cl)
    linhas = [
        f"📋 {cl.nome} - {loja.nome}",
        f"📅 {data_br(s.data)} ({dia_semana(date.fromisoformat(s.data))})",
        f"👤 Responsável: {s.responsavel}",
        f"🕐 {hora(s.iniciado_em)} às {hora(s.finalizado_em)} ({s.duracao_min()} min)"
        f" · 📸 {s.total_fotos()} foto(s)",
        "",
        f"✅ {c[Status.CONCLUIDO]} concluídas · ⚠️ {c[Status.PROBLEMA]} com problema",
        f"➖ {c[Status.NAO_SE_APLICA]} não se aplica · ⏳ {c[Status.NAO_REALIZADO]} não realizadas",
    ]
    problemas = s.problemas(cl)
    pendentes = s.nao_realizadas(cl)
    if problemas or pendentes:
        linhas += ["", "🚨 Atenção:"]
        for i, r in problemas:
            obs = " / ".join(o for o in r.obs if o) or "(sem descrição)"
            linhas.append(f"⚠️ {cl.etapas[i].titulo} - {obs}")
        for i in pendentes:
            linhas.append(f"⏳ {cl.etapas[i].titulo} - não realizada")
    else:
        linhas += ["", "Tudo certo, nenhuma pendência. 👏"]
    return "\n".join(linhas)


def progresso_texto(cl: Checklist, s: Sessao | None) -> str:
    """Lista do dia por seção, com ✅/⚠️/➖ e ⏳ para o que falta."""
    d = cl.data
    cab = f"📋 {cl.nome}"
    if d:
        cab += f" - {dia_semana(d)}, {data_br(d)}"
    linhas = [cab]
    if s is not None:
        c = s.contagem(cl)
        feitas = len(cl.etapas) - c[Status.NAO_REALIZADO]
        linhas.append(f"Progresso: {feitas}/{len(cl.etapas)} · 👤 {s.responsavel}")
    else:
        linhas.append(f"Nada registrado ainda · {len(cl.etapas)} etapa(s)")
    for nome, etapas in cl.secoes():
        linhas += ["", f"{nome}" if nome else "ETAPAS"]
        for i, e in etapas:
            st = s.status_da_etapa(i) if s else Status.NAO_REALIZADO
            extra = ""
            if s and st is not Status.NAO_REALIZADO:
                extra = f" ({hora(s.respostas[i].hora)})"
            linhas.append(f"{ICONE[st]} {i + 1}. {e.titulo}{extra}")
    return "\n".join(linhas)

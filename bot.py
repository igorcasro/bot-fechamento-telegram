"""Bot do Telegram para os checklists do restaurante (fechamento, abertura, ...).

Fluxo: /fechar -> o bot mostra uma etapa por vez com botões (Concluído / Problema /
Não se aplica), pede foto e observação quando preciso e, no fim, envia ao grupo do
gerente um resumo em texto + o relatório em PDF.
"""
from __future__ import annotations

import asyncio
import html
import logging
import os
from dataclasses import dataclass, field
from datetime import date, datetime
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler,
    PersistenceInput, PicklePersistence, filters,
)

from fechamento.arquivo import Arquivo
from fechamento.checklist import FOTO_NENHUMA, FOTO_OBRIGATORIA, Checklist
from fechamento.entrega import CanalEntrega
from fechamento.loja import Loja
from fechamento.pdf import gerar_lista_pdf, gerar_relatorio_pdf
from fechamento.relatorio import ICONE, ROTULO, data_br, progresso_texto, resumo_texto
from fechamento.sessao import EstadoInvalido, Sessao, Status

BASE_DIR = Path(__file__).parent
log = logging.getLogger("checklist-bot")

# comando -> tipo de checklist (arquivo lojas/<loja>/checklists/<tipo>.yaml)
COMANDOS_INICIO = {"fechar": "fechamento", "abrir": "abertura"}
STATUS_BOTAO = {"c": Status.CONCLUIDO, "p": Status.PROBLEMA, "n": Status.NAO_SE_APLICA}


# ------------------------------------------------------------------ contexto
class TelegramEntrega:
    """Entrega o resumo e o PDF em um chat/grupo do Telegram."""

    nome = "telegram"

    def __init__(self, bot, chat_id: str):
        self.bot, self.chat_id = bot, chat_id

    async def enviar(self, resumo: str, pdf: Path) -> None:
        await self.bot.send_message(self.chat_id, resumo)
        with pdf.open("rb") as f:
            await self.bot.send_document(
                self.chat_id, document=f, filename=pdf.name, caption="📄 Relatório em PDF"
            )


@dataclass
class Contexto:
    loja: Loja
    arquivo: Arquivo
    gerente_chat: str | None = None
    permitidos: set[int] = field(default_factory=set)
    retencao_dias: int = 7
    canais: list[CanalEntrega] = field(default_factory=list)

    @classmethod
    def do_ambiente(cls) -> "Contexto":
        loja = Loja.carregar(os.getenv("LOJAS_DIR", BASE_DIR / "lojas"),
                             os.getenv("LOJA", "divino-fogao"))
        arquivo = Arquivo(Path(os.getenv("ARCHIVE_DIR", BASE_DIR / "arquivo")) / loja.id)
        permitidos = {int(x) for x in os.getenv("ALLOWED_USER_IDS", "").replace(" ", "").split(",") if x}
        return cls(
            loja=loja, arquivo=arquivo, gerente_chat=os.getenv("MANAGER_CHAT_ID") or None,
            permitidos=permitidos, retencao_dias=int(os.getenv("RETENCAO_DIAS", "7")),
        )


def ctx_de(context: ContextTypes.DEFAULT_TYPE) -> Contexto:
    return context.application.bot_data["ctx"]


def somente_autorizados(fn):
    @wraps(fn)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        ctx = ctx_de(context)
        if ctx.permitidos and update.effective_user.id not in ctx.permitidos:
            if update.callback_query:
                await update.callback_query.answer("Sem permissão.", show_alert=True)
            else:
                await update.effective_message.reply_text(
                    "Você não tem permissão para usar este bot.")
            return
        return await fn(update, context)
    return wrapper


# ------------------------------------------------------------------- sessão
def get_sessao(context: ContextTypes.DEFAULT_TYPE) -> Sessao | None:
    raw = context.chat_data.get("sessao")
    return Sessao.from_dict(raw) if raw else None


def save_sessao(context: ContextTypes.DEFAULT_TYPE, s: Sessao | None) -> None:
    if s is None:
        context.chat_data.pop("sessao", None)
    else:
        context.chat_data["sessao"] = s.to_dict()


def checklist_da_sessao(ctx: Contexto, s: Sessao) -> Checklist:
    return ctx.loja.checklist(s.tipo).para_data(date.fromisoformat(s.data))


# ------------------------------------------------------------------- textos
def h(t: str) -> str:
    return html.escape(t)


def texto_etapa(cl: Checklist, s: Sessao) -> str:
    i = s.etapa_atual
    e = cl.etapas[i]
    if e.foto == FOTO_OBRIGATORIA:
        foto = f"📸 Foto obrigatória ({e.fotos})" if e.fotos > 1 else "📸 Foto obrigatória"
    elif e.foto == FOTO_NENHUMA:
        foto = "Não precisa de foto"
    else:
        foto = "📸 Foto opcional"
    linhas = [f"<b>{h(e.secao)}</b> · etapa {i + 1}/{len(cl.etapas)}" if e.secao
              else f"Etapa {i + 1}/{len(cl.etapas)}", f"<b>{h(e.titulo)}</b>"]
    if e.instrucao:
        linhas.append(h(e.instrucao))
    linhas += ["", foto]
    return "\n".join(linhas)


def teclado_status(cl: Checklist, idx: int) -> InlineKeyboardMarkup:
    linha1 = [InlineKeyboardButton("✅ Concluído", callback_data=f"st:{idx}:c"),
              InlineKeyboardButton("⚠️ Problema", callback_data=f"st:{idx}:p")]
    linhas = [linha1]
    if cl.etapas[idx].nao_se_aplica:
        linhas.append([InlineKeyboardButton("➖ Não se aplica", callback_data=f"st:{idx}:n")])
    return InlineKeyboardMarkup(linhas)


def teclado_continuar(idx: int, rotulo: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(rotulo, callback_data=f"ct:{idx}")]])


async def enviar_longo(msg, texto: str) -> None:
    """Divide em mensagens de até ~3500 caracteres (limite do Telegram: 4096)."""
    bloco = ""
    for linha in texto.split("\n"):
        if len(bloco) + len(linha) + 1 > 3500:
            await msg.reply_text(bloco)
            bloco = ""
        bloco += linha + "\n"
    if bloco.strip():
        await msg.reply_text(bloco)


# ------------------------------------------------------------------- fluxo
async def seguir(msg, context: ContextTypes.DEFAULT_TYPE, s: Sessao, cl: Checklist) -> None:
    """Salva a sessão e mostra o próximo passo conforme a fase atual."""
    fase = s.fase(cl)
    if fase == "fim":
        await finalizar(msg, context, s, cl)
        return
    save_sessao(context, s)
    i = s.etapa_atual
    if fase == "status":
        await msg.reply_html(texto_etapa(cl, s), reply_markup=teclado_status(cl, i))
    elif fase == "foto":
        e = cl.etapas[i]
        falta = s.fotos_faltando(cl)
        txt = f"📸 Envie {'a foto' if e.fotos == 1 else f'{falta} foto(s)'} desta etapa."
        if e.foto != FOTO_OBRIGATORIA:
            await msg.reply_text(txt + "\n(opcional)",
                                 reply_markup=teclado_continuar(i, "Continuar sem foto ➡️"))
        else:
            await msg.reply_text(txt)
    else:  # problema
        await msg.reply_text(
            "⚠️ Descreva o problema em texto e/ou envie foto.\n"
            "Quando terminar, toque em Continuar.",
            reply_markup=teclado_continuar(i, "Continuar ➡️"))


async def iniciar(update: Update, context: ContextTypes.DEFAULT_TYPE, tipo: str) -> None:
    ctx, msg = ctx_de(context), update.effective_message
    if get_sessao(context):
        await msg.reply_text("Já existe um checklist em andamento. Use /status, /finalizar ou /cancelar.")
        return
    try:
        base = ctx.loja.checklist(tipo)
    except FileNotFoundError:
        disp = ", ".join(ctx.loja.tipos_disponiveis()) or "nenhum"
        await msg.reply_text(f"O checklist '{tipo}' ainda não está configurado. Disponíveis: {disp}.")
        return
    agora = ctx.loja.agora()
    cl = base.para_data(agora.date())
    if not cl.etapas:
        await msg.reply_text(f"Não há etapas de {tipo} para hoje ({data_br(agora.date())}).")
        return
    ctx.arquivo.limpar_antigos(agora.date(), ctx.retencao_dias)
    s = Sessao.nova(cl, update.effective_user.full_name, agora)
    await msg.reply_html(f"Vamos começar: <b>{h(cl.nome)}</b> - {data_br(cl.data)} "
                         f"({len(cl.etapas)} etapas) 🔒")
    await seguir(msg, context, s, cl)


@somente_autorizados
async def cmd_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    comando = update.effective_message.text.split()[0].lstrip("/").split("@")[0].lower()
    await iniciar(update, context, COMANDOS_INICIO[comando])


@somente_autorizados
async def cmd_iniciar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        disp = ", ".join(ctx_de(context).loja.tipos_disponiveis())
        await update.effective_message.reply_text(f"Uso: /iniciar <tipo>. Disponíveis: {disp}.")
        return
    await iniciar(update, context, context.args[0].lower())


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Olá! Eu guio os checklists do restaurante.\n\n"
        "/fechar - fechamento da loja\n/abrir - abertura da loja\n"
        "/status - ver a etapa atual\n/finalizar - encerrar com o que já foi feito\n"
        "/cancelar - cancelar o checklist atual\n\n"
        "Acompanhamento e impressão:\n"
        "/hoje [tipo] - o que foi feito / falta fazer hoje\n"
        "/dia <data> [tipo] - o mesmo para outro dia (ex.: /dia 05/11)\n"
        "/imprimir [data] [tipo] - lista vazia em PDF para imprimir\n"
        "/resultado [data] [tipo] - lista preenchida em PDF\n"
        "/reenviar [data] [tipo] - reenvia o relatório ao gerente\n\n"
        f"Seu ID: {update.effective_user.id}"
    )


@somente_autorizados
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    s, msg = get_sessao(context), update.effective_message
    if not s:
        await msg.reply_text("Nenhum checklist em andamento. Use /fechar ou /abrir.")
        return
    await seguir(msg, context, s, checklist_da_sessao(ctx_de(context), s))


@somente_autorizados
async def cmd_cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if get_sessao(context):
        save_sessao(context, None)
        await update.effective_message.reply_text("Checklist cancelado. Use /fechar para recomeçar.")
    else:
        await update.effective_message.reply_text("Nenhum checklist em andamento.")


@somente_autorizados
async def cmd_finalizar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    s, msg = get_sessao(context), update.effective_message
    if not s:
        await msg.reply_text("Nenhum checklist em andamento.")
        return
    cl = checklist_da_sessao(ctx_de(context), s)
    restantes = len(cl.etapas) - s.etapa_atual
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Sim, finalizar", callback_data="fin:s"),
                                InlineKeyboardButton("Não", callback_data="fin:n")]])
    await msg.reply_text(
        f"Finalizar agora? {restantes} etapa(s) sem resposta serão marcadas como NÃO REALIZADAS.",
        reply_markup=kb)


@somente_autorizados
async def botao(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    ctx, msg = ctx_de(context), q.message
    partes = q.data.split(":")
    s = get_sessao(context)
    if not s:
        await q.answer("Este checklist não está mais em andamento.", show_alert=True)
        await q.edit_message_reply_markup(None)
        return
    cl = checklist_da_sessao(ctx, s)

    if partes[0] == "fin":
        await q.answer()
        await q.edit_message_reply_markup(None)
        if partes[1] == "s":
            await finalizar(msg, context, s, cl, antecipado=True)
        return

    idx = int(partes[1])
    if idx != s.etapa_atual:
        await q.answer("Essa etapa já foi respondida.", show_alert=True)
        await q.edit_message_reply_markup(None)
        return
    agora = ctx.loja.agora()
    try:
        if partes[0] == "st":
            status = STATUS_BOTAO[partes[2]]
            s.responder(cl, status, agora)
            marcado = f"{ICONE[status]} {ROTULO[status].capitalize()}"
        else:  # "ct"
            s.continuar(cl)
            marcado = "➡️ Continuando"
    except (PermissionError, EstadoInvalido) as exc:
        await q.answer(str(exc), show_alert=True)
        return
    await q.answer()
    await q.edit_message_text(f"{q.message.text_html}\n\n<b>{h(marcado)}</b>",
                              parse_mode=ParseMode.HTML)
    await seguir(msg, context, s, cl)


@somente_autorizados
async def foto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ctx, msg = ctx_de(context), update.effective_message
    s = get_sessao(context)
    if not s or s.encerrada:
        await msg.reply_text("Nenhum checklist em andamento. Use /fechar ou /abrir.")
        return
    cl = checklist_da_sessao(ctx, s)
    gid = msg.media_group_id
    continuacao = s.etapa_destino(gid) != s.etapa_atual
    if not continuacao and s.resposta_atual(cl) is None:
        await msg.reply_text("Antes da foto, escolha o status da etapa nos botões 👆")
        return

    agora = ctx.loja.agora()
    idx = s.etapa_destino(gid)
    existentes = len(s.respostas[idx].fotos) if idx in s.respostas else 0
    rel, destino = ctx.arquivo.caminho_foto(s, idx, existentes + 1, f"{agora:%H%M%S}")
    arq = await msg.photo[-1].get_file()
    await arq.download_to_drive(destino)
    await asyncio.to_thread(Arquivo.reduzir_foto, destino)

    try:
        idx, fechou = s.add_foto(cl, rel, agora, legenda=msg.caption, media_group_id=gid)
    except EstadoInvalido as exc:
        await msg.reply_text(str(exc))
        return
    if fechou:
        await msg.reply_text("✅ Etapa registrada!")
        await seguir(msg, context, s, cl)
        return
    save_sessao(context, s)
    if idx != s.etapa_atual:  # sobra de álbum anexada à etapa anterior
        return
    if s.fotos_faltando(cl):
        await msg.reply_text(f"📸 Recebida! Falta(m) {s.fotos_faltando(cl)} foto(s) desta etapa.")
    else:
        await msg.reply_text("📎 Foto anexada. Escreva uma observação ou toque em Continuar.")


@somente_autorizados
async def texto_solto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg, s = update.effective_message, get_sessao(context)
    if not s:
        return
    cl = checklist_da_sessao(ctx_de(context), s)
    try:
        s.add_obs(cl, msg.text)
    except EstadoInvalido:
        await msg.reply_text("Escolha o status da etapa nos botões 👆")
        return
    save_sessao(context, s)
    await msg.reply_text("📝 Observação anotada.")


# ----------------------------------------------------------------- finalizar
def nome_pdf(s: Sessao) -> str:
    return f"{s.tipo}_{s.data}_{datetime.fromisoformat(s.iniciado_em):%H%M}.pdf"


async def finalizar(
    msg, context: ContextTypes.DEFAULT_TYPE, s: Sessao, cl: Checklist, antecipado: bool = False
) -> None:
    ctx = ctx_de(context)
    s.finalizar(cl, ctx.loja.agora())
    save_sessao(context, None)
    ctx.arquivo.salvar_resultado(cl, s)
    pdf = ctx.arquivo.pasta(s) / nome_pdf(s)
    await asyncio.to_thread(gerar_relatorio_pdf, ctx.loja, cl, s, ctx.arquivo.raiz, pdf)
    resumo = resumo_texto(ctx.loja, cl, s)

    falhas = []
    for canal in ctx.canais:
        try:
            await canal.enviar(resumo, pdf)
        except Exception:
            log.exception("Falha ao enviar pelo canal %s", canal.nome)
            falhas.append(canal.nome)
    if not ctx.canais:
        log.warning("Nenhum canal de entrega configurado (MANAGER_CHAT_ID).")

    mesmo_chat = ctx.gerente_chat is not None and str(msg.chat_id) == str(ctx.gerente_chat)
    if not mesmo_chat:
        await msg.reply_text(f"🎉 Checklist concluído!\n\n{resumo}")
    if falhas or not ctx.canais:
        await msg.reply_text("⚠️ O relatório foi salvo, mas não consegui enviá-lo ao gerente. "
                             "Avise o responsável; depois use /reenviar.")
    ctx.arquivo.limpar_antigos(ctx.loja.agora().date(), ctx.retencao_dias)


# ------------------------------------------- acompanhamento, impressão, reenvio
def _data_arg(txt: str, hoje: date) -> date | None:
    """Aceita AAAA-MM-DD, DD/MM/AAAA ou DD/MM (ano atual)."""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(txt, fmt).date()
        except ValueError:
            pass
    try:
        return datetime.strptime(f"{txt}/{hoje.year}", "%d/%m/%Y").date()
    except ValueError:
        return None


def _args(ctx: Contexto, args: list[str]) -> tuple[date, str | None]:
    """Interpreta '[data] [tipo]' em qualquer ordem. Sem data = hoje."""
    hoje = ctx.loja.agora().date()
    d, tipo = hoje, None
    for a in args:
        dd = _data_arg(a, hoje)
        if dd:
            d = dd
        else:
            tipo = a.lower()
    return d, tipo


async def _responder_tipo_invalido(msg, ctx: Contexto, tipo: str | None) -> bool:
    if tipo and tipo not in ctx.loja.tipos_disponiveis():
        await msg.reply_text(f"Tipo '{tipo}' não existe. Disponíveis: "
                             f"{', '.join(ctx.loja.tipos_disponiveis())}.")
        return True
    return False


async def _mostrar_dia(update: Update, context: ContextTypes.DEFAULT_TYPE, args: list[str]) -> None:
    ctx, msg = ctx_de(context), update.effective_message
    d, tipo = _args(ctx, args)
    if await _responder_tipo_invalido(msg, ctx, tipo):
        return
    atual = get_sessao(context)
    for t in ([tipo] if tipo else ctx.loja.tipos_disponiveis()):
        cl = ctx.loja.checklist(t).para_data(d)
        if not cl.etapas:
            await msg.reply_text(f"{t}: sem etapas em {data_br(d)}.")
            continue
        s = atual if atual and atual.tipo == t and atual.data == d.isoformat() else None
        if s is None:
            salvos = ctx.arquivo.resultados(d, t)
            s = salvos[-1][1] if salvos else None
            if salvos:
                cl = salvos[-1][0]  # usa as etapas como estavam naquele dia
        await enviar_longo(msg, progresso_texto(cl, s))


@somente_autorizados
async def cmd_hoje(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _mostrar_dia(update, context, context.args or [])


@somente_autorizados
async def cmd_dia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.effective_message.reply_text("Uso: /dia <data> [tipo]. Ex.: /dia 05/11 fechamento")
        return
    await _mostrar_dia(update, context, context.args)


async def _enviar_pdf(msg, caminho: Path, legenda: str) -> None:
    with caminho.open("rb") as f:
        await msg.reply_document(document=f, filename=caminho.name, caption=legenda)


@somente_autorizados
async def cmd_imprimir(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ctx, msg = ctx_de(context), update.effective_message
    d, tipo = _args(ctx, context.args or [])
    tipo = tipo or "fechamento"
    if await _responder_tipo_invalido(msg, ctx, tipo):
        return
    cl = ctx.loja.checklist(tipo).para_data(d)
    if not cl.etapas:
        await msg.reply_text(f"Sem etapas de {tipo} em {data_br(d)}.")
        return
    destino = ctx.arquivo.raiz / "impressao" / f"{tipo}_{d.isoformat()}_vazio.pdf"
    destino.parent.mkdir(parents=True, exist_ok=True)
    await asyncio.to_thread(gerar_lista_pdf, ctx.loja, cl, None, destino)
    await _enviar_pdf(msg, destino, f"🖨️ {cl.nome} - {data_br(d)} (lista vazia)")


def _ultimo_resultado(ctx: Contexto, d: date, tipo: str | None):
    salvos = ctx.arquivo.resultados(d, tipo)
    return salvos[-1] if salvos else None


@somente_autorizados
async def cmd_resultado(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ctx, msg = ctx_de(context), update.effective_message
    d, tipo = _args(ctx, context.args or [])
    tipo = tipo or "fechamento"
    if await _responder_tipo_invalido(msg, ctx, tipo):
        return
    res = _ultimo_resultado(ctx, d, tipo)
    if not res:
        await msg.reply_text(f"Não há resultado de {tipo} em {data_br(d)} "
                             f"(os dados ficam guardados por {ctx.retencao_dias} dias).")
        return
    cl, s = res
    destino = ctx.arquivo.pasta(s) / f"{tipo}_{s.data}_lista.pdf"
    await asyncio.to_thread(gerar_lista_pdf, ctx.loja, cl, s, destino)
    await _enviar_pdf(msg, destino, f"🖨️ {cl.nome} - {data_br(d)} (preenchida)")


@somente_autorizados
async def cmd_reenviar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ctx, msg = ctx_de(context), update.effective_message
    d, tipo = _args(ctx, context.args or [])
    tipo = tipo or "fechamento"
    if await _responder_tipo_invalido(msg, ctx, tipo):
        return
    res = _ultimo_resultado(ctx, d, tipo)
    if not res:
        await msg.reply_text(f"Não há resultado de {tipo} em {data_br(d)}.")
        return
    cl, s = res
    pdf = ctx.arquivo.pasta(s) / nome_pdf(s)
    if not pdf.exists():
        await asyncio.to_thread(gerar_relatorio_pdf, ctx.loja, cl, s, ctx.arquivo.raiz, pdf)
    if not ctx.canais:
        await msg.reply_text("MANAGER_CHAT_ID não está configurado.")
        return
    for canal in ctx.canais:
        await canal.enviar(resumo_texto(ctx.loja, cl, s), pdf)
    await msg.reply_text("✅ Relatório reenviado.")


# --------------------------------------------------------------------- main
async def erro(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.error("Erro ao tratar update", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("😕 Algo deu errado. Tente de novo ou use /status.")


def build_app(token: str, ctx: Contexto) -> Application:
    persistence = PicklePersistence(
        filepath=BASE_DIR / "estado.pickle",
        store_data=PersistenceInput(bot_data=False, user_data=False, callback_data=False),
    )
    app = Application.builder().token(token).persistence(persistence).build()
    app.bot_data["ctx"] = ctx
    if ctx.gerente_chat:
        ctx.canais.append(TelegramEntrega(app.bot, ctx.gerente_chat))
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler(list(COMANDOS_INICIO), cmd_inicio))
    for nome, fn in [("iniciar", cmd_iniciar), ("status", cmd_status), ("cancelar", cmd_cancelar),
                     ("finalizar", cmd_finalizar), ("hoje", cmd_hoje), ("dia", cmd_dia),
                     ("imprimir", cmd_imprimir), ("resultado", cmd_resultado),
                     ("reenviar", cmd_reenviar)]:
        app.add_handler(CommandHandler(nome, fn))
    app.add_handler(CallbackQueryHandler(botao, pattern=r"^(st|ct|fin):"))
    app.add_handler(MessageHandler(filters.PHOTO, foto))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, texto_solto))
    app.add_error_handler(erro)
    return app


def main() -> None:
    load_dotenv(BASE_DIR / ".env")
    logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise SystemExit("Defina BOT_TOKEN no arquivo .env (veja .env.example).")
    ctx = Contexto.do_ambiente()
    removidos = ctx.arquivo.limpar_antigos(ctx.loja.agora().date(), ctx.retencao_dias)
    if removidos:
        log.info("Arquivo: removidos dias antigos %s", removidos)
    if not ctx.gerente_chat:
        log.warning("MANAGER_CHAT_ID não definido: relatórios não serão enviados.")
    log.info("Loja: %s | checklists: %s", ctx.loja.nome, ", ".join(ctx.loja.tipos_disponiveis()))
    build_app(token, ctx).run_polling()


if __name__ == "__main__":
    main()

"""Bot do Telegram para os checklists do restaurante (fechamento, abertura, ...).

Fluxo: o funcionário usa o bot em CONVERSA PRIVADA (/fechar, /abrir...). A cada etapa o bot
mostra botões (Concluído / Problema / Não se aplica) e pede foto/observação quando preciso.
No fim, o resumo em texto + o PDF (com as fotos) vão para o grupo do gerente. As fotos nunca
são devolvidas na conversa: só aparecem dentro do PDF.
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

from dotenv import dotenv_values, load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatType, ParseMode
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
ENV_ENCODING = "utf-8-sig"  # tolera arquivo salvo com BOM pelo Bloco de Notas
log = logging.getLogger("checklist-bot")

STATUS_BOTAO = {"c": Status.CONCLUIDO, "p": Status.PROBLEMA, "n": Status.NAO_SE_APLICA}


# ------------------------------------------------------------------ contexto
def parse_ids(txt: str) -> set[int]:
    """'111, 222,abc' -> {111, 222} (valores inválidos são ignorados com aviso)."""
    ids = set()
    for parte in txt.replace(";", ",").split(","):
        parte = parte.strip()
        if not parte:
            continue
        try:
            ids.add(int(parte))
        except ValueError:
            log.warning("ALLOWED_USER_IDS: '%s' não é um ID válido (ignorado).", parte)
    return ids


class TelegramEntrega:
    """Entrega o resumo e o PDF no grupo/chat do gerente (MANAGER_CHAT_ID)."""

    nome = "telegram"

    def __init__(self, bot, ctx: "Contexto"):
        self.bot, self.ctx = bot, ctx

    async def enviar(self, resumo: str, pdf: Path) -> None:
        chat = self.ctx.gerente_chat  # lido na hora: trocar o grupo no .env vale sem reiniciar
        if not chat:
            raise RuntimeError("MANAGER_CHAT_ID não está configurado.")
        await self.bot.send_message(chat, resumo)
        with pdf.open("rb") as f:
            await self.bot.send_document(chat, document=f, filename=pdf.name,
                                         caption="📄 Relatório em PDF")


@dataclass
class Contexto:
    loja: Loja
    arquivo: Arquivo
    gerente_chat: str | None = None
    permitidos: set[int] = field(default_factory=set)  # vazio = NINGUÉM tem acesso
    retencao_dias: int = 7
    canais: list[CanalEntrega] = field(default_factory=list)
    env_path: Path | None = None
    _env_mtime: float = 0.0

    @classmethod
    def do_ambiente(cls) -> "Contexto":
        loja = Loja.carregar(os.getenv("LOJAS_DIR", BASE_DIR / "lojas"),
                             os.getenv("LOJA", "divino-fogao"))
        arquivo = Arquivo(Path(os.getenv("ARCHIVE_DIR", BASE_DIR / "arquivo")) / loja.id)
        env = BASE_DIR / ".env"
        ctx = cls(
            loja=loja, arquivo=arquivo, gerente_chat=os.getenv("MANAGER_CHAT_ID") or None,
            permitidos=parse_ids(os.getenv("ALLOWED_USER_IDS", "")),
            retencao_dias=int(os.getenv("RETENCAO_DIAS", "7")),
            env_path=env if env.is_file() else None,
        )
        if ctx.env_path:
            ctx._env_mtime = ctx.env_path.stat().st_mtime
        return ctx

    def recarregar_env(self) -> None:
        """Relê ALLOWED_USER_IDS e MANAGER_CHAT_ID se o .env mudou (sem reiniciar o bot)."""
        if not self.env_path or not self.env_path.is_file():
            return
        mtime = self.env_path.stat().st_mtime
        if mtime == self._env_mtime:
            return
        self._env_mtime = mtime
        valores = dotenv_values(self.env_path, encoding=ENV_ENCODING)
        if "ALLOWED_USER_IDS" in valores:
            self.permitidos = parse_ids(valores["ALLOWED_USER_IDS"] or "")
        if "MANAGER_CHAT_ID" in valores:
            self.gerente_chat = valores["MANAGER_CHAT_ID"] or None
        log.info(".env recarregado: %d usuário(s) com acesso; grupo do gerente: %s",
                 len(self.permitidos), self.gerente_chat or "(não definido)")


def ctx_de(context: ContextTypes.DEFAULT_TYPE) -> Contexto:
    return context.application.bot_data["ctx"]


MSG_SEM_ACESSO = (
    "Você ainda não tem acesso aos checklists.\n"
    "Envie o número abaixo ao responsável para liberar o seu acesso:\n\n"
    "Seu ID de usuário: {uid}"
)


def somente_autorizados(fn):
    """Só quem está em ALLOWED_USER_IDS usa os comandos. Quem não está recebe o próprio ID."""
    @wraps(fn)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        ctx = ctx_de(context)
        ctx.recarregar_env()
        uid = update.effective_user.id
        if uid not in ctx.permitidos:
            if update.callback_query:
                await update.callback_query.answer("Sem acesso.", show_alert=True)
            else:
                await update.effective_message.reply_text(MSG_SEM_ACESSO.format(uid=uid))
            return
        return await fn(update, context)
    return wrapper


# ------------------------------------------------------------------- sessão
def salvar(context: ContextTypes.DEFAULT_TYPE, s: Sessao, cl: Checklist) -> None:
    """Guarda a sessão no chat (sobrevive a reinício) e no arquivo (visível em /hoje).

    Também guarda uma CÓPIA do checklist: editar o YAML no meio de um checklist em andamento
    não muda as etapas daquele checklist.
    """
    context.chat_data["sessao"] = s.to_dict()
    context.chat_data["checklist"] = cl.to_dict()
    ctx_de(context).arquivo.salvar_resultado(cl, s)


def limpar_sessao(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.chat_data.pop("sessao", None)
    context.chat_data.pop("checklist", None)


def carregar_sessao(context: ContextTypes.DEFAULT_TYPE) -> tuple[Sessao, Checklist] | None:
    raw = context.chat_data.get("sessao")
    if not raw:
        return None
    s = Sessao.from_dict(raw)
    snap = context.chat_data.get("checklist")
    if snap:
        cl = Checklist.from_dict(snap)
    else:  # estado antigo, sem cópia
        cl = ctx_de(context).loja.checklist(s.tipo).para_data(date.fromisoformat(s.data))
    return s, cl


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
    linhas = [[InlineKeyboardButton("✅ Concluído", callback_data=f"st:{idx}:c"),
               InlineKeyboardButton("⚠️ Problema", callback_data=f"st:{idx}:p")]]
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
    salvar(context, s, cl)
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
    if update.effective_chat.type != ChatType.PRIVATE:
        await msg.reply_text(
            "Para fazer o checklist, abra uma conversa privada comigo e envie o comando lá. "
            "(Em grupo eu não recebo as fotos.)")
        return
    if carregar_sessao(context):
        await msg.reply_text(
            "Já existe um checklist em andamento. Use /status, /finalizar ou /cancelar.")
        return
    try:
        base = ctx.loja.checklist(tipo)
    except FileNotFoundError:
        disp = ", ".join(ctx.loja.tipos_disponiveis()) or "nenhum"
        await msg.reply_text(f"O checklist '{tipo}' ainda não está configurado. Disponíveis: {disp}.")
        return
    except ValueError as exc:
        log.error("Checklist '%s' inválido: %s", tipo, exc)
        await msg.reply_text(f"O checklist '{tipo}' está com erro de configuração. "
                             "Avise o responsável pelo sistema.")
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
async def cmd_dinamico(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Qualquer /comando que não seja fixo: procura o checklist que usa esse comando."""
    ctx, msg = ctx_de(context), update.effective_message
    comando = msg.text.split()[0].lstrip("/").split("@")[0].lower()
    tipo = ctx.loja.tipo_por_comando(comando)
    if tipo is None:
        await msg.reply_text("Não conheço esse comando. Use /start para ver os disponíveis.")
        return
    await iniciar(update, context, tipo)


@somente_autorizados
async def cmd_iniciar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        disp = ", ".join(ctx_de(context).loja.tipos_disponiveis())
        await update.effective_message.reply_text(f"Uso: /iniciar <tipo>. Disponíveis: {disp}.")
        return
    await iniciar(update, context, context.args[0].lower())


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Aberto a todos: é assim que cada pessoa descobre o ID para pedir acesso."""
    ctx, msg = ctx_de(context), update.effective_message
    ctx.recarregar_env()
    uid = update.effective_user.id
    if uid not in ctx.permitidos:
        await msg.reply_text(
            MSG_SEM_ACESSO.format(uid=uid) + f"\nID deste chat: {update.effective_chat.id}")
        return
    iniciar_cmds = []
    for tipo in ctx.loja.tipos_disponiveis():
        try:
            c = ctx.loja.checklist(tipo)
        except (ValueError, FileNotFoundError):
            continue
        iniciar_cmds.append(f"/{c.comando} - {c.nome}")
    await msg.reply_text(
        "Olá! Eu guio os checklists do restaurante. Use-me em conversa privada.\n\n"
        + "\n".join(iniciar_cmds) + "\n"
        "/status - ver a etapa atual\n/finalizar - encerrar com o que já foi feito\n"
        "/cancelar - cancelar o checklist atual\n\n"
        "Acompanhamento e impressão:\n"
        "/hoje [tipo] - o que foi feito / falta fazer hoje\n"
        "/dia <data> [tipo] - o mesmo para outro dia (ex.: /dia 05/11)\n"
        "/imprimir [data] [tipo] - lista vazia em PDF para imprimir\n"
        "/resultado [data] [tipo] - lista preenchida em PDF\n"
        "/reenviar [data] [tipo] - reenvia o relatório ao grupo\n\n"
        f"Seu ID de usuário: {uid}\nID deste chat: {update.effective_chat.id}"
    )


@somente_autorizados
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg, par = update.effective_message, carregar_sessao(context)
    if not par:
        await msg.reply_text("Nenhum checklist em andamento. Use /start para ver os comandos.")
        return
    await seguir(msg, context, *par)


@somente_autorizados
async def cmd_cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    par = carregar_sessao(context)
    if not par:
        await update.effective_message.reply_text("Nenhum checklist em andamento.")
        return
    ctx_de(context).arquivo.apagar_sessao(par[0])  # descarta também as fotos desse checklist
    limpar_sessao(context)
    await update.effective_message.reply_text(
        "Checklist cancelado. Nada foi enviado ao grupo. Use /start para ver os comandos.")


@somente_autorizados
async def cmd_finalizar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg, par = update.effective_message, carregar_sessao(context)
    if not par:
        await msg.reply_text("Nenhum checklist em andamento.")
        return
    s, cl = par
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
    par = carregar_sessao(context)
    if not par:
        await q.answer("Este checklist não está mais em andamento.", show_alert=True)
        await q.edit_message_reply_markup(None)
        return
    s, cl = par

    if partes[0] == "fin":
        await q.answer()
        await q.edit_message_reply_markup(None)
        if partes[1] == "s":
            await finalizar(msg, context, s, cl)
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
    """Recebe a foto, guarda em disco (só para o PDF) e segue. A foto não é devolvida."""
    ctx, msg = ctx_de(context), update.effective_message
    par = carregar_sessao(context)
    if not par or par[0].encerrada:
        await msg.reply_text("Nenhum checklist em andamento. Use /start para ver os comandos.")
        return
    s, cl = par
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
    salvar(context, s, cl)
    if idx != s.etapa_atual:  # sobra de álbum anexada à etapa anterior
        return
    if s.fotos_faltando(cl):
        await msg.reply_text(f"📸 Recebida! Falta(m) {s.fotos_faltando(cl)} foto(s) desta etapa.")
    else:
        await msg.reply_text("📎 Foto anexada. Escreva uma observação ou toque em Continuar.")


@somente_autorizados
async def texto_solto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg, par = update.effective_message, carregar_sessao(context)
    if not par:
        return
    s, cl = par
    try:
        s.add_obs(cl, msg.text)
    except EstadoInvalido:
        await msg.reply_text("Escolha o status da etapa nos botões 👆")
        return
    salvar(context, s, cl)
    await msg.reply_text("📝 Observação anotada.")


# ----------------------------------------------------------------- finalizar
def nome_pdf(s: Sessao) -> str:
    return f"{s.tipo}_{s.data}_{datetime.fromisoformat(s.iniciado_em):%H%M}.pdf"


async def finalizar(
    msg, context: ContextTypes.DEFAULT_TYPE, s: Sessao, cl: Checklist
) -> None:
    ctx = ctx_de(context)
    s.finalizar(cl, ctx.loja.agora())
    limpar_sessao(context)
    ctx.arquivo.salvar_resultado(cl, s)
    pdf = ctx.arquivo.pasta(s) / nome_pdf(s)
    await asyncio.to_thread(gerar_relatorio_pdf, ctx.loja, cl, s, ctx.arquivo.raiz, pdf)
    resumo = resumo_texto(ctx.loja, cl, s)

    enviado = False
    if ctx.gerente_chat and ctx.canais:
        enviado = True
        for canal in ctx.canais:
            try:
                await canal.enviar(resumo, pdf)
            except Exception:
                log.exception("Falha ao enviar pelo canal %s", canal.nome)
                enviado = False
    else:
        log.warning("MANAGER_CHAT_ID não definido: relatório não enviado.")

    if enviado:
        await msg.reply_text(
            "🎉 Checklist concluído! O relatório (resumo e PDF) foi enviado ao grupo. Obrigado!")
    else:  # não perder a informação: mostra o resumo aqui e avisa
        await msg.reply_text(f"🎉 Checklist concluído!\n\n{resumo}")
        await msg.reply_text("⚠️ O relatório foi salvo, mas não consegui enviá-lo ao grupo. "
                             "Avise o responsável; depois ele pode usar /reenviar.")
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
    """Mostra o plano do dia e o que já foi feito (inclusive checklists em andamento
    iniciados por qualquer pessoa, pois tudo é lido do arquivo)."""
    ctx, msg = ctx_de(context), update.effective_message
    d, tipo = _args(ctx, args)
    if await _responder_tipo_invalido(msg, ctx, tipo):
        return
    for t in ([tipo] if tipo else ctx.loja.tipos_disponiveis()):
        try:
            cl = ctx.loja.checklist(t).para_data(d)
        except ValueError:
            await msg.reply_text(f"{t}: erro de configuração no checklist. Avise o responsável.")
            continue
        salvos = ctx.arquivo.resultados(d, t)
        s = None
        if salvos:
            cl, s = salvos[-1]  # usa as etapas como estavam naquele dia
        if not cl.etapas:
            await msg.reply_text(f"{t}: sem etapas em {data_br(d)}.")
            continue
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
    salvos = ctx.arquivo.resultados(d, tipo, apenas_finalizados=True)
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
        await msg.reply_text(f"Não há resultado finalizado de {tipo} em {data_br(d)} "
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
        await msg.reply_text(f"Não há resultado finalizado de {tipo} em {data_br(d)}.")
        return
    cl, s = res
    pdf = ctx.arquivo.pasta(s) / nome_pdf(s)
    if not pdf.exists():
        await asyncio.to_thread(gerar_relatorio_pdf, ctx.loja, cl, s, ctx.arquivo.raiz, pdf)
    try:
        for canal in ctx.canais:
            await canal.enviar(resumo_texto(ctx.loja, cl, s), pdf)
    except Exception as exc:
        log.exception("Falha no reenvio")
        await msg.reply_text(f"⚠️ Não consegui reenviar: {exc}")
        return
    await msg.reply_text("✅ Relatório reenviado ao grupo.")


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
    ctx.canais.append(TelegramEntrega(app.bot, ctx))
    app.add_handler(CommandHandler("start", cmd_start))
    for nome, fn in [("iniciar", cmd_iniciar), ("status", cmd_status), ("cancelar", cmd_cancelar),
                     ("finalizar", cmd_finalizar), ("hoje", cmd_hoje), ("dia", cmd_dia),
                     ("imprimir", cmd_imprimir), ("resultado", cmd_resultado),
                     ("reenviar", cmd_reenviar)]:
        app.add_handler(CommandHandler(nome, fn))
    app.add_handler(CallbackQueryHandler(botao, pattern=r"^(st|ct|fin):"))
    app.add_handler(MessageHandler(filters.PHOTO, foto))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, texto_solto))
    # por último: /fechar, /abrir e qualquer comando definido nos YAMLs
    app.add_handler(MessageHandler(filters.COMMAND, cmd_dinamico))
    app.add_error_handler(erro)
    return app


def main() -> None:
    env = BASE_DIR / ".env"
    load_dotenv(env, encoding=ENV_ENCODING)
    logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise SystemExit("Defina BOT_TOKEN no arquivo .env (veja .env.example).")
    ctx = Contexto.do_ambiente()
    removidos = ctx.arquivo.limpar_antigos(ctx.loja.agora().date(), ctx.retencao_dias)
    if removidos:
        log.info("Arquivo: removidos dias antigos %s", removidos)
    for tipo, erro_txt in ctx.loja.validar():
        log.error("Checklist '%s' com erro: %s", tipo, erro_txt)
    if not ctx.permitidos:
        log.warning("ALLOWED_USER_IDS vazio: ninguém conseguirá usar o bot até cadastrar IDs.")
    if not ctx.gerente_chat:
        log.warning("MANAGER_CHAT_ID não definido: relatórios não serão enviados.")
    log.info("Loja: %s | checklists: %s | usuários liberados: %d", ctx.loja.nome,
             ", ".join(ctx.loja.tipos_disponiveis()), len(ctx.permitidos))
    build_app(token, ctx).run_polling()


if __name__ == "__main__":
    main()

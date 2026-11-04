"""Bot do Telegram para rotina de fechamento de restaurante.

Fluxo: /fechar -> bot pede foto de cada etapa -> ao final envia relatório
(texto + fotos) para o grupo do gerente.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import InputMediaPhoto, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PicklePersistence,
    filters,
)

from closing import Checklist, Session

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO
)
log = logging.getLogger("fechamento-bot")

CHECKLIST = Checklist.load(os.getenv("CHECKLIST_FILE", BASE_DIR / "checklist.yaml"))
MANAGER_CHAT_ID = os.getenv("MANAGER_CHAT_ID")  # grupo/chat que recebe o relatório
ALLOWED_USERS = {
    int(x) for x in os.getenv("ALLOWED_USER_IDS", "").replace(" ", "").split(",") if x
}
ARCHIVE_DIR = Path(os.getenv("ARCHIVE_DIR", BASE_DIR / "arquivo"))


# ---------------------------------------------------------------- helpers
def autorizado(update: Update) -> bool:
    """Se ALLOWED_USER_IDS estiver vazio, qualquer um pode usar."""
    return not ALLOWED_USERS or update.effective_user.id in ALLOWED_USERS


def get_session(context: ContextTypes.DEFAULT_TYPE) -> Session | None:
    raw = context.chat_data.get("sessao")
    return Session.from_dict(raw) if raw else None


def save_session(context: ContextTypes.DEFAULT_TYPE, s: Session | None) -> None:
    if s is None:
        context.chat_data.pop("sessao", None)
    else:
        context.chat_data["sessao"] = s.to_dict()


def texto_etapa(s: Session) -> str:
    i = s.etapa_atual
    etapa = CHECKLIST.etapas[i]
    total = len(CHECKLIST.etapas)
    fotos = f"{etapa.fotos} fotos" if etapa.fotos > 1 else "1 foto"
    extra = "" if etapa.obrigatoria else "\n(opcional: /pular motivo)"
    return (
        f"Etapa {i + 1}/{total}: *{etapa.titulo}*\n"
        f"{etapa.instrucao}\n"
        f"📸 Envie {fotos}.{extra}"
    )


# --------------------------------------------------------------- comandos
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Olá! Eu guio o fechamento do restaurante.\n\n"
        "/fechar – iniciar o fechamento\n"
        "/status – ver em qual etapa estamos\n"
        "/pular motivo – pular etapa opcional\n"
        "/cancelar – cancelar o fechamento atual\n\n"
        f"Seu ID: {update.effective_user.id}"
    )


async def fechar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not autorizado(update):
        await update.message.reply_text("Você não tem permissão para usar este bot.")
        return
    if get_session(context):
        await update.message.reply_text(
            "Já existe um fechamento em andamento. Use /status ou /cancelar."
        )
        return
    s = Session(responsavel=update.effective_user.full_name)
    save_session(context, s)
    await update.message.reply_text(
        f"Vamos começar o {CHECKLIST.nome}! 🔒", parse_mode="Markdown"
    )
    await update.message.reply_text(texto_etapa(s), parse_mode="Markdown")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    s = get_session(context)
    if not s:
        await update.message.reply_text("Nenhum fechamento em andamento. Use /fechar.")
        return
    await update.message.reply_text(texto_etapa(s), parse_mode="Markdown")


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if get_session(context):
        save_session(context, None)
        await update.message.reply_text("Fechamento cancelado. Use /fechar para recomeçar.")
    else:
        await update.message.reply_text("Nenhum fechamento em andamento.")


async def pular(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    s = get_session(context)
    if not s:
        await update.message.reply_text("Nenhum fechamento em andamento. Use /fechar.")
        return
    try:
        s.pular(CHECKLIST, " ".join(context.args))
    except PermissionError as e:
        await update.message.reply_text(f"⚠️ {e}")
        return
    await avancar(update, context, s)


async def foto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    s = get_session(context)
    if not s:
        await update.message.reply_text("Nenhum fechamento em andamento. Use /fechar.")
        return
    if not autorizado(update):
        return

    msg = update.message
    maior = msg.photo[-1]  # maior resolução
    idx, avancou = s.add_foto(
        CHECKLIST,
        maior.file_id,
        legenda=msg.caption,
        media_group_id=msg.media_group_id,
    )

    # arquivo local (backup/auditoria)
    try:
        pasta = ARCHIVE_DIR / s.iniciado_em[:10] / f"{idx + 1:02d}"
        pasta.mkdir(parents=True, exist_ok=True)
        arq = await maior.get_file()
        n = len(s.fotos[idx])
        await arq.download_to_drive(pasta / f"{n}.jpg")
    except Exception:  # arquivar nunca deve travar o fluxo
        log.exception("Falha ao arquivar foto")

    if avancou:
        await avancar(update, context, s)
    else:
        save_session(context, s)
        etapa = CHECKLIST.etapas[idx]
        if len(s.fotos[idx]) < etapa.fotos:
            falta = etapa.fotos - len(s.fotos[idx])
            await msg.reply_text(f"📸 Recebida! Falta(m) {falta} foto(s) desta etapa.")


async def avancar(
    update: Update, context: ContextTypes.DEFAULT_TYPE, s: Session
) -> None:
    if s.concluida(CHECKLIST):
        await finalizar(update, context, s)
        return
    save_session(context, s)
    await update.message.reply_text("✅ Etapa registrada!")
    await update.message.reply_text(texto_etapa(s), parse_mode="Markdown")


async def finalizar(
    update: Update, context: ContextTypes.DEFAULT_TYPE, s: Session
) -> None:
    resumo = s.resumo(CHECKLIST)
    save_session(context, None)
    await update.message.reply_text(f"🎉 Fechamento concluído!\n\n{resumo}")

    if not MANAGER_CHAT_ID:
        log.warning("MANAGER_CHAT_ID não definido; relatório não enviado.")
        return

    bot = context.bot
    await bot.send_message(MANAGER_CHAT_ID, f"🔔 Novo fechamento\n\n{resumo}")
    for i, etapa in enumerate(CHECKLIST.etapas):
        ids = s.fotos.get(i, [])
        if not ids:
            continue
        legenda = f"{i + 1}. {etapa.titulo}"
        if s.notas.get(i):
            legenda += "\n" + "\n".join(s.notas[i])
        legenda = legenda[:1024]  # limite do Telegram
        if len(ids) == 1:
            await bot.send_photo(MANAGER_CHAT_ID, ids[0], caption=legenda)
        else:
            media = [
                InputMediaPhoto(fid, caption=legenda if k == 0 else None)
                for k, fid in enumerate(ids[:10])
            ]
            await bot.send_media_group(MANAGER_CHAT_ID, media)


async def texto_solto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if get_session(context):
        await update.message.reply_text("Preciso de uma *foto* para esta etapa 📸",
                                        parse_mode="Markdown")


# ------------------------------------------------------------------- main
def build_app(token: str) -> Application:
    persistence = PicklePersistence(filepath=BASE_DIR / "estado.pickle")
    app = Application.builder().token(token).persistence(persistence).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("fechar", fechar))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("cancelar", cancelar))
    app.add_handler(CommandHandler("pular", pular))
    app.add_handler(MessageHandler(filters.PHOTO, foto))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, texto_solto))
    return app


def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise SystemExit("Defina BOT_TOKEN no arquivo .env (veja .env.example).")
    build_app(token).run_polling()


if __name__ == "__main__":
    main()

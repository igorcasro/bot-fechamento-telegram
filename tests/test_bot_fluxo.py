"""Fluxo completo pelos handlers do Telegram, com objetos simulados (sem rede)."""
import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from PIL import Image

import bot
from fechamento.arquivo import Arquivo


class CanalFalso:
    nome = "falso"

    def __init__(self):
        self.enviados = []

    async def enviar(self, resumo, pdf):
        self.enviados.append((resumo, pdf))


def novo_msg(chat_id=1, text=None, photo=False, caption=None, gid=None):
    msg = SimpleNamespace(
        chat_id=chat_id, text=text, caption=caption, media_group_id=gid, text_html="etapa",
        reply_text=AsyncMock(), reply_html=AsyncMock(), reply_document=AsyncMock(),
        photo=[], 
    )
    if photo:
        async def baixar(destino):
            Image.new("RGB", (800, 1400), (60, 80, 100)).save(destino)
        arq = SimpleNamespace(download_to_drive=baixar)
        msg.photo = [SimpleNamespace(get_file=AsyncMock(return_value=arq))]
    return msg


class Chat:
    """Simula um chat do Telegram para um usuário."""

    def __init__(self, loja, tmp_path):
        self.canal = CanalFalso()
        self.ctx = bot.Contexto(loja=loja, arquivo=Arquivo(tmp_path / "arq"),
                                gerente_chat="-100", canais=[self.canal])
        self.context = SimpleNamespace(
            application=SimpleNamespace(bot_data={"ctx": self.ctx}), chat_data={}, args=[])
        self.user = SimpleNamespace(id=7, full_name="Arilson Junior")
        self.msgs = []

    def _update(self, msg, callback=None):
        return SimpleNamespace(effective_user=self.user, effective_message=msg,
                               callback_query=callback)

    def run(self, coro):
        return asyncio.run(coro)

    def comando(self, nome, *args):
        msg = novo_msg(text=f"/{nome}")
        self.context.args = list(args)
        self.msgs.append(msg)
        handler = {"fechar": bot.cmd_inicio, "finalizar": bot.cmd_finalizar, "hoje": bot.cmd_hoje,
                   "imprimir": bot.cmd_imprimir, "status": bot.cmd_status,
                   "resultado": bot.cmd_resultado}[nome]
        self.run(handler(self._update(msg), self.context))
        return msg

    def clicar(self, data):
        msg = novo_msg()
        q = SimpleNamespace(data=data, message=msg, answer=AsyncMock(),
                            edit_message_text=AsyncMock(), edit_message_reply_markup=AsyncMock())
        self.msgs.append(msg)
        self.run(bot.botao(self._update(msg, q), self.context))
        return msg, q

    def foto(self, **kw):
        msg = novo_msg(photo=True, **kw)
        self.msgs.append(msg)
        self.run(bot.foto(self._update(msg), self.context))
        return msg

    def texto(self, t):
        msg = novo_msg(text=t)
        self.run(bot.texto_solto(self._update(msg), self.context))
        return msg

    @property
    def sessao(self):
        return bot.get_sessao(self.context)


def test_fechamento_completo(loja, tmp_path):
    chat = Chat(loja, tmp_path)
    chat.comando("fechar")
    assert chat.sessao is not None and chat.sessao.etapa_atual == 0

    for i in range(21):
        e = loja.checklist("fechamento").etapas[i]
        if e.titulo == "Carne descongelando":
            chat.clicar(f"st:{i}:n")
        elif e.titulo == "Forno desligado":
            chat.clicar(f"st:{i}:p")
            chat.foto()
            chat.texto("Não esfriou")
            chat.clicar(f"ct:{i}")
        elif e.foto == "opcional":
            chat.clicar(f"st:{i}:c")
            chat.clicar(f"ct:{i}")
        else:
            chat.clicar(f"st:{i}:c")
            chat.foto()

    assert chat.sessao is None  # finalizou sozinho
    assert len(chat.canal.enviados) == 1
    resumo, pdf = chat.canal.enviados[0]
    assert pdf.exists() and pdf.read_bytes().startswith(b"%PDF")
    assert "19 concluídas · ⚠️ 1 com problema" in resumo and "➖ 1 não se aplica" in resumo
    assert "Forno desligado - Não esfriou" in resumo
    assert "📸 18 foto(s)" in resumo  # 17 obrigatórias + 1 do problema (2 etapas sem foto)
    assert len(chat.ctx.arquivo.resultados(loja.agora().date(), "fechamento")) == 1


def test_finalizar_antecipado_e_comandos_de_dia(loja, tmp_path):
    chat = Chat(loja, tmp_path)
    chat.comando("fechar")
    chat.clicar("st:0:c")
    chat.foto()
    # acompanhamento durante o checklist
    msg = chat.comando("hoje", "fechamento")
    texto = msg.reply_text.await_args_list[0].args[0]
    assert "✅ 1. Limpeza das caixas de gordura" in texto and "⏳ 2. Geladeira ligada" in texto
    # finalizar antes da hora
    chat.comando("finalizar")
    chat.clicar("fin:s")
    assert chat.sessao is None and len(chat.canal.enviados) == 1
    assert "20 não realizadas" in chat.canal.enviados[0][0]
    # lista vazia e preenchida em PDF
    m = chat.comando("imprimir")
    assert m.reply_document.await_count == 1
    m = chat.comando("resultado")
    assert m.reply_document.await_count == 1


def test_foto_sem_status_e_botao_velho(loja, tmp_path):
    chat = Chat(loja, tmp_path)
    chat.comando("fechar")
    m = chat.foto()
    assert "escolha o status" in m.reply_text.await_args.args[0].lower()
    assert chat.sessao.total_fotos() == 0
    chat.clicar("st:0:c"); chat.foto()
    _, q = chat.clicar("st:0:c")  # botão antigo da etapa 1
    assert q.answer.await_args.kwargs.get("show_alert") is True


def test_checklist_nao_configurado(loja, tmp_path):
    chat = Chat(loja, tmp_path)
    msg = novo_msg(text="/abrir")
    chat.run(bot.cmd_inicio(chat._update(msg), chat.context))
    assert "ainda não está configurado" in msg.reply_text.await_args.args[0]
    assert chat.sessao is None


def test_start_mostra_ids(loja, tmp_path):
    chat = Chat(loja, tmp_path)
    msg = novo_msg(text="/start")
    upd = SimpleNamespace(effective_user=chat.user, effective_message=msg,
                          effective_chat=SimpleNamespace(id=-1001234567890), callback_query=None)
    chat.run(bot.cmd_start(upd, chat.context))
    txt = msg.reply_text.await_args.args[0]
    assert "Seu ID de usuário: 7" in txt and "ID deste chat: -1001234567890" in txt

"""Fluxo completo pelos handlers do Telegram, com objetos simulados (sem rede)."""
import asyncio
import os
import shutil
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from PIL import Image

import bot
from fechamento.arquivo import Arquivo
from fechamento.loja import Loja

FECHAMENTO = "fechamento"


class CanalFalso:
    nome = "falso"

    def __init__(self):
        self.enviados = []

    async def enviar(self, resumo, pdf):
        self.enviados.append((resumo, pdf))


class BotFalso:
    """Telegram 'estrito': só aceita send_message e send_document (nunca foto/álbum)."""

    def __init__(self):
        self.chamadas = []

    async def send_message(self, chat_id, text, **kw):
        self.chamadas.append(("send_message", chat_id, text))

    async def send_document(self, chat_id, document, filename=None, caption=None, **kw):
        self.chamadas.append(("send_document", chat_id, filename, document.read(4)))

    def __getattr__(self, nome):
        raise AssertionError(f"O bot não deveria chamar {nome}")


def novo_msg(chat_id=1, text=None, photo=False, caption=None, gid=None):
    msg = SimpleNamespace(
        chat_id=chat_id, text=text, caption=caption, media_group_id=gid, text_html="etapa",
        reply_text=AsyncMock(), reply_html=AsyncMock(), reply_document=AsyncMock(), photo=[],
    )
    if photo:
        async def baixar(destino):
            Image.new("RGB", (800, 1400), (60, 80, 100)).save(destino)
        arq = SimpleNamespace(download_to_drive=baixar)
        msg.photo = [SimpleNamespace(get_file=AsyncMock(return_value=arq))]
    return msg


HANDLERS = {
    "start": bot.cmd_start, "status": bot.cmd_status, "finalizar": bot.cmd_finalizar,
    "cancelar": bot.cmd_cancelar, "hoje": bot.cmd_hoje, "dia": bot.cmd_dia,
    "imprimir": bot.cmd_imprimir, "resultado": bot.cmd_resultado, "reenviar": bot.cmd_reenviar,
}


def novo_ctx(loja, tmp_path, permitidos=frozenset({7}), canal=True, **kw):
    ctx = bot.Contexto(loja=loja, arquivo=Arquivo(tmp_path / "arq"), gerente_chat="-100",
                       permitidos=set(permitidos), canais=[CanalFalso()] if canal else [], **kw)
    return ctx


class Chat:
    """Simula um chat do Telegram com um usuário (cada Chat tem o próprio chat_data)."""

    def __init__(self, ctx, user_id=7, tipo="private", chat_id=1):
        self.ctx = ctx
        self.context = SimpleNamespace(
            application=SimpleNamespace(bot_data={"ctx": ctx}), chat_data={}, args=[])
        self.user = SimpleNamespace(id=user_id, full_name="Arilson Junior")
        self.chat = SimpleNamespace(id=chat_id, type=tipo)
        self.msgs = []

    @property
    def canal(self):
        return self.ctx.canais[0]

    def _update(self, msg, callback=None):
        return SimpleNamespace(effective_user=self.user, effective_message=msg,
                               effective_chat=self.chat, callback_query=callback)

    def run(self, coro):
        return asyncio.run(coro)

    def comando(self, nome, *args):
        msg = novo_msg(text=f"/{nome}")
        self.context.args = list(args)
        self.msgs.append(msg)
        self.run(HANDLERS.get(nome, bot.cmd_dinamico)(self._update(msg), self.context))
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
        par = bot.carregar_sessao(self.context)
        return par[0] if par else None


def completar(chat, loja):
    """Responde as 21 etapas do fechamento (1 N/A, 1 problema, 2 sem foto, 17 com foto)."""
    chat.comando("fechar")
    etapas = loja.checklist(FECHAMENTO).etapas
    for i, e in enumerate(etapas):
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


def copia_loja(loja, tmp_path) -> Loja:
    shutil.copytree(loja.pasta, tmp_path / "lojas" / "x")
    return Loja.carregar(tmp_path / "lojas", "x")


# ------------------------------------------------------------------ fluxo básico
def test_fechamento_completo(loja, tmp_path):
    chat = Chat(novo_ctx(loja, tmp_path))
    completar(chat, loja)

    assert chat.sessao is None  # finalizou sozinho
    assert len(chat.canal.enviados) == 1
    resumo, pdf = chat.canal.enviados[0]
    assert pdf.exists() and pdf.read_bytes().startswith(b"%PDF")
    assert "19 concluídas · ⚠️ 1 com problema" in resumo and "➖ 1 não se aplica" in resumo
    assert "Forno desligado - Não esfriou" in resumo
    assert "📸 18 foto(s)" in resumo  # 17 obrigatórias + 1 do problema
    assert len(chat.ctx.arquivo.resultados(loja.agora().date(), FECHAMENTO)) == 1
    # o funcionário recebe só uma confirmação curta (o resumo vai para o grupo)
    respostas = [c.args[0] for c in chat.msgs[-1].reply_text.await_args_list]
    assert any("enviado ao grupo" in r for r in respostas)
    assert not any("concluídas" in r for r in respostas)


def test_fotos_so_no_pdf_nunca_na_conversa(loja, tmp_path):
    bot_falso = BotFalso()
    ctx = novo_ctx(loja, tmp_path, canal=False)
    ctx.canais.append(bot.TelegramEntrega(bot_falso, ctx))
    chat = Chat(ctx)
    completar(chat, loja)

    # grupo: 1 texto + 1 documento PDF; nenhuma foto/álbum
    assert [c[0] for c in bot_falso.chamadas] == ["send_message", "send_document"]
    assert bot_falso.chamadas[0][1] == bot_falso.chamadas[1][1] == "-100"
    assert bot_falso.chamadas[1][2].endswith(".pdf") and bot_falso.chamadas[1][3] == b"%PDF"
    # conversa do funcionário: nenhuma mensagem devolveu foto ou documento
    assert all(m.reply_document.await_count == 0 for m in chat.msgs)


def test_finalizar_antecipado_e_comandos_de_dia(loja, tmp_path):
    chat = Chat(novo_ctx(loja, tmp_path))
    chat.comando("fechar")
    chat.clicar("st:0:c")
    chat.foto()
    msg = chat.comando("hoje", "fechamento")
    texto = msg.reply_text.await_args_list[0].args[0]
    assert "✅ 1. Limpeza das caixas de gordura" in texto and "⏳ 2. Geladeira ligada" in texto
    assert "em andamento" in texto
    chat.comando("finalizar")
    chat.clicar("fin:s")
    assert chat.sessao is None and len(chat.canal.enviados) == 1
    assert "20 não realizadas" in chat.canal.enviados[0][0]
    assert chat.comando("imprimir").reply_document.await_count == 1
    assert chat.comando("resultado").reply_document.await_count == 1


def test_foto_sem_status_e_botao_velho(loja, tmp_path):
    chat = Chat(novo_ctx(loja, tmp_path))
    chat.comando("fechar")
    m = chat.foto()
    assert "escolha o status" in m.reply_text.await_args.args[0].lower()
    assert chat.sessao.total_fotos() == 0
    chat.clicar("st:0:c")
    chat.foto()
    _, q = chat.clicar("st:0:c")  # botão antigo da etapa 1
    assert q.answer.await_args.kwargs.get("show_alert") is True


def test_checklist_nao_configurado(loja, tmp_path):
    chat = Chat(novo_ctx(loja, tmp_path))
    msg = chat.comando("abrir")  # a loja só tem fechamento por enquanto
    assert "Não conheço esse comando" in msg.reply_text.await_args.args[0]
    assert chat.sessao is None


def test_start_mostra_ids_e_comandos(loja, tmp_path):
    chat = Chat(novo_ctx(loja, tmp_path), chat_id=-1001234567890)
    txt = chat.comando("start").reply_text.await_args.args[0]
    assert "Seu ID de usuário: 7" in txt and "ID deste chat: -1001234567890" in txt
    assert "/fechar - Fechamento da Loja" in txt


# ------------------------------------------------------------------ acesso
def test_sem_acesso_recebe_o_proprio_id(loja, tmp_path):
    chat = Chat(novo_ctx(loja, tmp_path), user_id=99)
    for nome in ("fechar", "hoje", "imprimir"):
        txt = chat.comando(nome).reply_text.await_args.args[0]
        assert "ainda não tem acesso" in txt and "99" in txt
    assert chat.sessao is None
    # /start continua aberto: é como a pessoa descobre o ID para pedir acesso
    assert "Seu ID de usuário: 99" in chat.comando("start").reply_text.await_args.args[0]


def test_lista_vazia_ninguem_tem_acesso(loja, tmp_path):
    chat = Chat(novo_ctx(loja, tmp_path, permitidos=frozenset()))
    assert "ainda não tem acesso" in chat.comando("fechar").reply_text.await_args.args[0]


def test_env_recarregado_sem_reiniciar(loja, tmp_path):
    env = tmp_path / ".env"
    env.write_text("ALLOWED_USER_IDS=7\nMANAGER_CHAT_ID=-100\n", encoding="utf-8")
    ctx = novo_ctx(loja, tmp_path, env_path=env)
    ctx._env_mtime = env.stat().st_mtime
    chat = Chat(ctx, user_id=99)
    assert "ainda não tem acesso" in chat.comando("fechar").reply_text.await_args.args[0]

    # o responsável adiciona o ID e troca o grupo no .env (sem reiniciar o bot)
    env.write_text("ALLOWED_USER_IDS=7, 99, abc\nMANAGER_CHAT_ID=-555\n", encoding="utf-8")
    os.utime(env, (env.stat().st_mtime + 10, env.stat().st_mtime + 10))
    chat.comando("fechar")
    assert chat.sessao is not None
    assert ctx.permitidos == {7, 99} and ctx.gerente_chat == "-555"  # 'abc' ignorado


def test_checklist_so_em_conversa_privada(loja, tmp_path):
    chat = Chat(novo_ctx(loja, tmp_path), tipo="group", chat_id=-100)
    txt = chat.comando("fechar").reply_text.await_args.args[0]
    assert "conversa privada" in txt and chat.sessao is None


# ------------------------------------------------------------------ evolução dos checklists
def test_novo_checklist_funciona_sem_reiniciar(loja, tmp_path):
    loja2 = copia_loja(loja, tmp_path)
    chat = Chat(novo_ctx(loja2, tmp_path))
    (loja2.pasta / "checklists" / "limpeza.yaml").write_text(
        "comando: limpar\nnome: Limpeza Geral\nsecoes:\n  - nome: SALÃO\n    etapas:\n"
        "      - titulo: Mesas limpas\n      - titulo: Vidros limpos\n", encoding="utf-8")
    msg = chat.comando("limpar")
    assert chat.sessao.tipo == "limpeza"
    assert "Limpeza Geral" in msg.reply_html.await_args_list[0].args[0]
    assert "Mesas limpas" in msg.reply_html.await_args_list[1].args[0]
    # e o /hoje já lista o novo tipo junto com o fechamento
    txt = " ".join(c.args[0] for c in chat.comando("hoje").reply_text.await_args_list)
    assert "Limpeza Geral" in txt and "Fechamento da Loja" in txt


def test_editar_yaml_no_meio_nao_afeta_checklist_em_andamento(loja, tmp_path):
    loja2 = copia_loja(loja, tmp_path)
    chat = Chat(novo_ctx(loja2, tmp_path))
    chat.comando("fechar")
    arq = loja2.pasta / "checklists" / "fechamento.yaml"
    arq.write_text(arq.read_text(encoding="utf-8").replace(
        "      - titulo: \"Limpeza das caixas de gordura\"",
        "      - titulo: \"ETAPA NOVA\"\n      - titulo: \"Limpeza das caixas de gordura\"", 1),
        encoding="utf-8")
    assert len(loja2.checklist(FECHAMENTO).etapas) == 22  # o YAML mudou...
    chat.clicar("st:0:c")
    msg = chat.foto()
    proxima = msg.reply_html.await_args.args[0]
    assert "Geladeira ligada" in proxima and "etapa 2/21" in proxima  # ...mas a sessão não


def test_yaml_quebrado_nao_derruba_o_bot(loja, tmp_path):
    loja2 = copia_loja(loja, tmp_path)
    (loja2.pasta / "checklists" / "quebrado.yaml").write_text("secoes: []\n", encoding="utf-8")
    chat = Chat(novo_ctx(loja2, tmp_path))
    assert "erro de configuração" in " ".join(
        c.args[0] for c in chat.comando("hoje", "quebrado").reply_text.await_args_list)
    msg = chat.comando("quebrado")
    assert "erro de configuração" in msg.reply_text.await_args.args[0]
    chat.comando("fechar")
    assert chat.sessao is not None  # os outros checklists seguem funcionando


# ------------------------------------------------------------------ acompanhamento e cancelamento
def test_hoje_de_outro_chat_mostra_checklist_em_andamento(loja, tmp_path):
    ctx = novo_ctx(loja, tmp_path, permitidos=frozenset({7, 8}))
    funcionario = Chat(ctx, user_id=7, chat_id=1)
    gerente = Chat(ctx, user_id=8, tipo="group", chat_id=-100)
    funcionario.comando("fechar")
    funcionario.clicar("st:0:c")
    funcionario.foto()
    txt = gerente.comando("hoje", "fechamento").reply_text.await_args_list[0].args[0]
    assert "✅ 1. Limpeza das caixas de gordura" in txt and "em andamento" in txt


def test_cancelar_descarta_checklist_e_fotos(loja, tmp_path):
    chat = Chat(novo_ctx(loja, tmp_path))
    chat.comando("fechar")
    chat.clicar("st:0:c")
    chat.foto()
    pasta = chat.ctx.arquivo.raiz / chat.sessao.pasta
    assert any(pasta.rglob("*.jpg"))
    chat.comando("cancelar")
    assert chat.sessao is None and not pasta.exists()
    assert chat.canal.enviados == []
    txt = chat.comando("hoje", "fechamento").reply_text.await_args_list[0].args[0]
    assert "Nada registrado" in txt


def test_sem_grupo_configurado_mostra_resumo_ao_funcionario(loja, tmp_path):
    ctx = novo_ctx(loja, tmp_path)
    ctx.gerente_chat = None
    chat = Chat(ctx)
    chat.comando("fechar")
    chat.comando("finalizar")
    chat.clicar("fin:s")
    textos = " ".join(c.args[0] for c in chat.msgs[-1].reply_text.await_args_list)
    assert "não consegui enviá-lo ao grupo" in textos and "21 não realizadas" in textos
    assert chat.canal.enviados == []


def test_main_mensagens_claras_para_token_invalido_e_sem_rede(loja, tmp_path, monkeypatch, caplog):
    import logging

    from telegram.error import InvalidToken, NetworkError

    monkeypatch.setenv("BOT_TOKEN", "123:abc")
    monkeypatch.setenv("ALLOWED_USER_IDS", "7")
    monkeypatch.setenv("MANAGER_CHAT_ID", "-100")
    monkeypatch.setenv("ARCHIVE_DIR", str(tmp_path / "arq"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    raiz = logging.getLogger()
    antes = list(raiz.handlers)
    try:
        for erro, trecho in ((InvalidToken("x"), "recusou o BOT_TOKEN"),
                             (NetworkError("sem wifi"), "Sem conexão com o Telegram")):
            fake_app = SimpleNamespace(run_polling=lambda **kw: (_ for _ in ()).throw(erro))
            monkeypatch.setattr(bot, "build_app", lambda token, ctx: fake_app)
            caplog.clear()
            try:
                with caplog.at_level(logging.INFO):
                    bot.main()
                raise AssertionError("main() deveria encerrar com SystemExit")
            except SystemExit as exc:
                assert exc.code == 1
            assert trecho in caplog.text
    finally:
        for h in list(raiz.handlers):
            if h not in antes:
                raiz.removeHandler(h)
                h.close()


def test_configuracao_pode_ficar_fora_da_pasta_do_codigo(loja, tmp_path, monkeypatch):
    """LOJAS_DIR/ARCHIVE_DIR apontam para fora do projeto: atualizar o código não toca nelas."""
    config = tmp_path / "bot-config" / "lojas"
    shutil.copytree(loja.pasta.parent, config)
    (config / "divino-fogao" / "checklists" / "fechamento.yaml").write_text(
        "comando: fechar\nnome: Fechamento Personalizado\nsecoes:\n  - nome: A\n    etapas:\n"
        "      - titulo: Única etapa\n", encoding="utf-8")
    monkeypatch.setenv("LOJAS_DIR", str(config))
    monkeypatch.setenv("ARCHIVE_DIR", str(tmp_path / "dados"))
    monkeypatch.setenv("ALLOWED_USER_IDS", "7")
    ctx = bot.Contexto.do_ambiente()
    assert ctx.loja.checklist("fechamento").nome == "Fechamento Personalizado"
    assert str(ctx.arquivo.raiz).startswith(str(tmp_path / "dados"))

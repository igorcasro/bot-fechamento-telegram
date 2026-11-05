import logging

from nucleo import logs


def test_log_em_arquivo_e_token_nao_vaza(tmp_path):
    raiz = logging.getLogger()
    antes = list(raiz.handlers)
    try:
        arq = logs.configurar(tmp_path / "logs")
        logs.configurar(tmp_path / "logs")  # chamar de novo não duplica handlers
        assert len([h for h in raiz.handlers if getattr(h, "_checklist_arquivo", False)]) == 1
        logging.getLogger("checklist-bot").info("olá do teste")
        # o httpx escreve a URL (com o token) em INFO: precisa estar silenciado
        logging.getLogger("httpx").info("POST https://api.telegram.org/bot123:SEGREDO/getUpdates")
        for h in raiz.handlers:
            h.flush()
        conteudo = arq.read_text(encoding="utf-8")
        assert "olá do teste" in conteudo and "SEGREDO" not in conteudo
    finally:
        for h in list(raiz.handlers):
            if h not in antes:
                raiz.removeHandler(h)
                h.close()

# Bot de Checklists do Restaurante (Telegram)

Bot que conduz os checklists de rotina do restaurante (hoje: **fechamento**; depois:
abertura e outros) pelo Telegram. A equipe responde cada etapa com botões, envia fotos e
observações, e ao final o bot manda ao grupo do gerente um **resumo em texto** e um
**relatório em PDF** com as fotos.

## Como a equipe usa

1. `/fechar` inicia o checklist **do dia** (as etapas mudam conforme o dia, se configurado).
2. Para cada etapa o bot mostra os botões **✅ Concluído · ⚠️ Problema · ➖ Não se aplica**.
   - *Concluído*: pede a foto (obrigatória) ou oferece "Continuar sem foto" (opcional).
   - *Problema*: peça para descrever (texto e/ou foto) e tocar em **Continuar**.
   - *Não se aplica*: avança direto.
3. Ao responder a última etapa, o relatório é gerado e enviado ao gerente.
   Use `/finalizar` para encerrar antes: o que ficou sem resposta vira "não realizada".

| Comando | O que faz |
|---|---|
| `/fechar`, `/abrir`, `/iniciar <tipo>` | inicia um checklist |
| `/status` | mostra de novo a etapa atual |
| `/finalizar`, `/cancelar` | encerra com o que foi feito / cancela |
| `/hoje [tipo]` | o que já foi feito e o que falta hoje |
| `/dia <data> [tipo]` | o mesmo para outro dia (`/dia 05/11`, `/dia 2026-11-05`) |
| `/imprimir [data] [tipo]` | lista **vazia** em PDF para imprimir |
| `/resultado [data] [tipo]` | lista **preenchida** em PDF para imprimir |
| `/reenviar [data] [tipo]` | reenvia resumo + PDF ao gerente |

## Rodando

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # preencha BOT_TOKEN e MANAGER_CHAT_ID
python bot.py
```

1. Crie o bot com o `@BotFather` (`/newbot`) e coloque o token em `BOT_TOKEN`.
2. Crie um grupo com o gerente, adicione o bot e coloque o ID do grupo em `MANAGER_CHAT_ID`.
3. Restrinja quem pode usar em `ALLOWED_USER_IDS` (o `/start` mostra o ID de cada pessoa).

O `/start` mostra "Seu ID de usuário" e "ID deste chat" (use este último, no grupo, em `MANAGER_CHAT_ID`).

> **Onde rodar:** o bot precisa estar ligado na hora do fechamento. O computador do
> restaurante tende a ser desligado justamente nessa hora (é uma etapa do checklist!),
> então o ideal é um servidor pequeno sempre ligado (VPS barata, Raspberry Pi, etc.).
> O bot usa *polling*, então não precisa de IP fixo nem de domínio.

## Configurando checklists e lojas

```
lojas/
  divino-fogao/
    loja.yaml              # nome, local, fuso e logo
    logo.png
    checklists/
      fechamento.yaml      # um arquivo por tipo de checklist
```

- **Editar o checklist** = editar o YAML (veja os comentários em
  `lojas/divino-fogao/checklists/fechamento.yaml`): seções, etapas, `foto:
  obrigatoria | opcional | nenhuma`, `fotos: 2`, `nao_se_aplica: false`.
- **Etapas por dia**: `dias: [seg, qua]`, `datas: [2026-12-24]` (só nessas datas, se não
  houver `dias`) e `exceto: [2026-12-25]`.
- **Novo tipo** (ex.: abertura): crie `checklists/abertura.yaml`; o `/abrir` passa a funcionar.
- **Outra loja**: copie `lojas/divino-fogao/` para `lojas/<novo-id>/`, ajuste e rode com
  `LOJA=<novo-id>` (um bot/token por loja).

## Dados guardados

Fotos, `resultado.json` e PDFs ficam em `arquivo/<loja>/AAAA-MM-DD/<tipo>_HHMM/` e são
**apagados após 7 dias** (`RETENCAO_DIAS`). O progresso do checklist em andamento fica em
`estado.pickle`, então reiniciar o bot não perde o que já foi respondido.

## Estrutura do código

```
bot.py                  # adaptador do Telegram (comandos, botões, fotos, envio)
fechamento/
  checklist.py          # seções, etapas e regras por dia (YAML)
  sessao.py             # máquina de estados de um checklist em andamento
  relatorio.py          # resumo em texto e progresso do dia
  pdf.py                # PDF do relatório e listas para impressão
  arquivo.py            # fotos, resultado.json e retenção
  loja.py               # configuração por loja
  entrega.py            # interface de canais de entrega (Telegram hoje; WhatsApp depois)
lojas/                  # dados de cada loja
tests/                  # pytest
```

## Testes

```bash
pytest
```

## Próximos passos

- Envio por WhatsApp (implementar `CanalEntrega` em `fechamento/entrega.py`)
- Checklist de abertura (criar `abertura.yaml`)
- Página web para acompanhar as tarefas por dia (os dados já ficam em `resultado.json`)
- Lembrete automático se o fechamento não começar até certo horário

# Bot de Checklists do Restaurante (Telegram)

Bot que conduz os checklists de rotina do restaurante (hoje: **fechamento**; depois:
abertura e outros) pelo Telegram. A equipe responde cada etapa com botões, envia fotos e
observações, e ao final o bot manda ao grupo do gerente um **resumo em texto** e um
**relatório em PDF** com as fotos.

## Como a equipe usa

Cada funcionário usa o bot em **conversa privada** (em grupo o Telegram não entrega as fotos
ao bot, então o `/fechar` recusa e pede a conversa privada).

1. `/fechar` inicia o checklist **do dia** (as etapas mudam conforme o dia, se configurado).
2. Para cada etapa o bot mostra os botões **✅ Concluído · ⚠️ Problema · ➖ Não se aplica**.
   - *Concluído*: pede a foto (obrigatória) ou oferece "Continuar sem foto" (opcional).
   - *Problema*: descreva em texto e/ou foto e toque em **Continuar**.
   - *Não se aplica*: avança direto.
3. Ao responder a última etapa, o **resumo em texto e o PDF vão para o grupo** do gerente e o
   funcionário recebe só uma confirmação curta. As fotos **nunca voltam na conversa**: ficam
   guardadas só para montar o PDF.
   Use `/finalizar` para encerrar antes: o que ficou sem resposta vira "não realizada".

| Comando | O que faz |
|---|---|
| `/fechar`, `/abrir`, `/<comando do checklist>` | inicia um checklist (cada YAML define o seu) |
| `/status` | mostra de novo a etapa atual |
| `/finalizar` | encerra com o que foi feito |
| `/cancelar` | cancela e **descarta** o checklist e as fotos dele (nada vai ao grupo) |
| `/hoje [tipo]` | o que já foi feito e o que falta hoje (vale para qualquer chat) |
| `/dia <data> [tipo]` | o mesmo para outro dia (`/dia 05/11`, `/dia 2026-11-05`) |
| `/imprimir [data] [tipo]` | lista **vazia** em PDF para imprimir |
| `/resultado [data] [tipo]` | lista **preenchida** em PDF para imprimir |
| `/reenviar [data] [tipo]` | reenvia resumo + PDF ao grupo |

## Quem pode usar (lista de acesso)

Só quem está em `ALLOWED_USER_IDS` (no `.env`) usa o bot; todos os outros recebem o próprio ID.

1. O funcionário abre o bot e envia `/start`. Se ainda não tem acesso, o bot responde com
   **"Seu ID de usuário: 123456789"**.
2. Ele envia esse número a quem cuida do servidor (junto com o nome, para você saber de quem é).
3. Essa pessoa adiciona o número em `ALLOWED_USER_IDS`, separado por vírgula, e salva o `.env`.
   **Não precisa reiniciar**: o bot relê o arquivo sozinho. Para remover alguém, tire o número.

Quem for usar `/hoje`, `/resultado` etc. direto no grupo da gerência também precisa estar na lista.

## Rodando

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # preencha BOT_TOKEN e MANAGER_CHAT_ID
python bot.py
```

1. Crie o bot com o `@BotFather` (`/newbot`) e coloque o token em `BOT_TOKEN`.
2. Crie o grupo que receberá os relatórios, adicione o bot e envie `/start` no grupo: ele mostra
   o **"ID deste chat"** (número negativo). Coloque em `MANAGER_CHAT_ID`.
   Para trocar de grupo (ou enviar a uma pessoa só) depois, basta trocar esse número e salvar.
3. Cadastre os IDs de quem vai usar em `ALLOWED_USER_IDS` (veja "Quem pode usar").

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
  A mudança vale para os **próximos** checklists, sem reiniciar. Um checklist que já está em
  andamento mantém as etapas com que começou.
- **Etapas por dia**: `dias: [seg, qua]`, `datas: [2026-12-24]` (só nessas datas, se não
  houver `dias`) e `exceto: [2026-12-25]`.
- **Novo tipo de checklist** (ex.: abertura): copie `fechamento.yaml` para `abertura.yaml`
  (nesta pasta), troque `comando`, `nome` e as etapas. O comando (`/abrir`) **funciona na
  hora, sem reiniciar**. O nome do arquivo é o tipo, e o `comando` aceita só letras minúsculas,
  números e `_`. Para o comando aparecer no menu do Telegram, atualize `/setcommands` no
  @BotFather (opcional).
- Se um YAML tiver erro, o bot registra no log e avisa quem usar aquele checklist; os demais
  continuam funcionando.
- **Outra loja**: copie `lojas/divino-fogao/` para `lojas/<novo-id>/`, ajuste e rode com
  `LOJA=<novo-id>` (um bot/token por loja).

## Dados guardados

Fotos, `resultado.json` e PDFs ficam em `arquivo/<loja>/AAAA-MM-DD/<tipo>_HHMM/` e são
**apagados após 7 dias** (`RETENCAO_DIAS`). As fotos só servem para montar o PDF (e para
`/reenviar`, durante esses 7 dias). O progresso do checklist em andamento fica em
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
- Checklist de abertura e demais checklists (criar o YAML de cada um)
- Página web para acompanhar as tarefas por dia (os dados já ficam em `resultado.json`)
- Lembrete automático se o fechamento não começar até certo horário

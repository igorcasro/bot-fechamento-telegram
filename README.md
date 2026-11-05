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
   - *Problema*: descreva em texto e/ou foto e toque em **Continuar** (foto com legenda já
     encerra a etapa, sem precisar do botão).
   - Atalho: enviar a foto direto, sem tocar em **Concluído**, também conclui a etapa (a
     legenda vira observação).
   - *Não se aplica*: avança direto.
3. Ao responder a última etapa, o **resumo em texto e o PDF vão para o grupo** do gerente e o
   funcionário recebe só uma confirmação curta. As fotos **nunca voltam na conversa**: ficam
   guardadas só para montar o PDF.
   Use `/finalizar` para encerrar antes: o que ficou sem resposta vira "não realizada".

| Comando | O que faz |
|---|---|
| `/fechar`, `/abrir`, `/<comando do checklist>` | inicia um checklist (cada YAML define o seu comando) |
| `/iniciar <tipo>` | inicia um checklist pelo nome do tipo (ex.: `/iniciar fechamento`) |
| `/status` | mostra de novo a etapa atual |
| `/finalizar` | encerra com o que foi feito |
| `/cancelar` | cancela e **descarta** o checklist e as fotos dele (nada vai ao grupo) |
| `/hoje [tipo]` | o que já foi feito e o que falta hoje (vale para qualquer chat) |
| `/dia <data> [tipo]` | o mesmo para outro dia (`/dia 05/11`, `/dia 2026-11-05`) |
| `/imprimir [data] [tipo]` | lista **vazia** em PDF para imprimir |
| `/resultado [data] [tipo]` | lista **preenchida** em PDF para imprimir |
| `/reenviar [data] [tipo] [hora]` | reenvia resumo + PDF ao grupo |

Convenção: `[entre colchetes]` = opcional; `<entre sinais de menor/maior>` = obrigatório. Por isso
`/dia` mostra `<data>` (sem data ele seria igual a `/hoje`) e os demais mostram `[data]`.

**Parâmetros** (em qualquer ordem, separados por espaço):

- **data**: `05/11`, `05/11/2026` ou `2026-11-05`. Sem data = hoje.
- **tipo**: o nome do checklist (`fechamento`, `abertura`...). Sem tipo, `/hoje` e `/dia` mostram
  todos os tipos; `/imprimir`, `/resultado` e `/reenviar` assumem `fechamento`.
- **hora** (`22:38` ou `22h38`, só em `/hoje`, `/dia`, `/resultado` e `/reenviar`): escolhe o
  checklist **iniciado** nesse horário. Útil quando o mesmo checklist foi feito mais de uma vez no
  dia (nada é sobrescrito: cada um fica guardado separado, por 7 dias). Sem hora, `/hoje` e `/dia`
  mostram **todos** e `/resultado` e `/reenviar` usam o mais recente, avisando os horários dos outros.

Exemplos (copie e troque pelos seus valores):

| Quero... | Envie |
|---|---|
| ver o andamento de hoje | `/hoje` |
| ver só a abertura de hoje | `/hoje abertura` |
| ver o dia 5 | `/dia 05/11` |
| imprimir a lista vazia de amanhã | `/imprimir 06/11` |
| imprimir o último fechamento de hoje, preenchido | `/resultado` |
| imprimir o fechamento do dia 5 | `/resultado 05/11` |
| imprimir o fechamento do dia 5 iniciado às 18:30 | `/resultado 05/11 fechamento 18:30` |
| reenviar ao grupo o fechamento de hoje iniciado às 22:38 | `/reenviar 22:38` |

`/imprimir` gera a lista com as etapas que valem naquele dia da semana (segundas, feriados etc.
seguem as regras do YAML).

## Quem pode usar (lista de acesso)

Só quem está em `ALLOWED_USER_IDS` (no `.env`) usa o bot; todos os outros recebem o próprio ID.

1. O funcionário abre o bot e envia `/start`. Se ainda não tem acesso, o bot responde com
   **"Seu ID de usuário: 123456789"**.
2. Ele envia esse número a quem cuida do servidor (junto com o nome, para você saber de quem é).
3. Essa pessoa adiciona o número em `ALLOWED_USER_IDS`, separado por vírgula, e salva o `.env`.
   **Não precisa reiniciar**: o bot relê o arquivo sozinho. Para remover alguém, tire o número.

Quem for usar `/hoje`, `/resultado` etc. direto no grupo da gerência também precisa estar na lista.

## Rodando

**Primeira vez?** Siga o passo a passo completo em
[`docs/guia-primeiro-teste.md`](docs/guia-primeiro-teste.md). Resumo:

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Windows: copy .env.example .env  | preencha o BOT_TOKEN
python bot.py
```

Requer **Python 3.9 ou mais novo** (recomendado 3.11+).

1. Crie o bot com o `@BotFather` (`/newbot`) e coloque o token em `BOT_TOKEN`.
2. Rode `python bot.py` e, em conversa privada com o bot, envie `/start`: ele responde com o **seu
   ID de usuário**. Coloque em `ALLOWED_USER_IDS` e salve o `.env` (sem reiniciar). Sem isso,
   **ninguém** consegue usar o bot.
3. Crie o grupo que receberá os relatórios, adicione o bot e envie `/start` no grupo: ele mostra
   o **"ID deste chat"** (número negativo). Coloque em `MANAGER_CHAT_ID` e salve.
   Para trocar de grupo (ou enviar a uma pessoa só) depois, basta trocar esse número e salvar.

> **Onde rodar:** o bot precisa estar ligado na hora do fechamento. No Divino Fogão ele roda num
> **notebook Windows dedicado** (sempre na tomada e no Wi-Fi). O passo a passo para deixá-lo
> iniciando sozinho, sem suspender e voltando se travar está em
> [`docs/guia-servidor-windows.md`](docs/guia-servidor-windows.md) (scripts em `servidor/`).
> O bot usa *polling*: não precisa de IP fixo, domínio nem abrir portas no roteador.

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
- **Novo tipo de checklist** (ex.: limpeza): copie `abertura.yaml` para `limpeza.yaml`
  (nesta pasta), troque `tipo`, `comando`, `nome` e as etapas. O comando (`/limpeza`) **funciona na
  hora, sem reiniciar**. O nome do arquivo é o tipo, e o `comando` aceita só letras minúsculas,
  números e `_`. Para o comando aparecer no menu do Telegram, atualize `/setcommands` no
  @BotFather (opcional).
- Se um YAML tiver erro, o bot registra no log e avisa quem usar aquele checklist; os demais
  continuam funcionando.
- **Outra loja**: copie `lojas/divino-fogao/` para `lojas/<novo-id>/`, ajuste e rode com
  `LOJA=<novo-id>` (um bot/token por loja).
- **Configuração fora da pasta do código** (recomendado em servidor): copie `lojas/` para outra
  pasta (ex.: `C:\bot-config\lojas`) e aponte `LOJAS_DIR` no `.env`. Assim, atualizar o código
  (ZIP ou `git pull`) nunca sobrescreve os checklists editados. O mesmo vale para
  `ARCHIVE_DIR` e `LOG_DIR`.

## Dados guardados

Fotos, `resultado.json` e PDFs ficam em `arquivo/<loja>/AAAA-MM-DD/<tipo>_HHMM/` e são
**apagados após 7 dias** (`RETENCAO_DIAS`). As fotos só servem para montar o PDF (e para
`/reenviar`, durante esses 7 dias). O progresso do checklist em andamento fica em
`estado.pickle`, então reiniciar o bot não perde o que já foi respondido.

## Estrutura do código

```
bot.py                  # adaptador do Telegram (comandos, botões, fotos, envio)
nucleo/
  checklist.py          # seções, etapas e regras por dia (YAML)
  sessao.py             # máquina de estados de um checklist em andamento
  relatorio.py          # resumo em texto e progresso do dia
  pdf.py                # PDF do relatório e listas para impressão
  arquivo.py            # fotos, resultado.json e retenção
  loja.py               # configuração por loja
  entrega.py            # interface do canal de entrega (hoje: Telegram)
  logs.py               # log em arquivo com rotação (e sem o token do bot)
lojas/                  # dados de cada loja
servidor/               # scripts Windows: iniciar com o PC, reiniciar se cair, atualizar
docs/                   # guias
tests/                  # pytest
```

## Documentação

- [`docs/guia-primeiro-teste.md`](docs/guia-primeiro-teste.md): criar o bot e testar tudo no seu computador.
- [`docs/guia-servidor-windows.md`](docs/guia-servidor-windows.md): instalar e manter o bot no notebook do restaurante.

## Logs

Os logs ficam em `logs/bot.log` (rotação automática, ~6 MB no máximo). O token do bot **não** é
escrito neles.

## Testes

```bash
pip install -r requirements-dev.txt
pytest
```

## Próximos passos

- Demais checklists além de fechamento e abertura (criar o YAML de cada um)
- Página web para acompanhar as tarefas por dia (os dados já ficam em `resultado.json`)
- Lembrete automático se o fechamento não começar até certo horário

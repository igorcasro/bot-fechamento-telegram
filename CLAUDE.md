# CLAUDE.md

Guia para o Claude (e para quem for contribuir) neste repositório. Escreva código,
commits e mensagens ao usuário final em **português do Brasil**.

## O que é o projeto

Bot de Telegram que conduz os checklists de rotina do restaurante **Divino Fogão**
(Shopping Plaza Campos Gerais, Ponta Grossa/PR). A equipe responde cada etapa pelo
Telegram (status, foto, observação) e, ao final, o bot gera um **relatório em PDF** e
um **resumo em texto**, enviados a um grupo da gerência.

Hoje a equipe faz o fechamento manualmente; o bot substitui esse processo. O modelo do
relatório vem de um PDF de fechamento (03/11/2026) feito pelo colega que iniciou a
automação; o código dele não está disponível, só o PDF.

## Arquitetura

```
bot.py                 # ÚNICO lugar que importa Telegram: comandos, botões, fotos, envio
fechamento/
  checklist.py         # Checklist/Etapa, seções e regras por dia (dias/datas/exceto)
  sessao.py            # Sessao: máquina de estados (status, fotos, obs, finalizar)
  relatorio.py         # resumo_texto() e progresso_texto()
  pdf.py               # gerar_relatorio_pdf() e gerar_lista_pdf() (reportlab)
  arquivo.py           # fotos, resultado.json, retenção (7 dias)
  loja.py              # Loja: nome, local, fuso, logo, checklists
  entrega.py           # CanalEntrega (Protocol); TelegramEntrega está em bot.py
lojas/<id>/            # dados da loja: loja.yaml, logo.png, checklists/<tipo>.yaml
tests/                 # pytest (lógica, PDFs e fluxo completo dos handlers)
```

Regras de dependência: `fechamento/` **não importa Telegram**. `bot.py` só adapta.

### Modelo de dados

- **Checklist** = seções → etapas, lido de `lojas/<loja>/checklists/<tipo>.yaml`.
  `Checklist.para_data(data)` filtra as etapas do dia; os índices das etapas são sempre
  relativos a essa lista filtrada.
- **Etapa**: `titulo`, `instrucao`, `foto` (`obrigatoria|opcional|nenhuma`), `fotos` (qtd),
  `nao_se_aplica` (bool), `dias`, `datas`, `exceto`. Precedência: `exceto > datas > dias`;
  com `datas` e sem `dias` a etapa vale só nessas datas.
- **Status**: `concluido`, `problema`, `nao_se_aplica`, `nao_realizado` (etapa sem resposta
  ao finalizar).
- **Sessao**: estado de um checklist em andamento; serializa para dict (pickle do
  Telegram e `resultado.json`). Pasta: `AAAA-MM-DD/<tipo>_HHMM`.
- `resultado.json` (snapshot do checklist + sessão) é gravado a **cada resposta**, não só ao
  finalizar: assim `/hoje` mostra o andamento de qualquer chat e dá para regenerar PDFs/listas
  mesmo que o YAML mude depois. `finalizado_em` vazio = em andamento. `/cancelar` apaga a pasta.

### Fluxo de uma etapa

Botões de status → Concluído: foto obrigatória (precisa das `fotos`), opcional (pode
"Continuar sem foto") ou nenhuma / Problema: observação (texto) e/ou fotos + botão
Continuar / Não se aplica: avança. Álbuns de fotos enviados de uma vez são anexados à
etapa que acabou de fechar (não "vazam" para a próxima).

## Decisões já tomadas (com o usuário)

- Evoluir a base existente (não recomeçar).
- **Acesso**: lista de IDs em `ALLOWED_USER_IDS` no `.env`, **vazia = ninguém usa** (negado por
  padrão). Quem não está na lista recebe o próprio ID (`/start` é aberto) para enviar a quem
  cuida do servidor (o colega do usuário), que o adiciona ao `.env`. O bot relê o `.env` quando o
  arquivo muda (`Contexto.recarregar_env`), sem reiniciar; vale para `ALLOWED_USER_IDS` e
  `MANAGER_CHAT_ID`.
- **Uso em conversa privada**: funcionários usam o bot em chat privado (em grupo o Telegram não
  entrega fotos/textos soltos ao bot). `iniciar()` recusa em grupo. O grupo só recebe relatórios.
- **Fotos só no PDF**: o bot nunca devolve foto/álbum em conversa nem no grupo; só envia texto e
  PDF (`TelegramEntrega` usa apenas `send_message` e `send_document`; há teste estrito disso).
  O funcionário recebe só uma confirmação curta; o resumo vai ao grupo (se o envio falhar ou não
  houver grupo, o resumo aparece para o funcionário, para não perder a informação).
- **O grupo pode mudar**: `MANAGER_CHAT_ID` é lido na hora do envio (sem reiniciar); o usuário
  pode trocar de grupo ou mandar para uma pessoa só.
- **Mais passos e mais checklists**: um YAML por tipo em `lojas/<loja>/checklists/`; o nome do
  arquivo é o tipo e `comando:` define o `/comando` (padrão: `fechamento`->`/fechar`,
  `abertura`->`/abrir`, outros usam o nome do tipo). Comandos dinâmicos (`cmd_dinamico`), então
  um novo YAML funciona sem reiniciar. A sessão guarda uma **cópia** do checklist: editar o YAML
  no meio de um checklist em andamento não afeta ele.
- **Servidor**: o bot vai rodar num notebook antigo do colega do usuário, deixado no restaurante.
  (Ainda falta definir o sistema operacional e como iniciar o bot automaticamente.)
- Lista inicial de etapas = a do PDF de referência (21 etapas: Cozinha e Atendimento);
  o usuário vai editar depois, incluindo dias e atividades.
- Resumo + PDF vão para **um grupo** do Telegram por enquanto (`MANAGER_CHAT_ID`); pode
  virar uma pessoa só trocando o ID.
- **WhatsApp fica para depois**: implementar `CanalEntrega` e adicionar em `ctx.canais`.
  Não implementar sem o usuário escolher o serviço (API oficial/terceiros, com custo).
- Foto obrigatória/opcional/nenhuma configurada por etapa no YAML.
- Uma loja hoje, mas com estrutura multi-loja (`LOJA=<id>`, um bot/token por loja).
- Retenção de fotos/PDFs: **7 dias** (`RETENCAO_DIAS`).
- Acompanhamento por dia: comandos do bot (`/hoje`, `/dia`). Página web é opcional e só
  se for fácil (os dados já estão em `resultado.json`).
- Impressão: PDFs `/imprimir` (lista vazia) e `/resultado` (lista preenchida), com seções
  separadas e caixas de marcação.

## Convenções

- Conteúdo do checklist fica em YAML; não hardcodar etapas em Python.
- Toda regra nova ganha teste em `tests/`. O teste `tests/test_bot_fluxo.py` simula um
  fechamento completo pelos handlers (sem rede); mantenha-o passando.
- Datas/horas no fuso da loja (`Loja.agora()`, padrão `America/Sao_Paulo`).
- Mudanças em `Sessao.to_dict/from_dict` devem ser retrocompatíveis (há `estado.pickle` e
  `resultado.json` antigos) ou ter migração.
- Textos no Telegram usam HTML (`parse_mode=HTML`): escape com `h()`/`html.escape`.
- No PDF use só fontes padrão (Helvetica): evite emojis e caracteres fora do Latin-1.
- Antes de concluir mudanças no PDF, gere um exemplo e **olhe o resultado** (por exemplo
  `pdftoppm -r 60 -png arquivo.pdf pagina`): quebras de página e títulos órfãos só aparecem
  visualmente.

## Comandos

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env     # preencher BOT_TOKEN e MANAGER_CHAT_ID
python bot.py            # roda o bot (polling)
pytest                   # testes
```

## Segurança e privacidade

- **Nunca** commitar `.env`, `estado.pickle` nem `arquivo/` (já no `.gitignore`).
- `BOT_TOKEN` é segredo; não logar nem colocar em exemplos.
- Fotos do restaurante podem mostrar pessoas/dados; não usar fotos reais em testes,
  fixtures ou no repositório (os testes geram imagens sintéticas).
- O acesso é negado por padrão: `ALLOWED_USER_IDS` vazio bloqueia todos.

## Git

- O usuário autorizou push direto na `main` neste repositório. Mesmo assim, commits
  pequenos, em português, descrevendo o "porquê".

## Pendências em aberto

- **Servidor**: notebook antigo no restaurante (decidido). Falta saber o sistema operacional,
  como iniciar o bot sozinho ao ligar/reiniciar, impedir suspensão e queda de energia/Wi-Fi.
- Logo em `lojas/divino-fogao/logo.png` tem só ~300 px de largura (sai levemente
  serrilhada no PDF); trocar por uma versão maior quando houver.
- Checklist de **abertura** e checklists por dia: o usuário vai fornecer.
- Página web de acompanhamento (opcional) e lembretes automáticos.
- Envio por WhatsApp.
- Testar com um bot real no Telegram (o desenvolvimento aqui foi feito sem rede para o
  Telegram; os testes usam objetos simulados).

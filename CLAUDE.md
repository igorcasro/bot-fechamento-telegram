# CLAUDE.md

Guia para o Claude (e para quem for contribuir) neste repositório. Escreva código,
commits e mensagens ao usuário final em **português do Brasil**.

## O que é o projeto

Bot de Telegram que conduz os checklists de rotina do restaurante **Divino Fogão**
(Shopping Plaza Campos Gerais, Ponta Grossa/PR). A equipe responde cada etapa pelo
Telegram (status, foto, observação) e, ao final, o bot gera um **relatório em PDF** e
um **resumo em texto**, enviados à gerência.

Hoje a equipe faz o fechamento manualmente; o bot substitui esse processo.

## Estado atual (base já existente)

- `bot.py` – handlers do Telegram, envio do relatório (texto + fotos).
- `closing.py` – regras do checklist e da sessão, **sem dependência do Telegram**.
- `checklist.yaml` – etapas do checklist (editável sem mexer em código).
- `tests/test_closing.py` – testes da lógica (pytest).
- Estado em `estado.pickle`, fotos arquivadas em `arquivo/AAAA-MM-DD/`.

Comandos: `/start`, `/fechar`, `/status`, `/pular motivo`, `/cancelar`.

A decisão tomada com o usuário foi **evoluir esta base**, não recomeçar.

## Relatório de referência

O modelo do relatório é o PDF de fechamento de 03/11/2026 (gerado pelo colega que
iniciou a automação; o código dele não está disponível, só o PDF). O PDF deve conter:

- Logo, título "Relatório de Fechamento da Loja", loja/cidade.
- Cabeçalho: data, responsável, início, término, duração, total de fotos.
- Painel de contagem: **Concluídas / Com problema / Não se aplica / Não realizadas**.
- Bloco "Atenção: pendências e problemas" listando cada etapa com problema e a observação
  (ou "(sem descrição)").
- Detalhamento por seção (ex.: COZINHA, ATENDIMENTO), com etapas numeradas de forma
  contínua; cada etapa mostra status, horário, foto(s) com horário e observação.
- Etapas podem ser confirmadas **sem foto** ("Confirmado, sem foto.").
- Rodapé com loja, tipo de checklist, data, responsável e número de página;
  linha final "Relatório gerado automaticamente em DD/MM/AAAA HH:MM".

Melhorias já identificadas sobre o PDF do colega: miniaturas menores (o PDF saiu com 8
páginas só por causa do tamanho das fotos) e não deixar título de seção órfão no fim
da página.

Além do PDF, enviar um **resumo em texto** (mesmos números, lista de problemas).

## Requisitos e roadmap

1. **Modelo de etapa**: status por etapa (`concluido`, `problema`, `nao_se_aplica`,
   `nao_realizado`), horário, observação, foto opcional/obrigatória por etapa, seções.
2. **Fluxo no Telegram**: botões inline para o status; foto e observação quando fizer
   sentido; registrar horário de cada resposta.
3. **Relatório**: gerar PDF + resumo em texto ao final e enviar ao grupo do gerente.
4. **Vários tipos de checklist**: além do fechamento, o de **abertura** (e outros).
   Cada tipo tem seu comando/arquivo.
5. **Checklist por dia**: os passos mudam conforme o dia. Definição **por dia da semana
   + datas especiais** (feriados/exceções). O bot descobre o dia corrente (fuso
   `America/Sao_Paulo`) e monta o checklist correspondente.
6. **Visão de acompanhamento** (talvez): ver tarefas por dia, o que foi feito e o que
   falta.
7. **Impressão**: versões imprimíveis para o restaurante, **lista vazia** (para marcar à
   mão) e **lista com resultados**.
8. **WhatsApp**: decisão atual é **Telegram primeiro**; o envio de PDF/resumo deve ficar
   atrás de uma interface de "canal de entrega" para plugar o WhatsApp depois (exige API
   oficial/terceiros). Não implementar WhatsApp sem o usuário definir o serviço.

## Convenções

- Lógica de negócio em `closing.py` (ou módulos novos) **sem importar Telegram**; o
  `bot.py` só adapta. Mantenha assim para testar e para reaproveitar na impressão/PDF.
- Conteúdo do checklist fica em YAML; não hardcodar etapas em Python.
- Toda regra nova ganha teste em `tests/`.
- Datas/horas sempre no fuso `America/Sao_Paulo`.
- Mudanças de formato do estado persistido (`Session.to_dict`/`from_dict`) devem ser
  retrocompatíveis ou ter migração.

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
  fixtures ou no repositório.
- Restringir o uso por `ALLOWED_USER_IDS` em produção.

## Git

- Desenvolva em branch própria e abra PR para `main`; não faça push direto na `main`.
- Commits pequenos, em português, descrevendo o "porquê".

## Pendências em aberto (confirmar com o usuário antes de assumir)

- Lista real de etapas por dia da semana (hoje o `checklist.yaml` tem 8 etapas genéricas;
  o PDF de referência tem 21, em Cozinha e Atendimento).
- Arquivo do logo (Divino Fogão) para o PDF e licença de fonte, se houver.
- Quem recebe o relatório (um grupo? mais de uma pessoa?) e se o resumo vai no mesmo chat.
- Foto obrigatória ou opcional por etapa (o PDF mostra etapas confirmadas sem foto).
- Uma loja só, ou várias lojas no futuro?
- Onde o bot vai rodar (VPS, Docker, máquina do restaurante) e por quanto tempo guardar
  as fotos.
- Layout da lista impressa (vazia e preenchida) e se a visão de acompanhamento será web
  ou só comandos do bot.

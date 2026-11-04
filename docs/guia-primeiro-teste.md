# Guia: primeiro teste do bot no seu computador

Este guia leva você do zero até um fechamento completo funcionando no Telegram, rodando no
**seu** computador (Windows). Depois de testar aqui, o passo para o notebook do restaurante está
em [`guia-servidor-windows.md`](guia-servidor-windows.md).

Tempo estimado: 30 a 45 minutos. Você vai precisar de: o Telegram no celular, um computador com
internet e, de preferência, **uma segunda pessoa** (ou uma segunda conta do Telegram) para testar
o controle de acesso.

> **Importante:** este bot foi desenvolvido sem acesso ao Telegram real (os testes automatizados
> simulam o Telegram). Você está fazendo o **primeiro teste de verdade**. Se algo estranho
> acontecer, anote **o que fez, o que esperava e o que aconteceu** (a seção 7 diz como). É
> exatamente isso que ajuda a corrigir.

---

## 1. Criar o bot no Telegram

1. No Telegram, procure **@BotFather** (o que tem o selo azul de verificado) e toque em **Iniciar**.
2. Envie `/newbot`.
3. Ele pergunta o **nome** do bot (aparece nas conversas), por exemplo `Divino Fogão Checklist`.
4. Depois pergunta o **username**: precisa terminar em `bot` e ser único. Ex.:
   `divinofogao_checklist_bot`. Se já existir, tente outro.
5. Ele responde com o **token**, parecido com `1234567890:AAH...`. **Copie.**

> O token é uma **senha**. Não envie para ninguém e não coloque em lugar público. Se vazar,
> envie `/revoke` ao BotFather para gerar outro.

---

## 2. Instalar o Python

1. Acesse **python.org/downloads** e baixe a versão mais recente.
   **Não use** a versão da Microsoft Store.
2. No instalador, marque **Add python.exe to PATH** e clique em **Install Now**.
3. Abra o **Prompt de Comando** (tecla Windows, digite `cmd`) e verifique:

```bash
python --version
```

Deve aparecer `Python 3.x.x`. Se der erro ou abrir a Microsoft Store, reinstale marcando o PATH.

---

## 3. Baixar o projeto e instalar as dependências

1. Abra o repositório no GitHub (você tem acesso) → **Code → Download ZIP**.
2. Extraia em `C:\bot-fechamento`. **Confira:** o arquivo `bot.py` deve estar direto dentro de
   `C:\bot-fechamento`, e não numa pasta dentro dela.
3. No Prompt de Comando:

```bash
cd C:\bot-fechamento
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Verifique:** no final aparece `Successfully installed ...` e nenhuma linha vermelha.

---

## 4. Configurar o token

```bash
copy .env.example .env
notepad .env
```

No Bloco de Notas, preencha **só o token por enquanto** (sem aspas e sem espaços ao redor do `=`):

```text
BOT_TOKEN=1234567890:AAH...cole-aqui
ALLOWED_USER_IDS=
MANAGER_CHAT_ID=
```

Salve com **Ctrl+S** e feche.

---

## 5. Ligar o bot e liberar você mesmo

### 5.1 Ligar

```bash
.venv\Scripts\python.exe bot.py
```

**O que deve aparecer** (as linhas de aviso são normais neste momento, pois ainda não há IDs):

```text
... WARNING checklist-bot: ALLOWED_USER_IDS vazio: ninguém conseguirá usar o bot até cadastrar IDs.
... WARNING checklist-bot: MANAGER_CHAT_ID não definido: relatórios não serão enviados.
... INFO checklist-bot: Loja: Divino Fogão | checklists: fechamento | usuários liberados: 0
```

**Deixe essa janela aberta**: o bot só funciona enquanto ela estiver rodando. Para parar, use
**Ctrl+C**.

Se aparecer `O Telegram recusou o BOT_TOKEN`, o token está errado: copie de novo do
`@BotFather`. Se aparecer `Sem conexão com o Telegram`, verifique a internet.

### 5.2 Descobrir o seu ID

No celular, abra uma **conversa privada** com o bot (procure o username e toque em **Iniciar**)
e envie `/start`. Como você ainda não está liberado, ele responde algo como:

```text
Você ainda não tem acesso aos checklists.
Envie o número abaixo ao responsável para liberar o seu acesso:

Seu ID de usuário: 123456789
ID deste chat: 123456789
```

### 5.3 Liberar o seu ID

1. Abra o `.env` de novo: no Prompt (em **outra janela**, com a primeira ainda rodando) digite
   `notepad C:\bot-fechamento\.env`.
2. Preencha com o seu número e salve:

```text
ALLOWED_USER_IDS=123456789
```

3. Envie `/start` ao bot novamente. **Não precisa reiniciar o bot.** Agora ele responde com a
   lista de comandos (`/fechar`, `/status`, `/hoje`...). Na janela do Prompt aparece a linha
   `.env recarregado`.

---

## 6. Criar o grupo dos relatórios

1. No Telegram, crie um **novo grupo** (ex.: "Relatórios Divino Fogão - TESTE").
2. Adicione o seu bot ao grupo (procure pelo username).
3. No grupo, envie `/start`. O bot responde com o **ID deste chat**, um número **negativo**,
   como `-1001234567890`.
4. Abra o `.env`, preencha e salve (sem reiniciar):

```text
MANAGER_CHAT_ID=-1001234567890
```

> Se mais tarde o Telegram transformar o grupo em "supergrupo", o ID muda. Basta repetir este
> passo e trocar o número.

---

## 7. Roteiro de testes

Faça nesta ordem e marque o que funcionou. **Anote o que estranhar.**

### Teste 1: um fechamento completo

Na **conversa privada** com o bot:

1. Envie `/fechar`. O bot mostra "Vamos começar: Fechamento da Loja" e a etapa 1, com os botões
   **Concluído / Problema / Não se aplica**.
2. Toque **Concluído** → o bot pede uma foto → envie **uma foto qualquer** (de um objeto, não de
   pessoas). Deve responder "Etapa registrada" e mostrar a etapa 2.
3. Na etapa **"Coifa desligada e aberta"** (foto opcional): toque Concluído e depois
   **Continuar sem foto**.
4. Numa etapa, toque **Problema**: escreva um texto ("Ficou sujo"), envie uma foto e toque
   **Continuar**.
5. Na etapa **"Carne descongelando"**, toque **Não se aplica**.
6. Responda mais algumas etapas e envie `/status` (deve mostrar a etapa em que você está).
7. Envie `/finalizar` → toque **Sim, finalizar** (o que ficou sem resposta vira "não realizada").

**Esperado:**

- No **grupo**: chega **uma mensagem de resumo** e **um arquivo PDF**.
- Na **conversa privada**: só uma confirmação curta ("Checklist concluído! O relatório foi
  enviado ao grupo"). **Nenhuma foto** volta para o grupo nem para você.
- Abra o **PDF** e confira: logo, data, responsável, horários, contagem por status, bloco
  "Atenção" com o problema e a observação, fotos nas etapas certas.

### Teste 2: comandos de acompanhamento e impressão

Ainda na conversa privada:

| Comando | Esperado |
|---|---|
| `/hoje` | Lista das etapas de hoje com ✅ ⚠️ ➖ ⏳ |
| `/dia 05/11` (ou outra data) | Mostra aquele dia (sem registros, "Nada registrado") |
| `/imprimir` | PDF com a lista **vazia**, caixinhas e seções separadas |
| `/resultado` | PDF com a lista **preenchida** do que você fez |
| `/reenviar` | O grupo recebe o resumo e o PDF de novo |

### Teste 3: cancelar

1. `/fechar`, responda uma etapa com foto e envie `/cancelar`.
2. **Esperado:** "Checklist cancelado. Nada foi enviado ao grupo." E `/hoje` não mostra mais
   esse checklist.

### Teste 4: regras de acesso

1. Peça a **outra pessoa** (outra conta do Telegram) para enviar `/start` ao bot: ela deve
   receber o **ID dela** e a mensagem de que ainda não tem acesso. Se tentar `/fechar`, recebe
   a mesma mensagem.
2. Adicione o ID dela em `ALLOWED_USER_IDS` (separado por vírgula: `123456789,987654321`) e
   salve. **Sem reiniciar**, ela já consegue usar.
3. Envie `/fechar` **dentro do grupo**: o bot deve responder que é preciso usar a conversa
   privada.

### Teste 5: reiniciar no meio

1. Comece um `/fechar` e responda 2 ou 3 etapas.
2. Na janela do Prompt, **Ctrl+C** (para o bot) e ligue de novo
   (`.venv\Scripts\python.exe bot.py`).
3. Envie `/status`: o bot deve continuar **de onde parou**.

### Teste 6: editar o checklist

1. Abra `C:\bot-fechamento\lojas\divino-fogao\checklists\fechamento.yaml` no Bloco de Notas
   (o recuo é feito com **espaços, nunca Tab**).
2. Acrescente uma etapa nova no fim de uma seção, copiando o formato das outras, e salve.
3. Envie `/hoje`: a etapa nova deve aparecer (sem reiniciar o bot).

### Teste 7 (opcional): um segundo tipo de checklist

Copie `fechamento.yaml` para `abertura.yaml` (mesma pasta), troque `comando: fechar` por
`comando: abrir`, `nome:` por "Abertura da Loja" e ajuste as etapas. Envie `/abrir`: deve
iniciar o checklist de abertura, sem reiniciar o bot.

---

## 8. Se algo der errado

| O que aparece | O que fazer |
|---|---|
| `Defina BOT_TOKEN no arquivo .env` | O `.env` não está em `C:\bot-fechamento` ou o Windows salvou como `.env.txt`. Use sempre `notepad .env` pelo Prompt (e confirme com `dir` que existe `.env`, e não `.env.txt`). |
| `O Telegram recusou o BOT_TOKEN` | Token errado. Copie de novo do `@BotFather`, sem espaços nem aspas. |
| `Sem conexão com o Telegram` | Sem internet, ou a rede bloqueia o Telegram (algumas redes corporativas/escolares bloqueiam). Tente por outra rede (ex.: compartilhar a internet do celular). |
| `Conflict: terminated by other getUpdates` | O bot está rodando em **dois lugares** com o mesmo token. Feche a outra janela ou outro computador. |
| O bot não responde nada | A janela do Prompt com o bot está aberta e sem erro? Você está falando com o bot certo? |
| Responde "Você ainda não tem acesso" | O ID não está em `ALLOWED_USER_IDS` (confira o número e a vírgula) ou o arquivo não foi salvo. |
| O relatório não chega ao grupo | `MANAGER_CHAT_ID` está certo (com o `-`) e o bot está no grupo? O bot avisa na conversa se falhar; depois use `/reenviar`. |
| Mensagem "😕 Algo deu errado" | Veja o final do arquivo `logs\bot.log` e me envie as últimas linhas (o token **não** aparece nele). |

### O que me enviar quando algo estranhar

1. O **que você fez** (qual comando/botão) e **o que esperava**.
2. **O que aconteceu** (mensagem exata ou print).
3. As últimas ~30 linhas de `C:\bot-fechamento\logs\bot.log`.
4. Se for o PDF: o PDF (use fotos sem pessoas).

---

## 9. Ao terminar

- Para parar o bot: **Ctrl+C** na janela do Prompt.
- As fotos e PDFs do teste ficam em `C:\bot-fechamento\arquivo\` e são **apagados sozinhos
  após 7 dias**. Se quiser, apague a pasta agora.
- Pronto para o notebook do restaurante? Siga o [`guia-servidor-windows.md`](guia-servidor-windows.md).
  Você pode reaproveitar o **mesmo bot e o mesmo grupo**, ou criar um bot novo só para o
  restaurante (assim o teste não se mistura com o uso real).

# Guia: colocar o bot de checklists para rodar no notebook do restaurante (Windows)

Este guia leva o bot de "funciona no meu computador" para "funciona sozinho no notebook do
restaurante, todos os dias". Ao final, o bot:

- liga **sozinho** quando o notebook liga (sem ninguém entrar na conta do Windows);
- **volta sozinho** se travar ou se o Wi-Fi cair;
- continua rodando com a **tampa fechada** e sem entrar em suspensão;
- guarda um **registro (log)** do que aconteceu, para investigar problemas.

Tempo estimado: 40 a 60 minutos, com o notebook conectado à internet.

> **Aviso honesto:** os scripts da pasta `servidor/` foram escritos com cuidado, mas **não puderam
> ser executados em um Windows durante o desenvolvimento** (foram criados num ambiente Linux).
> Por isso o guia tem passos de verificação depois de cada etapa e um "teste de reinício" no fim.
> Se algo falhar, veja a seção **Problemas comuns** e me envie a mensagem de erro.

---

## 0. O que você precisa ter em mãos

| Item | Onde conseguir |
|---|---|
| **Token do bot** | Conversa com o `@BotFather` no Telegram (`/newbot`). É como uma senha: não compartilhe. |
| **Seu ID e o ID de cada funcionário** | Cada pessoa envia `/start` ao bot em conversa privada; ele responde "Seu ID de usuário: …". |
| **ID do grupo que recebe os relatórios** | Crie o grupo, adicione o bot e envie `/start` lá: ele responde "ID deste chat: -100…". |
| **Acesso ao repositório no GitHub** | O repositório `igorcasro/bot-fechamento-telegram` é **privado**: você precisa ser convidado. |
| **Conta de administrador no Windows** | Para instalar programas e rodar os scripts. |

> Os passos para criar o bot e descobrir os IDs estão em
> [`guia-primeiro-teste.md`](guia-primeiro-teste.md). Se ainda não fez o primeiro teste no seu
> computador, **faça primeiro**: ele valida o bot antes de você ir ao restaurante.

---

## 1. Preparar o Windows

### 1.1 Data, hora e fuso

O bot calcula "qual é o dia de hoje" (e as etapas desse dia) pela hora do computador.

1. **Configurações → Hora e idioma → Data e hora**.
2. Ative **Definir fuso horário automaticamente** (ou escolha **(UTC-03:00) Brasília**).
3. Clique em **Sincronizar agora**.

### 1.2 Wi-Fi sempre conectado

1. **Configurações → Rede e Internet → Wi-Fi → Gerenciar redes conhecidas**.
2. Clique na rede do restaurante → **Propriedades** → ative **Conectar automaticamente quando
   estiver ao alcance**.
3. Impeça o Windows de "desligar o Wi-Fi para economizar energia":
   **Gerenciador de Dispositivos** (clique direito no botão Iniciar) → **Adaptadores de rede** →
   duplo clique no adaptador Wi-Fi → aba **Gerenciamento de energia** → **desmarque**
   *Permitir que o computador desligue este dispositivo para economizar energia*.

### 1.3 Atualizações do Windows

O Windows às vezes reinicia sozinho para atualizar. O bot volta sozinho depois, mas é melhor que
isso **não aconteça na hora do fechamento**.

1. **Configurações → Windows Update → Opções avançadas → Horas ativas**.
2. Defina, por exemplo, de **08:00 a 02:00** (o máximo permitido é 18 horas).

### 1.4 Avise a equipe

Cole uma etiqueta no notebook: **"SERVIDOR DO BOT - NÃO DESLIGAR"**.
O checklist tem a etapa "Computador desligado", e ela se refere ao computador do caixa, **não**
a este notebook.

---

## 2. Instalar o Python

1. Acesse **python.org/downloads** e baixe a versão mais recente (3.11 ou mais nova).
   **Não use** a versão da Microsoft Store: ela não funciona bem com tarefas em segundo plano.
2. Abra o instalador e:
   - marque **Add python.exe to PATH**;
   - clique em **Customize installation** → **Next** → marque **Install Python for all users**
     → **Install**.
3. Verifique: abra o **Prompt de Comando** (tecla Windows, digite `cmd`) e rode:

```bash
python --version
```

Deve aparecer algo como `Python 3.13.x`. Se aparecer erro ou abrir a Microsoft Store, reinstale
marcando a opção do PATH.

---

## 3. Baixar o projeto para `C:\bot-fechamento`

A pasta **precisa ser curta e sem espaços** (por isso `C:\bot-fechamento`).

### Opção A (recomendada): Git — facilita as atualizações

1. Instale o **Git para Windows**: **git-scm.com** (pode aceitar todas as opções padrão).
2. No Prompt de Comando:

```bash
cd C:\
git clone https://github.com/igorcasro/bot-fechamento-telegram.git bot-fechamento
```

Como o repositório é privado, vai abrir uma janela para você **entrar no GitHub**. Use a conta
que recebeu o convite.

### Opção B: ZIP

1. No GitHub, abra o repositório → **Code → Download ZIP**.
2. Extraia em `C:\bot-fechamento`. **Confira:** o arquivo `bot.py` precisa estar direto dentro
   de `C:\bot-fechamento` (e não em `C:\bot-fechamento\bot-fechamento-telegram-main\`).

---

## 4. Instalar as dependências

No Prompt de Comando:

```bash
cd C:\bot-fechamento
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

A instalação leva 1 a 2 minutos. **Verifique:** no final deve aparecer
`Successfully installed ...` e nenhuma linha vermelha de erro.

---

## 5. Configurar o arquivo `.env`

```bash
copy .env.example .env
notepad .env
```

Preencha (sem aspas e sem espaços ao redor do `=`):

```text
BOT_TOKEN=1234567890:AAH...seu-token
ALLOWED_USER_IDS=111111111,222222222,333333333
MANAGER_CHAT_ID=-1001234567890
```

- `ALLOWED_USER_IDS`: IDs de **quem pode usar o bot**, separados por vírgula. Vazio = ninguém usa.
- `MANAGER_CHAT_ID`: ID do grupo que recebe o resumo e o PDF (número **negativo**).

Salve com **Ctrl+S**. (Se o Bloco de Notas não deixar salvar, feche e abra de novo com
**botão direito → Executar como administrador**.)

### Recomendado: separar a configuração do código

Os checklists e a logo ficam na pasta `lojas\`, dentro do projeto. Se você atualizar o bot
(ZIP ou `git pull`), essa pasta pode ser sobrescrita e **você perde as edições dos checklists**.
Para evitar, guarde a configuração **fora** da pasta do código:

```bash
xcopy /E /I C:\bot-fechamento\lojas C:\bot-config\lojas
notepad C:\bot-fechamento\.env
```

E acrescente ao `.env`:

```text
LOJAS_DIR=C:\bot-config\lojas
```

Daí em diante, **edite os checklists em `C:\bot-config\lojas\...`** e trate a pasta
`C:\bot-fechamento` como "código: não mexer, só atualizar". Na rotina, a única coisa que se
edita é o `.env` e os arquivos `.yaml` (valores e textos, nunca os arquivos `.py`).

---

## 6. Teste manual (antes de automatizar)

```bash
cd C:\bot-fechamento
.venv\Scripts\python.exe bot.py
```

**O que deve aparecer:** uma linha parecida com

```text
... INFO checklist-bot: Loja: Divino Fogão | checklists: fechamento | usuários liberados: 3
```

Agora, no celular:

1. Em **conversa privada** com o bot, envie `/start`: deve listar os comandos.
2. Envie `/fechar` e faça as primeiras etapas.
3. Envie `/finalizar` e confirme: o **grupo** deve receber o resumo e o PDF.

Quando terminar o teste, volte à janela do Prompt e pressione **Ctrl+C** para parar o bot.

> Se o bot respondeu "Você ainda não tem acesso", o ID da pessoa não está em
> `ALLOWED_USER_IDS`. Adicione e salve o `.env` (não precisa reiniciar).

---

## 7. Instalar como serviço (liga sozinho com o Windows)

1. Clique no botão Iniciar, digite **PowerShell**, clique com o **botão direito** →
   **Executar como administrador**.
2. Rode:

```bash
cd C:\bot-fechamento
powershell -ExecutionPolicy Bypass -File .\servidor\instalar-windows.ps1
```

O script faz três coisas (todas com mensagem `[ok]` ao final):

1. cria uma **tarefa agendada** chamada `BotChecklistRestaurante` que inicia o bot quando o
   Windows liga, mesmo sem ninguém logado, e que o reinicia se ele cair (o arquivo
   `servidor\iniciar-bot.bat` espera 15 segundos e liga de novo);
2. ajusta a **energia**: na tomada, nunca suspende nem hiberna e **fechar a tampa não faz nada**;
3. **inicia o bot agora**.

**Verifique:**

- No celular, envie `/start` ao bot: ele deve responder.
- Abra o log: `notepad C:\bot-fechamento\logs\bot.log` (ou o arquivo
  `C:\bot-fechamento\logs\servico.log`, que mostra cada vez que o bot é ligado).

> O bot **não** deve ficar rodando em dois lugares ao mesmo tempo (por exemplo, no notebook e
> no seu computador). Isso causa o erro "Conflict" e nenhum dos dois funciona direito.
> Se estava testando com `python bot.py` aberto, feche-o (Ctrl+C) antes de instalar.

---

## 8. Testes finais (não pule!)

### 8.1 Teste de reinício sem entrar na conta

1. Reinicie o notebook (**Iniciar → Energia → Reiniciar**).
2. **Não entre na conta do Windows.** Deixe na tela de login.
3. Espere uns 3 minutos e envie `/start` ao bot pelo celular.

Se respondeu: está certo. (Se o Wi-Fi demorar a conectar, o bot tenta de novo a cada 15 segundos até a internet voltar.) Se **não** respondeu, veja o item "O bot não responde depois de
reiniciar" em *Problemas comuns* (geralmente é o Wi-Fi não conectar antes do login).

### 8.2 Teste de queda do bot

1. Com o bot rodando, abra o **Gerenciador de Tarefas** (Ctrl+Shift+Esc) → aba **Detalhes**.
2. Encontre o `python.exe` do bot (se houver vários, o que usa mais memória) e **Finalizar tarefa**.
3. Em cerca de 20 segundos, o bot deve voltar a responder.

### 8.3 Teste da tampa

Feche a tampa por 2 minutos e envie `/start`. Deve responder.

### 8.4 Teste de ponta a ponta

Faça um fechamento completo pelo celular de um funcionário e confirme que **o grupo recebeu o
resumo e o PDF**, e que **nenhuma foto** apareceu solta na conversa.

---

## 9. Rotina do dia a dia

| Tarefa | Como fazer |
|---|---|
| **Liberar um funcionário** | A pessoa envia `/start` ao bot e manda o número ("Seu ID de usuário") a quem cuida do servidor. Abra `C:\bot-fechamento\.env`, adicione o número em `ALLOWED_USER_IDS` (separado por vírgula) e salve. **Não precisa reiniciar.** O bot relê o arquivo na **próxima mensagem** que receber, e aí aparece `.env recarregado` no log. |
| **Remover um funcionário** | Apague o número de `ALLOWED_USER_IDS` e salve. |
| **Trocar o grupo dos relatórios** | Troque o número em `MANAGER_CHAT_ID` e salve. Também **não precisa reiniciar**. |
| **Editar etapas do checklist** | Edite `C:\bot-config\lojas\divino-fogao\checklists\fechamento.yaml` (ou `C:\bot-fechamento\lojas\...`, se não separou a configuração). Use o Bloco de Notas; o recuo é feito com **espaços, nunca Tab**. Vale para os **próximos** checklists, sem reiniciar. Teste com `/hoje` no Telegram. |
| **Criar outro checklist (ex.: abertura)** | Copie `fechamento.yaml` para `abertura.yaml` na mesma pasta e ajuste. O comando (`/abrir`) funciona na hora. |
| **Ver o que aconteceu** | `C:\bot-fechamento\logs\bot.log`. O log guarda no máximo ~6 MB (apaga os mais antigos sozinho). |
| **Atualizar o bot** | Se instalou com Git: clique direito em `servidor\atualizar.bat` → **Executar como administrador**. Com ZIP: extraia o novo ZIP em outra pasta e copie o conteúdo por cima de `C:\bot-fechamento`, **exceto a pasta `lojas\`** (se a configuração está em `C:\bot-config`, nada a preservar). O `.env`, `arquivo\` e `estado.pickle` não vêm no ZIP, então não são afetados. Depois reinicie a tarefa (ou o notebook). |
| **Fotos antigas** | Apagadas sozinhas após 7 dias. Nada a fazer. |

> **Cuidado ao editar o YAML:** se ficar com erro, o bot registra no log e avisa quem tentar usar
> aquele checklist, mas os outros checklists continuam funcionando. Revise o último arquivo que
> você alterou.

### Backup (1 vez por mês)

Copie para um pendrive ou para o Google Drive:

- `C:\bot-fechamento\.env` (contém o token: **guarde em lugar seguro, não compartilhe**);
- a pasta de configuração: `C:\bot-config\` (ou `C:\bot-fechamento\lojas\`, se não separou).

As fotos e PDFs dos últimos 7 dias não precisam de backup.

---

## 10. Acesso remoto (opcional, mas útil)

Para liberar funcionários ou editar o checklist sem ir ao restaurante, você precisa controlar
o notebook à distância. Opções comuns: **AnyDesk**, **Chrome Remote Desktop** ou
**TeamViewer** (instalando no notebook com **acesso não supervisionado**).

- Use senha **forte** e, se houver, **verificação em duas etapas**: quem controla o notebook
  controla o bot e o token.
- Anote em local seguro o código de acesso do notebook.

---

## 11. Problemas comuns

| Sintoma | O que verificar |
|---|---|
| **O bot não responde** | 1) O notebook está ligado e com internet? 2) Abra `logs\bot.log` e veja as últimas linhas. 3) No PowerShell (administrador): `Get-ScheduledTask -TaskName BotChecklistRestaurante` mostra o estado (`Running` = rodando). 4) Se estiver parado: `Start-ScheduledTask -TaskName BotChecklistRestaurante`. |
| **Log mostra `O Telegram recusou o BOT_TOKEN`** | O `BOT_TOKEN` no `.env` está errado ou foi revogado. Copie de novo do `@BotFather`, salve e **reinicie a tarefa** (o token só é lido ao ligar). |
| **Log mostra `Sem conexão com o Telegram`** | Sem internet (ou o Wi-Fi ainda não conectou). Não precisa fazer nada: o `iniciar-bot.bat` tenta de novo a cada 15 segundos. Se persistir, veja Wi-Fi e rede. |
| **Log mostra `Conflict: terminated by other getUpdates`** | O bot está rodando em **outro lugar** com o mesmo token (outro computador, ou uma janela do Prompt aberta). Deixe só uma cópia. |
| **`ModuleNotFoundError` em `logs\erro-saida.log`** | As dependências não foram instaladas. Refaça o passo 4. |
| **O bot não responde depois de reiniciar** | Provavelmente o Wi-Fi só conecta depois do login. No notebook, vá em **Configurações → Rede e Internet → Wi-Fi → Gerenciar redes conhecidas**, remova a rede e **reconecte marcando "Conectar automaticamente"**, mantendo a opção de que **vale para todos os usuários**. Depois refaça o teste 8.1. Em último caso, conecte o notebook por cabo de rede. |
| **A tarefa não existe** | Rode de novo o passo 7 (PowerShell **como administrador**). |
| **Funcionário recebe "Você ainda não tem acesso"** | O ID dele não está em `ALLOWED_USER_IDS`. Adicione e salve o `.env`. |
| **O relatório não chega ao grupo** | O funcionário recebe um aviso. Verifique `MANAGER_CHAT_ID` (com o sinal de menos) e se o bot ainda está no grupo. Depois, use `/reenviar` no Telegram. |
| **PDF sem foto em alguma etapa** | A foto pode ter sido apagada (mais de 7 dias) ou a etapa foi concluída sem foto (permitido nas etapas com foto opcional). |
| **Hora errada nos relatórios** | Refaça o passo 1.1 (fuso e sincronização). |

Para desfazer a instalação do serviço: PowerShell como administrador →
`powershell -ExecutionPolicy Bypass -File .\servidor\desinstalar-windows.ps1`.

---

## 12. Plano B: se o bot ou a internet falhar

O bot permite imprimir a lista do dia para preencher **à mão**:

- `/imprimir` → PDF com a lista **vazia** (caixas para marcar, seções separadas);
- `/resultado` → PDF com a lista **preenchida** com o que já foi registrado.

Deixe sempre algumas cópias impressas na loja. Se o bot cair na hora do fechamento, a equipe
preenche o papel, e depois alguém registra no bot ou arquiva o papel.

---

## 13. Segurança, resumo

- O bot só **recebe** informações do Telegram (não abre nenhuma porta no notebook). Não precisa
  configurar o roteador nem o firewall.
- O **token** fica só no `.env` do notebook. Se vazar, no `@BotFather` envie `/revoke`, gere um
  novo e troque no `.env` (aí reinicie o bot).
- Só quem está em `ALLOWED_USER_IDS` usa o bot.
- Ponha **senha** na conta do Windows e mantenha o Windows atualizado (o bot volta sozinho
  depois de cada reinício).

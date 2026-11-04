# Bot de Fechamento de Restaurante (Telegram)

O funcionário digita `/fechar` e o bot conduz o fechamento etapa por etapa,
pedindo uma foto de cada ponto (cozinha, salão, caixa, portas...). No final,
envia ao gerente um relatório com o resumo e todas as fotos.

## Como funciona

1. `/fechar` inicia o checklist.
2. O bot pede a(s) foto(s) da etapa 1; ao receber, avança sozinho para a 2, e assim por diante.
3. Etapas marcadas como `obrigatoria: false` podem ser puladas com `/pular motivo`.
4. Ao terminar, o relatório (texto + fotos por etapa) vai para o chat do gerente
   e as fotos ficam arquivadas em `arquivo/AAAA-MM-DD/`.

Comandos: `/fechar`, `/status`, `/pular motivo`, `/cancelar`.

## Rodando

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # preencha BOT_TOKEN e MANAGER_CHAT_ID
python bot.py
```

1. Crie o bot com o `@BotFather` (`/newbot`) e coloque o token em `BOT_TOKEN`.
2. Crie um grupo com o gerente, adicione o bot e coloque o ID do grupo em `MANAGER_CHAT_ID`.
3. (Opcional) Restrinja quem pode usar em `ALLOWED_USER_IDS`. O `/start` mostra o ID de cada pessoa.

## Personalizando o checklist

Edite `checklist.yaml`: título, instrução, número de fotos e se a etapa é obrigatória.
Não precisa mexer em código.

## Estrutura

```
bot.py            # handlers do Telegram e envio do relatório
closing.py        # regras do fechamento (sem dependência do Telegram)
checklist.yaml    # etapas do restaurante
tests/            # testes da lógica
```

O estado do fechamento fica em `estado.pickle`, então um reinício do bot não perde o progresso.

## Testes

```bash
pytest
```

## Ideias para próximas versões

- Lembrete automático se o fechamento não começar até certo horário
- Várias lojas / vários checklists (abertura e fechamento)
- Painel web ou planilha com o histórico dos fechamentos
- Validação básica da foto (ex.: bloqueio de foto repetida)
- Deploy em VPS com `systemd` ou Docker

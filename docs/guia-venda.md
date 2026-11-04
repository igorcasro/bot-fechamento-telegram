# Guia: o que preciso para vender este sistema para outras pessoas

> **Leia primeiro:** este guia reúne o que normalmente é preciso para transformar um sistema que
> funciona em **um** restaurante em um **produto vendável**. Ele é um roteiro de organização, **não
> é aconselhamento jurídico, fiscal ou contábil**. Os trechos sobre contrato, LGPD, trabalhista e
> impostos servem para você saber **o que perguntar** a um advogado e a um contador antes de
> assinar ou cobrar qualquer coisa. Não há valores de preço inventados aqui: no lugar, há um modo
> de calcular o seu.

## Resumo em 1 minuto

Hoje o sistema é um **protótipo validado (ou em validação) em uma loja**. Antes de vender, você
precisa resolver, **nesta ordem**:

1. **Quem é dono do quê** (você, o responsável pelo Projeto 1, o restaurante) e deixar isso **por escrito**.
2. **Tirar a marca do Divino Fogão do produto** e separar o que é "produto" do que é "cliente".
3. **Escolher o modelo de entrega**: instalar no cliente, hospedar você mesmo ou vender o código.
4. Cuidar de **contrato e LGPD** (o sistema guarda nomes/IDs de funcionários e fotos do local).
5. Preparar **suporte e implantação**: quem atende quando o bot cair às 22h40?
6. Fazer os **ajustes técnicos mínimos** da seção 4 (principalmente: o cliente não deveria
   precisar editar arquivos de texto para liberar um funcionário).

A recomendação é **não construir uma plataforma grande antes de ter clientes**: faça um piloto
no Divino Fogão, depois 2 ou 3 clientes pagantes com uma instalação por cliente, e só então
decida se vale investir em algo hospedado e multi-cliente (seção 5).

---

## 1. O que já está pronto

Funcionalidades hoje (verificadas por testes automatizados e por simulação; o uso com o Telegram
real ainda precisa ser validado no piloto):

- Checklist guiado pelo Telegram, etapa por etapa: **Concluído / Problema / Não se aplica**,
  fotos obrigatórias, opcionais ou nenhuma, observações, horário de cada etapa.
- **Relatório em PDF** (com fotos) e **resumo em texto**, enviados a um grupo de gestão.
- **Vários tipos de checklist** (fechamento, abertura, etc.) e **etapas por dia da semana/data**.
- **Listas para imprimir** (vazia e preenchida) e acompanhamento do dia (`/hoje`, `/dia`).
- **Controle de acesso** por lista de IDs; fotos guardadas só por 7 dias; log com rotação.
- Estrutura por loja (`lojas/<id>`), testes automatizados e instalação no Windows.

O que isso **não é ainda**: um produto para clientes não técnicos. Hoje, mudar um checklist ou
liberar um funcionário exige editar arquivos num computador (seção 4).

---

## 2. Propriedade e direitos (resolva ANTES de vender)

### 2.1 Quem é dono do código?

Faça estas perguntas e **registre as respostas por escrito** (um acordo simples assinado pelos
envolvidos já ajuda muito):

| Pergunta | Por que importa |
|---|---|
| O **responsável pelo Projeto 1** iniciou a automação e repassou o modelo do relatório. Ele se considera dono ou sócio de algo? | Sem acordo, qualquer um pode contestar a venda depois. |
| Vocês vão **vender juntos**? Como dividem **receita, suporte e decisões**? | É a causa mais comum de briga em parceria informal. |
| O código dele (que você não viu) entrou neste projeto? | Não entrou: foi usado apenas o **PDF modelo**. Confirme com ele que não há restrição de uso do layout. |
| O **Divino Fogão** tem algum direito sobre o que foi feito (ex.: fez por contrato, foi pago, é sócio)? | Se o sistema foi desenvolvido a pedido/pago pelo restaurante, o contrato pode atribuir a ele direitos ou exigir autorização. |
| Você tem algum **contrato de trabalho/exclusividade** que dê ao empregador direitos sobre o que você cria? | Verifique antes de comercializar. |

### 2.2 Marca, logo e conteúdo do Divino Fogão

- O **nome, a logo e a lista de etapas** do Divino Fogão pertencem ao restaurante. Não podem ir
  para outro cliente nem aparecer em demonstrações sem **autorização por escrito**.
- O PDF de referência contém **nome de funcionário e fotos**: peça autorização antes de usá-lo
  em apresentações.
- Para vender, tenha uma **loja de demonstração genérica** (ex.: "Restaurante Exemplo", logo
  fictícia, checklist de exemplo).

### 2.3 Código gerado com ajuda de IA

Este código foi escrito com apoio do Claude. Em geral, os termos de uso da Anthropic atribuem a
você os resultados gerados na sua conta, mas **leia os termos vigentes** e confirme com seu
advogado se isso é suficiente para o seu caso (por exemplo, para fins de registro e de contrato).

### 2.4 Licenças das bibliotecas usadas

| Biblioteca | Licença | O que isso exige na prática |
|---|---|---|
| python-telegram-bot | **LGPL-3.0** | Pode ser usada em produto comercial **sem modificá-la**. Mantenha o aviso de licença, informe que a usa e **não altere o código dela** (se alterar, as alterações dela precisam ser abertas). Seu código continua seu. |
| ReportLab | BSD | Permissiva: manter o aviso de copyright. |
| Pillow | MIT-CMU (HPND) | Permissiva: manter o aviso. |
| PyYAML | MIT | Permissiva. |
| python-dotenv | BSD-3-Clause | Permissiva. |
| tzdata | Apache-2.0 | Permissiva: manter o aviso. |
| (dependências indiretas, como `httpx`) | em geral BSD/MIT | Conferir. |

Conferi as licenças acima nos metadados das bibliotecas instaladas. Antes de vender, gere a
lista completa (incluindo dependências indiretas) com `pip install pip-licenses` e
`pip-licenses`, e guarde como "avisos de terceiros" junto do produto.

**Licença do seu código:** hoje o repositório **não tem arquivo de licença** (e é privado). Para
vender, defina que o código é **proprietário** ("todos os direitos reservados") e que o cliente
recebe **direito de uso**, e não o código-fonte, a menos que o contrato diga o contrário.

### 2.5 Telegram como canal

- O bot é gratuito de operar (a Bot API não cobra), mas você deve respeitar os **termos do
  Telegram** (leia os Termos de Serviço e as regras para bots).
- **Risco de dependência:** o Telegram pode mudar regras e limites. Seu produto depende dele.
- **Risco comercial:** muitos restaurantes usam WhatsApp, não Telegram. Cada funcionário precisa
  instalar o Telegram. Pergunte ao cliente sobre isso **antes** de vender.
- Recomendação: **cada cliente tem o seu próprio bot** (criado no `@BotFather` com o nome do
  restaurante). Assim a identidade e o token são do cliente, e um problema num bot não afeta os
  outros.
- **WhatsApp:** **decisão do projeto: não implementar.** Para registro, ele exigiria a plataforma
  oficial (Meta) ou serviços de terceiros, com custo recorrente e aprovações. Se um cliente só
  aceitar WhatsApp, isso é **fora do escopo** e muda a conversa comercial (ou o cliente não é o
  público-alvo).

---

## 3. Jurídico, fiscal e LGPD (perguntas para o advogado e o contador)

### 3.1 Formalização e impostos

- Você vai vender como **pessoa física ou jurídica**? Qual **enquadramento** (MEI, Simples,
  outro) permite a atividade de **desenvolvimento/licenciamento de software e suporte**? Cada
  enquadramento tem limites de faturamento e de atividade.
- Como emitir **nota fiscal** (serviço/licença) e qual **CNAE** usar?
- Cobrança recorrente: como receber (boleto, Pix, cartão) e emitir nota todo mês.

### 3.2 Contrato com o cliente

Peça a um advogado um **contrato padrão** (de prestação de serviços e licença de uso) que cubra:

- **O que está incluído:** instalação, quantidade de lojas/checklists/usuários, treinamento.
- **Preço, reajuste, prazo e cancelamento** (e o que acontece com os dados ao cancelar).
- **Suporte e disponibilidade (SLA):** horários de atendimento e prazo de resposta. Atenção ao
  **horário de fechamento da loja**: se o cliente espera suporte às 22h, isso precisa estar
  escrito (e precificado).
- **Limitação de responsabilidade:** o sistema **ajuda a registrar rotinas, mas não substitui**
  obrigações sanitárias, trabalhistas ou de segurança do cliente.
- **Propriedade intelectual:** o software é seu; os **dados e fotos** são do cliente.
- **Confidencialidade** e **proteção de dados** (item 3.3).
- **Mudanças no Telegram ou em serviços de terceiros** fora do seu controle.
- **Customizações** sob demanda: como são pedidas, cobradas e de quem é o resultado.

### 3.3 LGPD (Lei Geral de Proteção de Dados)

O sistema trata **dados pessoais** e é preciso tratá-los com cuidado:

| Dado | De quem | Observação |
|---|---|---|
| **Nome e ID do Telegram** | Funcionários | Identificam a pessoa. |
| **Fotos do local** | Funcionários/clientes que apareçam | Podem mostrar pessoas. Oriente a fotografar **equipamentos e ambientes**, não pessoas. |
| **Horários de cada tarefa** | Funcionários | Podem funcionar como controle de jornada/produtividade. |

Pontos para tratar com o advogado:

- **Papéis:** em geral, o **cliente (restaurante) é o controlador** e **você é o operador**, se
  guardar ou processar dados em servidor seu. Isso exige **cláusulas de tratamento de dados** no
  contrato.
- **Base legal** para tratar os dados dos funcionários e **transparência**: avisar a equipe
  (um comunicado/termo curto) sobre o que é coletado, para quê e por quanto tempo.
- **Minimização e retenção:** já guardamos fotos por **7 dias** (configurável). Documente isso.
- **Segurança:** acesso só por lista de IDs; token protegido; backups; o que fazer em caso de
  **incidente** (vazamento) e quem avisar.
- **Direitos dos titulares:** como atender pedido de exclusão/acesso.
- **Política de privacidade** e **termos de uso** do serviço.
- **Trabalhista:** conversar com o advogado sobre o uso de registros por foto/horário como
  **evidência** em relação a empregados.
- **Alimentos/vigilância sanitária:** não prometa conformidade com normas sanitárias. Diga que o
  sistema **ajuda a documentar rotinas**.

### 3.4 Marca e nome do produto

Antes de dar nome ao produto: pesquise o nome no **INPI** e em redes sociais/domínios; registre
o domínio; só então crie contas e bots com esse nome.

---

## 4. O que falta no produto (ajustes técnicos)

Priorizado pelo que mais atrapalha **vender para quem não é técnico**:

| # | Ajuste | Por que | Esforço |
|---|---|---|---|
| 1 | **Separar produto e cliente**: tirar `lojas/divino-fogao` (logo, textos) do repositório do produto e manter a configuração de cada cliente fora dele (o sistema já aceita outra pasta com `LOJAS_DIR`). Incluir uma loja `exemplo`. | Evita levar a marca e os dados de um cliente para outro. | Baixo |
| 2 | **Gerenciar usuários pelo Telegram** (ex.: comandos `/liberar` e `/remover` para o gerente, com papéis: dono, gerente, funcionário) em vez de editar `.env`. | Hoje exige acesso ao computador. | Médio |
| 3 | **Editar checklists sem YAML** (uma planilha, uma página web simples ou comandos do bot). | O cliente não vai editar arquivos de texto. É o ajuste que mais pesa na venda. | Médio/Alto |
| 4 | **Monitoramento e alertas**: avisar você (ou o gerente) se o bot cair e **lembrar** a equipe se o fechamento não começar até certo horário. | Hoje só descobrimos que caiu quando alguém reclama. | Médio |
| 5 | **Backup** automático da configuração e do histórico, e **histórico maior** que 7 dias (opcional e configurável por contrato). | Segurança e valor para o cliente. | Médio |
| 6 | **Assistente de instalação** que valida o token, o grupo e os IDs antes de ligar. | Reduz erros de configuração em cada novo cliente. | Médio |
| 7 | **Atualização segura** com versões numeradas, histórico de mudanças e como voltar atrás. | Você vai manter vários clientes na mesma versão. | Médio |
| 8 | **Teste com Telegram real** e um período de observação de erros em produção. | Os testes atuais usam objetos simulados. | Baixo (é o piloto) |
| 9 | **Manual do funcionário e do gerente**, com prints (1 página cada) e FAQ. | Reduz suporte. | Baixo |
| 10 | **Painel web** com histórico, filtros e relatórios semanais/mensais. | Diferencial para vender, mas só depois de ter clientes. | Alto |
| 11 | ~~WhatsApp como canal~~ | **Fora do escopo** (decisão do projeto). Só reavaliar se virar requisito de venda. | Alto |
| 12 | **Plataforma multi-cliente hospedada (SaaS)**: banco de dados, login, painel, cobrança, isolamento entre clientes, segurança. | Só vale com muitos clientes. | Muito alto |

---

## 5. Como entregar ao cliente (três modelos)

| Modelo | Como funciona | Vantagens | Desvantagens |
|---|---|---|---|
| **A. Instalado no cliente** (como no Divino Fogão) | Notebook/PC do cliente roda o bot; você instala e dá suporte. | Barato para começar; dados ficam com o cliente. | Depende do computador e do Wi-Fi do cliente; suporte presencial/remoto por instalação. |
| **B. Hospedado por você (uma instalação por cliente)** | Cada cliente tem o seu bot rodando num servidor (VPS) que você administra. | Mais confiável que um notebook; você controla atualização e monitoramento. | Você vira **operador de dados** (LGPD); custo de servidor e responsabilidade de disponibilidade. |
| **C. Plataforma única (SaaS)** | Um sistema atende vários clientes, com painel e cobrança. | Escala. | Grande investimento de desenvolvimento e segurança. |

**Recomendação:** comece com **A** (já funciona) ou **B** (mais profissional), com **1 instalação
por cliente**, até ter uns 3 a 5 clientes. Só então avalie o **C**, usando o que aprendeu.
**Não recomendo** vender o código-fonte no início: perde-se o controle e a receita recorrente.

---

## 6. Preço e custos

Não existe um preço "certo" que eu possa afirmar sem dados do seu mercado. O que faz sentido é
calcular o **piso** e comparar com o que o cliente **ganha**.

### 6.1 Seus custos por cliente

- **Servidor** (modelo B) ou **tempo de instalação** e deslocamento (modelo A).
- **Seu tempo de implantação** (levantar rotinas, montar checklists, treinar) e **de suporte**.
- **Impostos e taxas** de pagamento.
- **Backup e monitoramento.**
- **Divisão de receita** com quem vender junto com você, se houver.

### 6.2 Fórmula do piso da mensalidade

```text
mensalidade mínima = (custo fixo mensal por cliente + horas de suporte × valor da sua hora)
                     ÷ (1 − percentual de impostos e taxas)
```

Cobre também uma **taxa de implantação** única para pagar a instalação e o treinamento.
Pesquise **quanto custam aplicativos prontos de checklist para restaurantes** (existem vários)
para saber a faixa que o mercado aceita.

### 6.3 O valor para o cliente (use no piloto)

Meça no Divino Fogão **antes e depois**, por 2 a 4 semanas: tempo de fechamento, quantas etapas
tiveram problema, quantas ficaram sem registro, equipamentos que ficaram ligados, tempo que o
gerente economiza conferindo. Esses números são o seu argumento de venda, mais do que a lista
de funcionalidades.

---

## 7. Parceria (se vocês forem vender juntos)

Se você for vender junto com o responsável pelo Projeto 1 (ou com qualquer outra pessoa), antes de ganhar o primeiro real definam por escrito:

- **Papéis:** quem vende, quem instala, quem dá suporte, quem programa.
- **Divisão** de receita e de custos (e se muda conforme o trabalho de cada um).
- **Propriedade** do código e do layout do relatório; o que acontece se um deles sair.
- **Decisões** importantes (preço, novos clientes, mudanças grandes) e como resolver divergência.
- **Confidencialidade** e se um pode atender os mesmos clientes por fora.

---

## 8. Checklist para implantar um cliente novo

1. **Contrato assinado**, cláusula de dados incluída e **aviso à equipe** sobre a coleta de dados.
2. **Levantamento das rotinas** com o gerente: etapas, quais precisam de foto, o que muda por dia.
3. Criar o **`checklists/*.yaml`** do cliente (e a pasta da loja com nome e logo dele).
4. Criar o **bot no `@BotFather`** com o nome do cliente (token fica com o cliente) e o **grupo** de relatórios.
5. Coletar os **IDs** dos funcionários e do grupo.
6. **Instalar** o servidor (guia `docs/guia-servidor-windows.md` ou VPS) e fazer todos os **testes finais**.
7. **Treinamento** de 15 a 20 minutos com a equipe (e entregar o manual de 1 página).
8. **Plano B impresso**: deixar cópias de `/imprimir`.
9. **Semana de acompanhamento**: olhar os relatórios, ajustar etapas, corrigir dúvidas.
10. **Combinar** o canal de suporte e o horário de atendimento.

---

## 9. Principais riscos

| Risco | O que fazer |
|---|---|
| **Propriedade indefinida** (responsável pelo Projeto 1/restaurante) | Acordo escrito antes de vender (seção 2.1 e 7). |
| **Dependência do Telegram** ou cliente que só usa WhatsApp | Validar com o cliente **antes** de vender; WhatsApp está fora do escopo (seção 2.5). |
| **Notebook ou Wi-Fi do cliente caem** | Modelo B (servidor seu), monitoramento e plano B impresso. |
| **Suporte fora do horário comercial** | Definir SLA e preço; automatizar alertas. |
| **LGPD / fotos de pessoas** | Contrato, aviso à equipe, retenção curta, orientação de fotografar equipamentos. |
| **Concorrentes** (aplicativos prontos) | Pesquisar preço e recursos; vender o que eles não fazem: simplicidade no Telegram, PDF pronto, impressão. |
| **Você virar o único ponto de falha** | Documentar, ter outra pessoa treinada, automatizar instalação e monitoramento. |

---

## 10. Roteiro sugerido

1. **Agora:** acordo com o responsável pelo Projeto 1; autorização do Divino Fogão; **piloto de 2 a 4 semanas** no
   restaurante, medindo antes e depois (seção 6.3).
2. **Produto mínimo:** itens 1, 2, 4, 6, 8 e 9 da seção 4; modelo de contrato; política de privacidade.
3. **2 ou 3 clientes pagantes**, com instalação por cliente e suporte combinado.
4. **Decidir com dados:** painel web ou plataforma multi-cliente, conforme o que os
   clientes pedirem e pagarem.

---

## 11. Decisões que só você (e quem for sócio) podem tomar

- Você vai vender **sozinho ou com sócio**? Em que **proporção**?
- O **público** é restaurantes e lanchonetes pequenos, franquias ou outro segmento?
- O seu primeiro cliente-alvo aceita **Telegram**? (WhatsApp está fora do escopo.)
- Prefere **instalar no cliente** (modelo A) ou **hospedar** (modelo B)?
- Qual **nome** terá o produto e qual será a identidade visual?
- Quanto tempo por semana você consegue dedicar a **suporte** sem prejudicar o resto?

---

## 12. Como entregar o software: código, executável ou hospedado

Esta seção responde: "devo passar todo o código, ou entregar um executável em que a pessoa só
edita valores?". E, no caso do **Projeto 1** (Divino Fogão), **a pessoa responsável pelo
notebook não deve ver este guia** (nem o `CLAUDE.md`).

### 12.1 O que cada pessoa realmente precisa editar

No dia a dia, o responsável só precisa mexer em **valores**, nunca em código:

- `.env`: token, IDs liberados, grupo dos relatórios;
- os arquivos `.yaml` dos checklists e da loja.

Isso já é assim hoje. O que falta é **separar** onde esses arquivos ficam do código (veja 12.3)
e **controlar o que a pessoa recebe** (12.2).

### 12.2 Três jeitos de entregar

| Opção | O que a pessoa recebe | Prós | Contras |
|---|---|---|---|
| **1. Pacote ZIP com o código** | Uma pasta com os `.py`; ela só edita `.env` e `.yaml`. | **Funciona hoje**, sem trabalho extra. Fácil de atualizar. | O código Python é legível: quem quiser lê e copia. Não protege o seu trabalho por si só. |
| **2. Executável (`.exe`)** | Um programa que roda sem Python instalado; pasta de configuração ao lado. | Esconde o código-fonte de quem só quer usar (dificulta, **não impede**: dá para descompilar). Instalação mais simples. | Precisa ser gerado **num Windows** (não dá no Linux), ajustes nos caminhos de arquivos, dados embutidos (fusos, imagens, PDF) e **testes em Windows**. Executável sem assinatura pode ser **barrado pelo Windows (SmartScreen) ou pelo antivírus**; certificado de assinatura é pago. Atualizar exige gerar e substituir o `.exe`. Esforço médio. |
| **3. Hospedado por você** | Nada instalado: só usa o bot. | **Melhor proteção** do código; atualização e monitoramento centralizados. | Custo de servidor; você vira operador dos dados (LGPD, seção 3.3); precisa de um jeito de ele gerenciar usuários e checklists sem acessar arquivos (seção 4, itens 2 e 3). |

### 12.3 Recomendação

**Projeto 1 (agora): opção 1, com cuidados.**

1. **Não dê acesso ao repositório do GitHub** à pessoa. O histórico do repositório contém este
   guia (mesmo que o arquivo seja apagado depois, o histórico o guarda). Entregue **um ZIP**.
2. Gere o ZIP com o próprio Git, que **deixa de fora** este guia e o `CLAUDE.md` (isso está
   configurado em `.gitattributes`):

```bash
git archive --format=zip --prefix=bot-fechamento/ -o bot-fechamento-pacote.zip main
```

   Confira a lista de arquivos do ZIP antes de enviar (`docs/guia-venda.md` e `CLAUDE.md` não
   devem estar nela). O ZIP também **não inclui o histórico** do Git.
3. **Configuração fora da pasta do código:** o guia `guia-servidor-windows.md` já orienta a manter
   `C:\bot-config\lojas` separada. Assim, ele só edita valores, e **você pode trocar o código
   inteiro** (novo ZIP) sem perder as configurações dele.
4. **Entregue o código depois do acordo por escrito** (seções 2.1 e 7). Entregar antes enfraquece
   a sua posição.
5. Se ele precisar de acesso ao repositório por algum motivo, crie **outro repositório privado
   só para entrega** com o conteúdo do ZIP (histórico limpo), em vez de dar acesso a este.

**Se este guia já foi enviado a alguém por engano:** o repositório hoje é privado e só você tem
acesso. Se um dia for necessário remover o guia do histórico, isso exige reescrever o histórico
(operação destrutiva, que deve ser planejada e confirmada antes). Não é preciso agora.

**Clientes futuros:** prefira a opção **3** (hospedado) ou, no começo, a **1** com contrato que
proíba cópia e redistribuição. Só considere o **executável (2)** quando houver mais de um cliente
instalando por conta própria e valer o esforço de testes em Windows e assinatura.

### 12.4 Se quiser o executável

O que precisaria ser feito (não foi feito ainda): ajustar `bot.py` para achar `.env`, `lojas/`,
`arquivo/` e `logs/` ao lado do `.exe`; gerar com PyInstaller num Windows (de preferência por uma
rotina automática no GitHub, num runner Windows); testar o `.exe` no notebook (inclusive
reinício, fusos e PDF com logo); decidir sobre assinatura de código. É um projeto pequeno, mas
**só vale a pena depois de o bot ter rodado bem por algumas semanas** e de haver motivo comercial.

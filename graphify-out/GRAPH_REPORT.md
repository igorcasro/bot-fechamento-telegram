# Graph Report - bot-fechamento-telegram  (2026-11-09)

## Corpus Check
- 26 files · ~26,429 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 2, .bat 2, .example 1)

## Summary
- 478 nodes · 1309 edges · 29 communities (12 shown, 17 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 194 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `feec7911`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- bot.py
- pdf.py
- test_bot_fluxo.py
- entrega.py
- Status
- Sessao
- fixtures/lojas/divino-fogao/checklists/abertura.yaml
- fechamento.yaml
- arquivo.py
- Loja
- abertura.yaml
- fixtures/lojas/divino-fogao/checklists/fechamento.yaml
- BotFalso

## God Nodes (most connected - your core abstractions)
1. `Sessao` - 58 edges
2. `Checklist` - 57 edges
3. `Chat` - 39 edges
4. `novo_ctx()` - 34 edges
5. `Status` - 32 edges
6. `gerar_relatorio_pdf()` - 30 edges
7. `hora()` - 28 edges
8. `build_app()` - 25 edges
9. `gerar_lista_pdf()` - 25 edges
10. `Loja` - 24 edges

## Surprising Connections (you probably didn't know these)
- `cmd_imprimir()` --indirect_call--> `gerar_lista_pdf()`  [INFERRED]
  bot.py → nucleo/pdf.py
- `cmd_resultado()` --indirect_call--> `gerar_lista_pdf()`  [INFERRED]
  bot.py → nucleo/pdf.py
- `cl()` --uses--> `Checklist`  [INFERRED]
  tests/conftest.py → nucleo/checklist.py
- `test_comando_padrao_e_personalizado()` --uses--> `Checklist`  [INFERRED]
  tests/test_checklist.py → nucleo/checklist.py
- `test_para_data_filtra_etapas()` --uses--> `Checklist`  [INFERRED]
  tests/test_checklist.py → nucleo/checklist.py

## Import Cycles
- None detected.

## Communities (29 total, 17 thin omitted)

### Community 0 - "bot.py"
Cohesion: 0.06
Nodes (53): _args(), botao(), build_app(), caminho_env(), carregar_sessao(), cmd_cancelar(), cmd_dia(), cmd_dinamico() (+45 more)

### Community 1 - "pdf.py"
Cohesion: 0.07
Nodes (22): _barra_secao(), _cabecalho(), _Caixa, _carregar_foto(), _celula_etapa(), _distribuir(), _doc(), gerar_lista_pdf() (+14 more)

### Community 3 - "test_bot_fluxo.py"
Cohesion: 0.12
Nodes (38): CanalFalso, Chat, completar(), copia_loja(), novo_ctx(), novo_msg(), test_botoes_de_sessao_anterior_sao_rejeitados(), test_cancelar_descarta_checklist_e_fotos() (+30 more)

### Community 5 - "Status"
Cohesion: 0.13
Nodes (26): EstadoInvalido, Status, hora(), cenario(), test_fotos_ocupam_cerca_de_um_quarto_da_pagina(), test_lista_preenchida_destaca_etapas_nao_realizadas(), test_lista_vazia_e_preenchida(), test_relatorio_pdf() (+18 more)

### Community 6 - "Sessao"
Cohesion: 0.07
Nodes (18): Arquivo, destino_atomico(), Checklist, resumo_texto(), _iso(), Resposta, Sessao, test_roundtrip_dict() (+10 more)

### Community 7 - "fixtures/lojas/divino-fogao/checklists/abertura.yaml"
Cohesion: 0.20
Nodes (9): comando, foto, instrucao, titulo, nome, secoes, etapas, nome (+1 more)

### Community 8 - "fechamento.yaml"
Cohesion: 0.20
Nodes (9): comando, foto, fotos, titulo, nome, secoes, etapas, nome (+1 more)

### Community 9 - "arquivo.py"
Cohesion: 0.08
Nodes (3): configurar(), FotoReg, test_log_em_arquivo_e_token_nao_vaza()

### Community 12 - "Loja"
Cohesion: 0.08
Nodes (15): Etapa, _to_date(), Loja, cl(), loja(), test_comando_padrao_e_personalizado(), test_loja_tipo_por_comando_e_validar(), test_lojas_reais_carregam_sem_erro() (+7 more)

### Community 15 - "abertura.yaml"
Cohesion: 0.20
Nodes (9): comando, foto, instrucao, titulo, nome, secoes, etapas, nome (+1 more)

### Community 25 - "fixtures/lojas/divino-fogao/checklists/fechamento.yaml"
Cohesion: 0.22
Nodes (8): comando, foto, titulo, nome, secoes, etapas, nome, tipo

### Community 26 - "BotFalso"
Cohesion: 0.18
Nodes (3): TelegramEntrega, BotFalso, test_env_externo_recarrega_destino_privado()

## Knowledge Gaps
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Checklist` connect `Sessao` to `bot.py`, `pdf.py`, `Status`, `arquivo.py`, `Loja`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `Sessao` (e.g. with `Arquivo` and `_celula_etapa()`) actually correct?**
  _`Sessao` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Should `bot.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05970790378006873 - nodes in this community are weakly interconnected._
- **Why does `Sessao` connect `Sessao` to `bot.py`, `arquivo.py`, `Status`, `pdf.py`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `Checklist` (e.g. with `Arquivo` and `Loja`) actually correct?**
  _`Checklist` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Should `pdf.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07138535995160314 - nodes in this community are weakly interconnected._
- **Why does `Loja` connect `Loja` to `bot.py`, `pdf.py`, `test_bot_fluxo.py`, `Status`, `Sessao`, `arquivo.py`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
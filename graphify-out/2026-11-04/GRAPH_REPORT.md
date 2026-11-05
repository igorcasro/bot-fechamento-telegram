# Graph Report - bot-fechamento-telegram  (2026-11-04)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 403 nodes · 1139 edges · 13 communities (9 shown, 4 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 168 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `27a3023e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- bot.py
- pdf.py
- test_bot_fluxo.py
- Sessao
- Status
- logs.py
- fechamento.yaml
- checklist.py
- Loja
- abertura.yaml

## God Nodes (most connected - your core abstractions)
1. `Sessao` - 55 edges
2. `Checklist` - 48 edges
3. `Status` - 32 edges
4. `gerar_relatorio_pdf()` - 31 edges
5. `Chat` - 29 edges
6. `hora()` - 27 edges
7. `gerar_lista_pdf()` - 24 edges
8. `novo_ctx()` - 24 edges
9. `Loja` - 23 edges
10. `Arquivo` - 22 edges

## Surprising Connections (you probably didn't know these)
- `Contexto` --uses--> `Arquivo`  [INFERRED]
  bot.py → fechamento/arquivo.py
- `Contexto` --uses--> `CanalEntrega`  [INFERRED]
  bot.py → fechamento/entrega.py
- `Contexto` --uses--> `Loja`  [INFERRED]
  bot.py → fechamento/loja.py
- `foto()` --uses--> `Arquivo`  [INFERRED]
  bot.py → fechamento/arquivo.py
- `carregar_sessao()` --uses--> `Checklist`  [INFERRED]
  bot.py → fechamento/checklist.py

## Import Cycles
- None detected.

## Communities (13 total, 4 thin omitted)

### Community 0 - "bot.py"
Cohesion: 0.08
Nodes (43): _args(), botao(), build_app(), carregar_sessao(), cmd_cancelar(), cmd_dia(), cmd_dinamico(), cmd_finalizar() (+35 more)

### Community 1 - "pdf.py"
Cohesion: 0.07
Nodes (23): _barra_secao(), _cabecalho(), _Caixa, _carregar_foto(), _celula_etapa(), _distribuir(), _doc(), gerar_lista_pdf() (+15 more)

### Community 3 - "test_bot_fluxo.py"
Cohesion: 0.11
Nodes (28): BotFalso, CanalFalso, Chat, completar(), copia_loja(), novo_ctx(), novo_msg(), test_cancelar_descarta_checklist_e_fotos() (+20 more)

### Community 4 - "Sessao"
Cohesion: 0.07
Nodes (14): Arquivo, Checklist, EstadoInvalido, FotoReg, _iso(), Resposta, Sessao, test_roundtrip_dict() (+6 more)

### Community 5 - "Status"
Cohesion: 0.14
Nodes (26): Status, hora(), cenario(), test_fotos_ocupam_cerca_de_um_quarto_da_pagina(), test_lista_preenchida_destaca_etapas_nao_realizadas(), test_lista_vazia_e_preenchida(), test_relatorio_pdf(), test_varias_fotos_na_mesma_etapa_encolhem_para_caber_na_pagina() (+18 more)

### Community 7 - "logs.py"
Cohesion: 0.14
Nodes (5): main(), parse_ids(), configurar(), test_main_mensagens_claras_para_token_invalido_e_sem_rede(), test_log_em_arquivo_e_token_nao_vaza()

### Community 8 - "fechamento.yaml"
Cohesion: 0.22
Nodes (8): comando, foto, titulo, nome, secoes, etapas, nome, tipo

### Community 12 - "Loja"
Cohesion: 0.07
Nodes (14): Etapa, _to_date(), Loja, cl(), loja(), test_comando_padrao_e_personalizado(), test_loja_tipo_por_comando_e_validar(), test_para_data_filtra_etapas() (+6 more)

### Community 15 - "abertura.yaml"
Cohesion: 0.20
Nodes (9): comando, foto, instrucao, titulo, nome, secoes, etapas, nome (+1 more)

## Knowledge Gaps
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Checklist` connect `Sessao` to `bot.py`, `pdf.py`, `Status`, `checklist.py`, `Loja`?**
  _High betweenness centrality (0.127) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `Sessao` (e.g. with `carregar_sessao()` and `finalizar()`) actually correct?**
  _`Sessao` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Should `bot.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07525807525807526 - nodes in this community are weakly interconnected._
- **Why does `Sessao` connect `Sessao` to `bot.py`, `checklist.py`, `Status`, `pdf.py`?**
  _High betweenness centrality (0.109) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `Checklist` (e.g. with `carregar_sessao()` and `finalizar()`) actually correct?**
  _`Checklist` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Should `pdf.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06746031746031746 - nodes in this community are weakly interconnected._
- **Why does `Loja` connect `Loja` to `bot.py`, `pdf.py`, `test_bot_fluxo.py`, `Sessao`, `Status`, `checklist.py`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
# Graph Report - bot-fechamento-telegram  (2026-11-04)

## Corpus Check
- 23 files · ~20,901 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 2, .bat 2, .example 1)

## Summary
- 415 nodes · 1151 edges · 25 communities (10 shown, 15 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 194 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `67f05658`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- bot.py
- pdf.py
- test_bot_fluxo.py
- Arquivo
- Status
- Sessao
- logs.py
- fechamento.yaml
- sessao.py
- Loja
- abertura.yaml

## God Nodes (most connected - your core abstractions)
1. `Sessao` - 57 edges
2. `Checklist` - 53 edges
3. `Status` - 36 edges
4. `gerar_relatorio_pdf()` - 31 edges
5. `Chat` - 29 edges
6. `hora()` - 27 edges
7. `gerar_lista_pdf()` - 25 edges
8. `Loja` - 24 edges
9. `novo_ctx()` - 24 edges
10. `Arquivo` - 22 edges

## Surprising Connections (you probably didn't know these)
- `Contexto` --uses--> `Arquivo`  [INFERRED]
  bot.py → nucleo/arquivo.py
- `Contexto` --uses--> `CanalEntrega`  [INFERRED]
  bot.py → nucleo/entrega.py
- `Contexto` --uses--> `Loja`  [INFERRED]
  bot.py → nucleo/loja.py
- `salvar()` --uses--> `Checklist`  [INFERRED]
  bot.py → nucleo/checklist.py
- `salvar()` --uses--> `Sessao`  [INFERRED]
  bot.py → nucleo/sessao.py

## Import Cycles
- None detected.

## Communities (25 total, 15 thin omitted)

### Community 0 - "bot.py"
Cohesion: 0.08
Nodes (44): _args(), botao(), build_app(), carregar_sessao(), cmd_cancelar(), cmd_dia(), cmd_dinamico(), cmd_finalizar() (+36 more)

### Community 1 - "pdf.py"
Cohesion: 0.07
Nodes (24): _barra_secao(), _cabecalho(), _Caixa, _carregar_foto(), _celula_etapa(), _distribuir(), _doc(), gerar_lista_pdf() (+16 more)

### Community 3 - "test_bot_fluxo.py"
Cohesion: 0.11
Nodes (28): BotFalso, CanalFalso, Chat, completar(), copia_loja(), novo_ctx(), novo_msg(), test_cancelar_descarta_checklist_e_fotos() (+20 more)

### Community 4 - "Arquivo"
Cohesion: 0.12
Nodes (4): Arquivo, test_roundtrip_dict(), test_reduzir_foto(), test_retencao_remove_so_dias_antigos()

### Community 5 - "Status"
Cohesion: 0.14
Nodes (26): EstadoInvalido, Status, hora(), test_varias_fotos_na_mesma_etapa_encolhem_para_caber_na_pagina(), sessao_pronta(), test_progresso_texto(), test_resultados_ida_e_volta(), test_resumo_sem_pendencias() (+18 more)

### Community 6 - "Sessao"
Cohesion: 0.13
Nodes (7): Checklist, dia_semana(), progresso_texto(), resumo_texto(), _iso(), Resposta, Sessao

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
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Checklist` connect `Sessao` to `bot.py`, `pdf.py`, `Arquivo`, `Status`, `sessao.py`, `Loja`?**
  _High betweenness centrality (0.129) - this node is a cross-community bridge._
- **Are the 22 inferred relationships involving `Sessao` (e.g. with `carregar_sessao()` and `finalizar()`) actually correct?**
  _`Sessao` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Should `bot.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07530022719896137 - nodes in this community are weakly interconnected._
- **Why does `Sessao` connect `Sessao` to `bot.py`, `pdf.py`, `Arquivo`, `Status`, `sessao.py`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Are the 21 inferred relationships involving `Checklist` (e.g. with `carregar_sessao()` and `finalizar()`) actually correct?**
  _`Checklist` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Should `pdf.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06779661016949153 - nodes in this community are weakly interconnected._
- **Why does `Loja` connect `Loja` to `bot.py`, `pdf.py`, `test_bot_fluxo.py`, `Status`, `Sessao`, `sessao.py`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
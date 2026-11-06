# Graph Report - bot-fechamento-telegram  (2026-11-05)

## Corpus Check
- 26 files · ~26,074 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 2, .bat 2, .example 1)

## Summary
- 474 nodes · 1288 edges · 29 communities (12 shown, 17 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 192 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9162ca5a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- bot.py
- pdf.py
- test_bot_fluxo.py
- Arquivo
- Status
- sessao.py
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
3. `Chat` - 37 edges
4. `novo_ctx()` - 33 edges
5. `Status` - 32 edges
6. `gerar_relatorio_pdf()` - 30 edges
7. `hora()` - 28 edges
8. `gerar_lista_pdf()` - 25 edges
9. `build_app()` - 24 edges
10. `Loja` - 24 edges

## Surprising Connections (you probably didn't know these)
- `Contexto` --uses--> `CanalEntrega`  [INFERRED]
  bot.py → nucleo/entrega.py
- `cmd_imprimir()` --indirect_call--> `gerar_lista_pdf()`  [INFERRED]
  bot.py → nucleo/pdf.py
- `cmd_resultado()` --indirect_call--> `gerar_lista_pdf()`  [INFERRED]
  bot.py → nucleo/pdf.py
- `loja()` --uses--> `Loja`  [INFERRED]
  tests/conftest.py → nucleo/loja.py
- `test_loja_tipo_por_comando_e_validar()` --uses--> `Loja`  [INFERRED]
  tests/test_checklist.py → nucleo/loja.py

## Import Cycles
- None detected.

## Communities (29 total, 17 thin omitted)

### Community 0 - "bot.py"
Cohesion: 0.06
Nodes (52): _args(), botao(), build_app(), carregar_sessao(), cmd_cancelar(), cmd_dia(), cmd_dinamico(), cmd_finalizar() (+44 more)

### Community 1 - "pdf.py"
Cohesion: 0.06
Nodes (23): Loja, _barra_secao(), _cabecalho(), _Caixa, _carregar_foto(), _celula_etapa(), _distribuir(), _doc() (+15 more)

### Community 3 - "test_bot_fluxo.py"
Cohesion: 0.12
Nodes (37): CanalFalso, Chat, completar(), copia_loja(), novo_ctx(), novo_msg(), test_botoes_de_sessao_anterior_sao_rejeitados(), test_cancelar_descarta_checklist_e_fotos() (+29 more)

### Community 4 - "Arquivo"
Cohesion: 0.12
Nodes (10): Arquivo, destino_atomico(), sessao_pronta(), test_gravacao_interrompida_preserva_resultado_anterior(), test_progresso_texto(), test_reduzir_foto(), test_resultados_ida_e_volta(), test_resultados_ignora_arquivo_corrompido_e_le_pasta_antiga() (+2 more)

### Community 5 - "Status"
Cohesion: 0.12
Nodes (27): EstadoInvalido, Status, hora(), cenario(), test_lista_preenchida_destaca_etapas_nao_realizadas(), test_lista_vazia_e_preenchida(), test_relatorio_pdf(), test_varias_fotos_na_mesma_etapa_encolhem_para_caber_na_pagina() (+19 more)

### Community 6 - "sessao.py"
Cohesion: 0.10
Nodes (6): progresso_texto(), resumo_texto(), FotoReg, _iso(), Resposta, Sessao

### Community 7 - "fixtures/lojas/divino-fogao/checklists/abertura.yaml"
Cohesion: 0.20
Nodes (9): comando, foto, instrucao, titulo, nome, secoes, etapas, nome (+1 more)

### Community 8 - "fechamento.yaml"
Cohesion: 0.20
Nodes (9): comando, foto, fotos, titulo, nome, secoes, etapas, nome (+1 more)

### Community 9 - "arquivo.py"
Cohesion: 0.08
Nodes (3): CanalEntrega, configurar(), test_log_em_arquivo_e_token_nao_vaza()

### Community 12 - "Loja"
Cohesion: 0.08
Nodes (16): Checklist, Etapa, _to_date(), cl(), loja(), test_comando_padrao_e_personalizado(), test_loja_tipo_por_comando_e_validar(), test_lojas_reais_carregam_sem_erro() (+8 more)

### Community 15 - "abertura.yaml"
Cohesion: 0.20
Nodes (9): comando, foto, instrucao, titulo, nome, secoes, etapas, nome (+1 more)

### Community 25 - "fixtures/lojas/divino-fogao/checklists/fechamento.yaml"
Cohesion: 0.22
Nodes (8): comando, foto, titulo, nome, secoes, etapas, nome, tipo

## Knowledge Gaps
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Checklist` connect `Loja` to `bot.py`, `pdf.py`, `Arquivo`, `Status`, `sessao.py`, `arquivo.py`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `Sessao` (e.g. with `Arquivo` and `_celula_etapa()`) actually correct?**
  _`Sessao` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Should `bot.py` be split into smaller, more focused modules?**
  _Cohesion score 0.056070913213770356 - nodes in this community are weakly interconnected._
- **Why does `Sessao` connect `sessao.py` to `bot.py`, `pdf.py`, `Arquivo`, `Status`, `arquivo.py`, `Loja`?**
  _High betweenness centrality (0.098) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `Checklist` (e.g. with `Arquivo` and `Loja`) actually correct?**
  _`Checklist` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Should `pdf.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06349206349206349 - nodes in this community are weakly interconnected._
- **Why does `Loja` connect `pdf.py` to `bot.py`, `test_bot_fluxo.py`, `Status`, `sessao.py`, `arquivo.py`, `Loja`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
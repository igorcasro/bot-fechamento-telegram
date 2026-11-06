# Graph Report - bot-fechamento-telegram  (2026-11-05)

## Corpus Check
- 26 files · ~25,399 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 2, .bat 2, .example 1)

## Summary
- 462 nodes · 1241 edges · 29 communities (12 shown, 17 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 190 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b0984da5`
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
- logs.py
- Loja
- abertura.yaml
- fixtures/lojas/divino-fogao/checklists/fechamento.yaml
- entrega.py

## God Nodes (most connected - your core abstractions)
1. `Sessao` - 60 edges
2. `Checklist` - 55 edges
3. `Status` - 36 edges
4. `Chat` - 33 edges
5. `gerar_relatorio_pdf()` - 30 edges
6. `novo_ctx()` - 28 edges
7. `hora()` - 27 edges
8. `gerar_lista_pdf()` - 25 edges
9. `Loja` - 24 edges
10. `Arquivo` - 22 edges

## Surprising Connections (you probably didn't know these)
- `cmd_imprimir()` --indirect_call--> `gerar_lista_pdf()`  [INFERRED]
  bot.py → nucleo/pdf.py
- `cmd_resultado()` --indirect_call--> `gerar_lista_pdf()`  [INFERRED]
  bot.py → nucleo/pdf.py
- `cenario()` --uses--> `Sessao`  [INFERRED]
  tests/test_pdf.py → nucleo/sessao.py
- `test_varias_fotos_na_mesma_etapa_encolhem_para_caber_na_pagina()` --uses--> `Sessao`  [INFERRED]
  tests/test_pdf.py → nucleo/sessao.py
- `sessao_pronta()` --uses--> `Sessao`  [INFERRED]
  tests/test_relatorio_arquivo.py → nucleo/sessao.py

## Import Cycles
- None detected.

## Communities (29 total, 17 thin omitted)

### Community 0 - "bot.py"
Cohesion: 0.07
Nodes (47): _args(), botao(), build_app(), carregar_sessao(), cmd_cancelar(), cmd_dia(), cmd_dinamico(), cmd_finalizar() (+39 more)

### Community 1 - "pdf.py"
Cohesion: 0.07
Nodes (24): _barra_secao(), _cabecalho(), _Caixa, _carregar_foto(), _celula_etapa(), _distribuir(), _doc(), gerar_lista_pdf() (+16 more)

### Community 3 - "test_bot_fluxo.py"
Cohesion: 0.11
Nodes (32): BotFalso, CanalFalso, Chat, completar(), copia_loja(), novo_ctx(), novo_msg(), test_botoes_de_sessao_anterior_sao_rejeitados() (+24 more)

### Community 4 - "Arquivo"
Cohesion: 0.09
Nodes (10): Arquivo, destino_atomico(), sessao_pronta(), test_gravacao_interrompida_preserva_resultado_anterior(), test_progresso_texto(), test_reduzir_foto(), test_resultados_ida_e_volta(), test_resultados_ignora_arquivo_corrompido_e_le_pasta_antiga() (+2 more)

### Community 5 - "Status"
Cohesion: 0.15
Nodes (22): EstadoInvalido, FotoReg, Status, hora(), test_varias_fotos_na_mesma_etapa_encolhem_para_caber_na_pagina(), nova(), test_album_nao_vaza_para_proxima_etapa(), test_concluido_com_foto_obrigatoria_avanca() (+14 more)

### Community 6 - "sessao.py"
Cohesion: 0.12
Nodes (9): Checklist, data_br(), dia_semana(), progresso_texto(), resumo_texto(), _iso(), Resposta, Sessao (+1 more)

### Community 7 - "fixtures/lojas/divino-fogao/checklists/abertura.yaml"
Cohesion: 0.20
Nodes (9): comando, foto, instrucao, titulo, nome, secoes, etapas, nome (+1 more)

### Community 8 - "fechamento.yaml"
Cohesion: 0.20
Nodes (9): comando, foto, fotos, titulo, nome, secoes, etapas, nome (+1 more)

### Community 9 - "logs.py"
Cohesion: 0.14
Nodes (5): main(), parse_ids(), configurar(), test_main_mensagens_claras_para_token_invalido_e_sem_rede(), test_log_em_arquivo_e_token_nao_vaza()

### Community 12 - "Loja"
Cohesion: 0.06
Nodes (16): Etapa, _to_date(), Loja, cl(), loja(), test_comando_padrao_e_personalizado(), test_loja_tipo_por_comando_e_validar(), test_lojas_reais_carregam_sem_erro() (+8 more)

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

- **Why does `Checklist` connect `sessao.py` to `bot.py`, `pdf.py`, `Arquivo`, `Status`, `Loja`?**
  _High betweenness centrality (0.117) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `Sessao` (e.g. with `Arquivo` and `_celula_etapa()`) actually correct?**
  _`Sessao` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Should `bot.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06757865937072503 - nodes in this community are weakly interconnected._
- **Why does `Sessao` connect `sessao.py` to `bot.py`, `pdf.py`, `Arquivo`, `Status`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `Checklist` (e.g. with `Arquivo` and `Loja`) actually correct?**
  _`Checklist` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Should `pdf.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07017543859649122 - nodes in this community are weakly interconnected._
- **Why does `Loja` connect `Loja` to `bot.py`, `pdf.py`, `test_bot_fluxo.py`, `sessao.py`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
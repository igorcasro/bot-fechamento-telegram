# Graph Report - bot-fechamento-telegram  (2026-11-04)

## Corpus Check
- 22 files · ~23,703 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 2, .bat 2, .example 1)

## Summary
- 384 nodes · 1121 edges · 12 communities (8 shown, 4 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 175 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6378a8ab`
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
- entrega.py
- test_checklist.py

## God Nodes (most connected - your core abstractions)
1. `Sessao` - 55 edges
2. `Checklist` - 53 edges
3. `Status` - 32 edges
4. `gerar_relatorio_pdf()` - 30 edges
5. `Chat` - 29 edges
6. `hora()` - 26 edges
7. `gerar_lista_pdf()` - 24 edges
8. `Loja` - 24 edges
9. `novo_ctx()` - 24 edges
10. `Arquivo` - 22 edges

## Surprising Connections (you probably didn't know these)
- `cmd_reenviar()` --indirect_call--> `gerar_relatorio_pdf()`  [INFERRED]
  bot.py → fechamento/pdf.py
- `finalizar()` --indirect_call--> `gerar_relatorio_pdf()`  [INFERRED]
  bot.py → fechamento/pdf.py
- `cmd_imprimir()` --indirect_call--> `gerar_lista_pdf()`  [INFERRED]
  bot.py → fechamento/pdf.py
- `cmd_resultado()` --indirect_call--> `gerar_lista_pdf()`  [INFERRED]
  bot.py → fechamento/pdf.py
- `Contexto` --uses--> `Arquivo`  [INFERRED]
  bot.py → fechamento/arquivo.py

## Import Cycles
- None detected.

## Communities (12 total, 4 thin omitted)

### Community 0 - "bot.py"
Cohesion: 0.08
Nodes (43): _args(), botao(), build_app(), carregar_sessao(), cmd_cancelar(), cmd_dia(), cmd_dinamico(), cmd_finalizar() (+35 more)

### Community 1 - "pdf.py"
Cohesion: 0.08
Nodes (23): _barra_secao(), _cabecalho(), _Caixa, _celula_etapa(), _doc(), gerar_lista_pdf(), gerar_relatorio_pdf(), _grade_info() (+15 more)

### Community 3 - "test_bot_fluxo.py"
Cohesion: 0.11
Nodes (28): BotFalso, CanalFalso, Chat, completar(), copia_loja(), novo_ctx(), novo_msg(), test_cancelar_descarta_checklist_e_fotos() (+20 more)

### Community 4 - "Sessao"
Cohesion: 0.07
Nodes (16): Arquivo, Checklist, progresso_texto(), resumo_texto(), FotoReg, _iso(), Resposta, Sessao (+8 more)

### Community 5 - "Status"
Cohesion: 0.23
Nodes (20): EstadoInvalido, Status, hora(), nova(), test_album_nao_vaza_para_proxima_etapa(), test_concluido_com_foto_obrigatoria_avanca(), test_etapa_com_duas_fotos(), test_finalizar_descarta_concluido_sem_fotos_obrigatorias() (+12 more)

### Community 7 - "logs.py"
Cohesion: 0.14
Nodes (5): main(), parse_ids(), configurar(), test_main_mensagens_claras_para_token_invalido_e_sem_rede(), test_log_em_arquivo_e_token_nao_vaza()

### Community 8 - "fechamento.yaml"
Cohesion: 0.22
Nodes (8): comando, foto, titulo, nome, secoes, etapas, nome, tipo

### Community 12 - "test_checklist.py"
Cohesion: 0.06
Nodes (14): Etapa, _to_date(), Loja, cl(), loja(), test_comando_padrao_e_personalizado(), test_loja_tipo_por_comando_e_validar(), test_para_data_filtra_etapas() (+6 more)

## Knowledge Gaps
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Checklist` connect `Sessao` to `bot.py`, `pdf.py`, `test_checklist.py`?**
  _High betweenness centrality (0.146) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `Sessao` (e.g. with `carregar_sessao()` and `finalizar()`) actually correct?**
  _`Sessao` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Should `bot.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07525807525807526 - nodes in this community are weakly interconnected._
- **Why does `Sessao` connect `Sessao` to `bot.py`, `pdf.py`, `test_checklist.py`, `Status`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **Are the 17 inferred relationships involving `Checklist` (e.g. with `carregar_sessao()` and `finalizar()`) actually correct?**
  _`Checklist` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Should `pdf.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07518796992481203 - nodes in this community are weakly interconnected._
- **Why does `Loja` connect `test_checklist.py` to `bot.py`, `pdf.py`, `test_bot_fluxo.py`, `Sessao`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
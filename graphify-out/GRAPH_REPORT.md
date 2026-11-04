# Graph Report - bot-fechamento-telegram  (2026-11-04)

## Corpus Check
- 22 files · ~22,039 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 2, .bat 2, .example 1)

## Summary
- 365 nodes · 1064 edges · 13 communities (10 shown, 3 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 180 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `28b4153b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- bot.py
- pdf.py
- Loja
- test_bot_fluxo.py
- Sessao
- Status
- Arquivo
- logs.py
- fechamento.yaml
- entrega.py
- test_checklist.py

## God Nodes (most connected - your core abstractions)
1. `Sessao` - 55 edges
2. `Checklist` - 53 edges
3. `Status` - 32 edges
4. `gerar_relatorio_pdf()` - 30 edges
5. `Chat` - 27 edges
6. `Loja` - 24 edges
7. `gerar_lista_pdf()` - 23 edges
8. `hora()` - 23 edges
9. `Arquivo` - 22 edges
10. `build_app()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `Contexto` --uses--> `Arquivo`  [INFERRED]
  bot.py → fechamento/arquivo.py
- `Contexto` --uses--> `CanalEntrega`  [INFERRED]
  bot.py → fechamento/entrega.py
- `Contexto` --uses--> `Loja`  [INFERRED]
  bot.py → fechamento/loja.py
- `salvar()` --uses--> `Checklist`  [INFERRED]
  bot.py → fechamento/checklist.py
- `salvar()` --uses--> `Sessao`  [INFERRED]
  bot.py → fechamento/sessao.py

## Import Cycles
- None detected.

## Communities (13 total, 3 thin omitted)

### Community 0 - "bot.py"
Cohesion: 0.09
Nodes (40): _args(), botao(), build_app(), carregar_sessao(), cmd_cancelar(), cmd_dia(), cmd_dinamico(), cmd_finalizar() (+32 more)

### Community 1 - "pdf.py"
Cohesion: 0.08
Nodes (20): _barra_secao(), _cabecalho(), _Caixa, _celula_etapa(), _doc(), gerar_lista_pdf(), gerar_relatorio_pdf(), _grade_info() (+12 more)

### Community 2 - "Loja"
Cohesion: 0.09
Nodes (7): Loja, cl(), loja(), test_loja_tipo_por_comando_e_validar(), sessao_pronta(), test_progresso_texto(), test_resumo_texto()

### Community 3 - "test_bot_fluxo.py"
Cohesion: 0.12
Nodes (24): BotFalso, CanalFalso, Chat, completar(), copia_loja(), novo_ctx(), novo_msg(), test_cancelar_descarta_checklist_e_fotos() (+16 more)

### Community 4 - "Sessao"
Cohesion: 0.10
Nodes (9): Checklist, dia_semana(), progresso_texto(), resumo_texto(), EstadoInvalido, _iso(), Resposta, Sessao (+1 more)

### Community 5 - "Status"
Cohesion: 0.20
Nodes (18): FotoReg, Status, hora(), test_resumo_sem_pendencias(), nova(), test_album_nao_vaza_para_proxima_etapa(), test_concluido_com_foto_obrigatoria_avanca(), test_etapa_com_duas_fotos() (+10 more)

### Community 6 - "Arquivo"
Cohesion: 0.15
Nodes (4): Arquivo, test_reduzir_foto(), test_resultados_ida_e_volta(), test_retencao_remove_so_dias_antigos()

### Community 7 - "logs.py"
Cohesion: 0.14
Nodes (5): main(), parse_ids(), configurar(), test_main_mensagens_claras_para_token_invalido_e_sem_rede(), test_log_em_arquivo_e_token_nao_vaza()

### Community 8 - "fechamento.yaml"
Cohesion: 0.22
Nodes (8): comando, foto, titulo, nome, secoes, etapas, nome, tipo

### Community 12 - "test_checklist.py"
Cohesion: 0.12
Nodes (10): Etapa, _to_date(), test_comando_padrao_e_personalizado(), test_para_data_filtra_etapas(), test_secoes_indices_globais(), test_tipo_deve_ser_igual_ao_arquivo_e_comando_valido(), test_vale_em_dias_da_semana(), test_vale_em_sem_regras_vale_todo_dia() (+2 more)

## Knowledge Gaps
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Checklist` connect `Sessao` to `bot.py`, `pdf.py`, `Loja`, `Arquivo`, `test_checklist.py`?**
  _High betweenness centrality (0.156) - this node is a cross-community bridge._
- **Are the 20 inferred relationships involving `Sessao` (e.g. with `carregar_sessao()` and `finalizar()`) actually correct?**
  _`Sessao` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Should `bot.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0907928388746803 - nodes in this community are weakly interconnected._
- **Why does `Sessao` connect `Sessao` to `bot.py`, `pdf.py`, `Loja`, `Status`, `Arquivo`?**
  _High betweenness centrality (0.122) - this node is a cross-community bridge._
- **Are the 21 inferred relationships involving `Checklist` (e.g. with `carregar_sessao()` and `finalizar()`) actually correct?**
  _`Checklist` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Should `pdf.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08235294117647059 - nodes in this community are weakly interconnected._
- **Why does `Loja` connect `Loja` to `bot.py`, `pdf.py`, `test_bot_fluxo.py`, `Sessao`, `test_checklist.py`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
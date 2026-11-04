# Graph Report - bot-fechamento-telegram  (2026-11-04)

## Corpus Check
- 23 files · ~24,284 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 2, .bat 2, .example 1)

## Summary
- 395 nodes · 1125 edges · 17 communities (12 shown, 5 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 168 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b3383e16`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- bot.py
- pdf.py
- test_bot_fluxo.py
- Sessao
- Status
- Arquivo
- logs.py
- fechamento.yaml
- entrega.py
- test_checklist.py
- resumo_texto
- gerar_lista_pdf
- abertura.yaml

## God Nodes (most connected - your core abstractions)
1. `Sessao` - 55 edges
2. `Checklist` - 48 edges
3. `Status` - 32 edges
4. `gerar_relatorio_pdf()` - 30 edges
5. `Chat` - 29 edges
6. `hora()` - 26 edges
7. `novo_ctx()` - 24 edges
8. `gerar_lista_pdf()` - 24 edges
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

## Communities (17 total, 5 thin omitted)

### Community 0 - "bot.py"
Cohesion: 0.08
Nodes (43): _args(), botao(), build_app(), carregar_sessao(), cmd_cancelar(), cmd_dia(), cmd_dinamico(), cmd_finalizar() (+35 more)

### Community 1 - "pdf.py"
Cohesion: 0.12
Nodes (12): _barra_secao(), _cabecalho(), _celula_etapa(), gerar_relatorio_pdf(), _grade_info(), _linhas_etapas(), _linhas_fotos(), _logo() (+4 more)

### Community 3 - "test_bot_fluxo.py"
Cohesion: 0.11
Nodes (28): BotFalso, CanalFalso, Chat, completar(), copia_loja(), novo_ctx(), novo_msg(), test_cancelar_descarta_checklist_e_fotos() (+20 more)

### Community 4 - "Sessao"
Cohesion: 0.15
Nodes (6): Checklist, EstadoInvalido, _iso(), Resposta, Sessao, test_resumo_sem_pendencias()

### Community 5 - "Status"
Cohesion: 0.16
Nodes (24): FotoReg, Status, hora(), cenario(), test_lista_preenchida_destaca_etapas_nao_realizadas(), test_lista_vazia_e_preenchida(), test_relatorio_pdf(), nova() (+16 more)

### Community 6 - "Arquivo"
Cohesion: 0.12
Nodes (5): Arquivo, test_roundtrip_dict(), test_reduzir_foto(), test_resultados_ida_e_volta(), test_retencao_remove_so_dias_antigos()

### Community 7 - "logs.py"
Cohesion: 0.14
Nodes (5): main(), parse_ids(), configurar(), test_main_mensagens_claras_para_token_invalido_e_sem_rede(), test_log_em_arquivo_e_token_nao_vaza()

### Community 8 - "fechamento.yaml"
Cohesion: 0.22
Nodes (8): comando, foto, titulo, nome, secoes, etapas, nome, tipo

### Community 12 - "test_checklist.py"
Cohesion: 0.06
Nodes (14): Etapa, _to_date(), Loja, cl(), loja(), test_comando_padrao_e_personalizado(), test_loja_tipo_por_comando_e_validar(), test_para_data_filtra_etapas() (+6 more)

### Community 13 - "resumo_texto"
Cohesion: 0.22
Nodes (8): data_br(), dia_semana(), hora(), progresso_texto(), resumo_texto(), sessao_pronta(), test_progresso_texto(), test_resumo_texto()

### Community 14 - "gerar_lista_pdf"
Cohesion: 0.15
Nodes (4): _Caixa, _doc(), gerar_lista_pdf(), _Rodape

### Community 15 - "abertura.yaml"
Cohesion: 0.20
Nodes (9): comando, foto, instrucao, titulo, nome, secoes, etapas, nome (+1 more)

## Knowledge Gaps
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Checklist` connect `Sessao` to `bot.py`, `pdf.py`, `Arquivo`, `test_checklist.py`, `resumo_texto`, `gerar_lista_pdf`?**
  _High betweenness centrality (0.129) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `Sessao` (e.g. with `carregar_sessao()` and `finalizar()`) actually correct?**
  _`Sessao` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Should `bot.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07525807525807526 - nodes in this community are weakly interconnected._
- **Why does `Sessao` connect `Sessao` to `bot.py`, `pdf.py`, `Status`, `Arquivo`, `test_checklist.py`, `resumo_texto`, `gerar_lista_pdf`, `.etapa_destino`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `Checklist` (e.g. with `carregar_sessao()` and `finalizar()`) actually correct?**
  _`Checklist` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Should `pdf.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11931818181818182 - nodes in this community are weakly interconnected._
- **Why does `Loja` connect `test_checklist.py` to `bot.py`, `pdf.py`, `test_bot_fluxo.py`, `Sessao`, `resumo_texto`, `gerar_lista_pdf`?**
  _High betweenness centrality (0.078) - this node is a cross-community bridge._
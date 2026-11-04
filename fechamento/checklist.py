"""Modelo do checklist (seções, etapas e regras por dia). Sem dependência do Telegram.

Formato do YAML (veja lojas/divino-fogao/checklists/fechamento.yaml):

    tipo: fechamento                # opcional; se existir, deve ser igual ao nome do arquivo
    comando: fechar                 # opcional: comando do Telegram que inicia (/fechar)
    nome: "Fechamento da Loja"
    secoes:
      - nome: COZINHA
        etapas:
          - titulo: "Fogão desligado"
            instrucao: "..."            # opcional
            foto: obrigatoria           # obrigatoria | opcional | nenhuma
            fotos: 1                    # quantas fotos (padrão 1)
            nao_se_aplica: true         # permite o botão "Não se aplica" (padrão true)
            dias: [seg, qua]            # opcional: só nesses dias da semana
            datas: [2026-12-24]         # opcional: nessas datas específicas
            exceto: [2026-12-25]        # opcional: NÃO aparece nessas datas

Regra de "vale_em(data)": exceto > datas > dias. Sem `dias` nem `datas`, vale todo dia.
Com `datas` e sem `dias`, a etapa vale SOMENTE nessas datas.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

DIAS_SEMANA = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]  # date.weekday()
DIAS_SEMANA_LONGO = [
    "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
    "sexta-feira", "sábado", "domingo",
]
# comando padrão de cada tipo; os demais usam o próprio nome do tipo (ex.: limpeza -> /limpeza)
COMANDOS_PADRAO = {"fechamento": "fechar", "abertura": "abrir"}
FOTO_OBRIGATORIA, FOTO_OPCIONAL, FOTO_NENHUMA = "obrigatoria", "opcional", "nenhuma"
_FOTO_VALIDAS = {FOTO_OBRIGATORIA, FOTO_OPCIONAL, FOTO_NENHUMA}


def _to_date(v) -> date:
    if isinstance(v, date):
        return v
    return date.fromisoformat(str(v))


@dataclass
class Etapa:
    titulo: str
    instrucao: str = ""
    secao: str = ""
    foto: str = FOTO_OBRIGATORIA
    fotos: int = 1
    nao_se_aplica: bool = True
    dias: list[int] | None = None  # índices de date.weekday(); None = todos
    datas: list[date] = field(default_factory=list)
    exceto: list[date] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.foto not in _FOTO_VALIDAS:
            raise ValueError(
                f"Etapa '{self.titulo}': foto deve ser um de {sorted(_FOTO_VALIDAS)}, "
                f"recebi '{self.foto}'."
            )
        if self.fotos < 1:
            raise ValueError(f"Etapa '{self.titulo}': 'fotos' deve ser >= 1.")

    def vale_em(self, d: date) -> bool:
        if d in self.exceto:
            return False
        if d in self.datas:
            return True
        if self.dias is not None:
            return d.weekday() in self.dias
        return not self.datas

    def to_dict(self) -> dict:
        return {
            "titulo": self.titulo, "instrucao": self.instrucao, "secao": self.secao,
            "foto": self.foto, "fotos": self.fotos, "nao_se_aplica": self.nao_se_aplica,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Etapa":
        return cls(**d)


@dataclass
class Checklist:
    tipo: str
    nome: str
    etapas: list[Etapa]
    data: date | None = None  # preenchido por para_data()
    comando: str = ""  # comando do Telegram que inicia este checklist (sem a barra)

    @classmethod
    def carregar(cls, path: str | Path) -> "Checklist":
        path = Path(path)
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        tipo = path.stem  # o tipo é o nome do arquivo (fechamento.yaml -> "fechamento")
        if raw.get("tipo", tipo) != tipo:
            raise ValueError(
                f"{path.name}: 'tipo' ({raw['tipo']}) deve ser igual ao nome do arquivo ({tipo})."
            )
        comando = str(raw.get("comando") or COMANDOS_PADRAO.get(tipo, tipo)).lstrip("/").lower()
        if not re.fullmatch(r"[a-z0-9_]{1,32}", comando):
            raise ValueError(
                f"{path.name}: defina 'comando:' só com letras minúsculas, números e _ "
                f"(recebi '{comando}')."
            )
        etapas: list[Etapa] = []
        for sec in raw.get("secoes", []):
            for e in sec.get("etapas", []):
                etapas.append(cls._etapa(sec.get("nome", ""), e))
        if not etapas:
            raise ValueError(f"{path.name}: o checklist precisa ter pelo menos uma etapa.")
        return cls(tipo=tipo, nome=raw.get("nome", tipo.capitalize()), etapas=etapas,
                   comando=comando)

    @staticmethod
    def _etapa(secao: str, e: dict) -> Etapa:
        dias = e.get("dias")
        if dias is not None:
            try:
                dias = [DIAS_SEMANA.index(str(x).lower()[:3]) for x in dias]
            except ValueError as exc:
                raise ValueError(
                    f"Etapa '{e.get('titulo')}': dias deve usar {DIAS_SEMANA}."
                ) from exc
        return Etapa(
            titulo=e["titulo"],
            instrucao=e.get("instrucao", ""),
            secao=secao,
            foto=e.get("foto", FOTO_OBRIGATORIA),
            fotos=int(e.get("fotos", 1)),
            nao_se_aplica=bool(e.get("nao_se_aplica", True)),
            dias=dias,
            datas=[_to_date(x) for x in e.get("datas", [])],
            exceto=[_to_date(x) for x in e.get("exceto", [])],
        )

    def para_data(self, d: date) -> "Checklist":
        """Checklist só com as etapas que valem naquela data."""
        return Checklist(
            tipo=self.tipo, nome=self.nome, data=d, comando=self.comando,
            etapas=[e for e in self.etapas if e.vale_em(d)],
        )

    def secoes(self) -> list[tuple[str, list[tuple[int, Etapa]]]]:
        """[(nome da seção, [(índice global, etapa), ...]), ...] na ordem do checklist."""
        out: list[tuple[str, list[tuple[int, Etapa]]]] = []
        for i, e in enumerate(self.etapas):
            if not out or out[-1][0] != e.secao:
                out.append((e.secao, []))
            out[-1][1].append((i, e))
        return out

    def to_dict(self) -> dict:
        return {
            "tipo": self.tipo, "nome": self.nome, "comando": self.comando,
            "data": self.data.isoformat() if self.data else None,
            "etapas": [e.to_dict() for e in self.etapas],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Checklist":
        return cls(
            tipo=d["tipo"], nome=d["nome"], comando=d.get("comando", ""),
            data=date.fromisoformat(d["data"]) if d.get("data") else None,
            etapas=[Etapa.from_dict(e) for e in d["etapas"]],
        )

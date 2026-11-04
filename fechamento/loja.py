"""Configuração por loja. Cada loja é uma pasta em lojas/<id>/ com loja.yaml, logo e checklists."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from .checklist import Checklist


@dataclass
class Loja:
    id: str
    nome: str
    local: str
    fuso: str
    pasta: Path
    logo: Path | None = None

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.fuso)

    def agora(self) -> datetime:
        return datetime.now(self.tz)

    def tipos_disponiveis(self) -> list[str]:
        d = self.pasta / "checklists"
        return sorted(p.stem for p in d.glob("*.yaml")) if d.is_dir() else []

    def checklist(self, tipo: str) -> Checklist:
        path = self.pasta / "checklists" / f"{tipo}.yaml"
        if not path.is_file():
            raise FileNotFoundError(tipo)
        return Checklist.carregar(path)

    @classmethod
    def carregar(cls, lojas_dir: str | Path, loja_id: str) -> "Loja":
        pasta = Path(lojas_dir) / loja_id
        arq = pasta / "loja.yaml"
        if not arq.is_file():
            raise FileNotFoundError(f"Loja '{loja_id}' não encontrada em {pasta}.")
        raw = yaml.safe_load(arq.read_text(encoding="utf-8")) or {}
        logo = pasta / raw["logo"] if raw.get("logo") else None
        return cls(
            id=loja_id,
            nome=raw["nome"],
            local=raw.get("local", ""),
            fuso=raw.get("fuso", "America/Sao_Paulo"),
            pasta=pasta,
            logo=logo if logo and logo.is_file() else None,
        )

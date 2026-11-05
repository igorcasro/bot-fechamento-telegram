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

    def tipo_por_comando(self, comando: str) -> str | None:
        """Tipo de checklist iniciado por /comando (None se não houver). Lê os YAMLs na hora,
        então novos checklists funcionam sem reiniciar o bot."""
        for tipo in self.tipos_disponiveis():
            try:
                if self.checklist(tipo).comando == comando:
                    return tipo
            except ValueError:
                # YAML com erro: se o comando padrão (nome do arquivo) bate, devolve o tipo para
                # o bot poder avisar "erro de configuração" em vez de "comando desconhecido".
                if tipo == comando:
                    return tipo
        return None

    def validar(self) -> list[tuple[str, str]]:
        """[(tipo, mensagem de erro)] para os checklists que não carregam."""
        erros = []
        for tipo in self.tipos_disponiveis():
            try:
                self.checklist(tipo)
            except Exception as exc:  # YAML malformado, campo faltando, etc.
                erros.append((tipo, str(exc)))
        return erros

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

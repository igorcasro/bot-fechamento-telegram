"""Arquivo local: fotos, resultado.json e PDFs por dia, com retenção automática."""
from __future__ import annotations

import json
import shutil
from datetime import date, timedelta
from pathlib import Path

from PIL import Image, ImageOps

from .checklist import Checklist
from .sessao import Sessao

MAX_LADO_FOTO = 1280


class Arquivo:
    """Raiz = <ARCHIVE_DIR>/<id da loja>. Estrutura: AAAA-MM-DD/<tipo>_HHMM/..."""

    def __init__(self, raiz: str | Path):
        self.raiz = Path(raiz)

    def pasta(self, s: Sessao) -> Path:
        p = self.raiz / s.pasta
        (p / "fotos").mkdir(parents=True, exist_ok=True)
        return p

    def caminho_foto(self, s: Sessao, idx: int, n: int, hhmmss: str) -> tuple[str, Path]:
        """(caminho relativo à raiz, caminho absoluto) para uma nova foto."""
        rel = f"{s.pasta}/fotos/{idx + 1:02d}_{n}_{hhmmss}.jpg"
        self.pasta(s)
        return rel, self.raiz / rel

    @staticmethod
    def reduzir_foto(path: Path) -> None:
        """Corrige a rotação, limita o tamanho e salva como JPEG (economiza disco e PDF)."""
        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            im.thumbnail((MAX_LADO_FOTO, MAX_LADO_FOTO))
            im.save(path, "JPEG", quality=85)

    def salvar_resultado(self, cl: Checklist, s: Sessao) -> Path:
        arq = self.pasta(s) / "resultado.json"
        arq.write_text(
            json.dumps({"checklist": cl.to_dict(), "sessao": s.to_dict()},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return arq

    def resultados(self, d: date, tipo: str | None = None) -> list[tuple[Checklist, Sessao]]:
        """Resultados salvos de um dia, do mais antigo ao mais recente."""
        out = []
        base = self.raiz / d.isoformat()
        if not base.is_dir():
            return out
        for arq in sorted(base.glob("*/resultado.json")):
            raw = json.loads(arq.read_text(encoding="utf-8"))
            cl, s = Checklist.from_dict(raw["checklist"]), Sessao.from_dict(raw["sessao"])
            if tipo is None or s.tipo == tipo:
                out.append((cl, s))
        return sorted(out, key=lambda x: x[1].iniciado_em)

    def limpar_antigos(self, hoje: date, dias: int) -> list[str]:
        """Apaga pastas de dias com mais de `dias` dias. Retorna os nomes removidos."""
        removidos = []
        if not self.raiz.is_dir():
            return removidos
        limite = hoje - timedelta(days=dias)
        for p in self.raiz.iterdir():
            try:
                d = date.fromisoformat(p.name)
            except ValueError:
                continue  # ignora o que não é pasta de dia
            if p.is_dir() and d < limite:
                shutil.rmtree(p, ignore_errors=True)
                removidos.append(p.name)
        return removidos

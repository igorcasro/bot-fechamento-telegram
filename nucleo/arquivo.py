"""Arquivo local: fotos, resultado.json e PDFs por dia, com retenção automática."""
from __future__ import annotations

import json
import logging
import shutil
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile

from PIL import Image, ImageOps

from .checklist import Checklist
from .sessao import Sessao

MAX_LADO_FOTO = 1280
log = logging.getLogger(__name__)


@contextmanager
def destino_atomico(destino: Path):
    """Publica o arquivo completo por substituição no mesmo diretório."""
    with NamedTemporaryFile(dir=destino.parent, suffix=".tmp", delete=False) as arquivo:
        temporario = Path(arquivo.name)
    try:
        yield temporario
        temporario.replace(destino)
    finally:
        temporario.unlink(missing_ok=True)


class Arquivo:
    """Raiz = <ARCHIVE_DIR>/<id da loja>. Sessões novas têm um UUID após HHMM."""

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
        with destino_atomico(arq) as temporario:
            temporario.write_text(
                json.dumps({"checklist": cl.to_dict(), "sessao": s.to_dict()},
                           ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        return arq

    def resultados(
        self, d: date, tipo: str | None = None, apenas_finalizados: bool = False
    ) -> list[tuple[Checklist, Sessao]]:
        """Sessões salvas de um dia, da mais antiga à mais recente.

        O resultado.json é gravado a cada resposta, então inclui checklists em andamento
        (finalizado_em vazio), o que permite acompanhar o dia a partir de qualquer chat."""
        out = []
        base = self.raiz / d.isoformat()
        if not base.is_dir():
            return out
        for arq in sorted(base.glob("*/resultado.json")):
            try:
                raw = json.loads(arq.read_text(encoding="utf-8"))
                cl, s = Checklist.from_dict(raw["checklist"]), Sessao.from_dict(raw["sessao"])
                datetime.fromisoformat(s.iniciado_em)
                if s.finalizado_em is not None:
                    datetime.fromisoformat(s.finalizado_em)
                for resposta in s.respostas.values():
                    datetime.fromisoformat(resposta.hora)
                    for foto in resposta.fotos:
                        datetime.fromisoformat(foto.hora)
            except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
                log.warning("Resultado ignorado em %s: %s", arq, exc)
                continue
            if (tipo is None or s.tipo == tipo) and (not apenas_finalizados or s.encerrada):
                out.append((cl, s))
        return sorted(out, key=lambda x: x[1].iniciado_em)

    def apagar_sessao(self, s: Sessao) -> None:
        """Remove fotos e dados de uma sessão (usado ao cancelar um checklist)."""
        shutil.rmtree(self.raiz / s.pasta, ignore_errors=True)

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

"""Lógica do fechamento, independente do Telegram (fácil de testar)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml


@dataclass
class Step:
    titulo: str
    instrucao: str
    fotos: int = 1
    obrigatoria: bool = True


@dataclass
class Checklist:
    nome: str
    etapas: list[Step]

    @classmethod
    def load(cls, path: str | Path) -> "Checklist":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        etapas = [Step(**e) for e in data["etapas"]]
        if not etapas:
            raise ValueError("O checklist precisa ter pelo menos uma etapa.")
        return cls(nome=data.get("nome", "Fechamento"), etapas=etapas)


@dataclass
class Session:
    """Estado de um fechamento em andamento. Serializável (dict) para persistir."""

    responsavel: str
    iniciado_em: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    etapa_atual: int = 0
    # índice da etapa -> lista de file_ids do Telegram
    fotos: dict[int, list[str]] = field(default_factory=dict)
    # índice da etapa -> motivo informado ao pular
    puladas: dict[int, str] = field(default_factory=dict)
    # índice da etapa -> legenda/observação enviada junto da foto
    notas: dict[int, list[str]] = field(default_factory=dict)
    # para juntar fotos de um álbum (várias fotos enviadas de uma vez) na mesma etapa
    _ultimo_grupo: str | None = None
    _ultima_etapa: int | None = None

    # ---- serialização -------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "responsavel": self.responsavel,
            "iniciado_em": self.iniciado_em,
            "etapa_atual": self.etapa_atual,
            "fotos": {str(k): v for k, v in self.fotos.items()},
            "puladas": {str(k): v for k, v in self.puladas.items()},
            "notas": {str(k): v for k, v in self.notas.items()},
            "_ultimo_grupo": self._ultimo_grupo,
            "_ultima_etapa": self._ultima_etapa,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Session":
        s = cls(responsavel=d["responsavel"], iniciado_em=d["iniciado_em"])
        s.etapa_atual = d["etapa_atual"]
        s.fotos = {int(k): v for k, v in d["fotos"].items()}
        s.puladas = {int(k): v for k, v in d["puladas"].items()}
        s.notas = {int(k): v for k, v in d["notas"].items()}
        s._ultimo_grupo = d.get("_ultimo_grupo")
        s._ultima_etapa = d.get("_ultima_etapa")
        return s

    # ---- regras -------------------------------------------------------
    def concluida(self, checklist: Checklist) -> bool:
        return self.etapa_atual >= len(checklist.etapas)

    def add_foto(
        self,
        checklist: Checklist,
        file_id: str,
        legenda: str | None = None,
        media_group_id: str | None = None,
    ) -> tuple[int, bool]:
        """Registra uma foto. Retorna (índice da etapa que recebeu, etapa_avancou).

        Fotos de um álbum enviado logo após a etapa avançar são anexadas à etapa
        anterior, em vez de "vazarem" para a próxima.
        """
        if self.concluida(checklist):
            raise ValueError("Fechamento já concluído.")

        if (
            media_group_id
            and media_group_id == self._ultimo_grupo
            and self._ultima_etapa is not None
        ):
            idx = self._ultima_etapa
            self.fotos.setdefault(idx, []).append(file_id)
            if legenda:
                self.notas.setdefault(idx, []).append(legenda)
            return idx, False

        idx = self.etapa_atual
        self.fotos.setdefault(idx, []).append(file_id)
        if legenda:
            self.notas.setdefault(idx, []).append(legenda)

        avancou = len(self.fotos[idx]) >= checklist.etapas[idx].fotos
        if avancou:
            self.etapa_atual += 1
            self._ultimo_grupo = media_group_id
            self._ultima_etapa = idx
        return idx, avancou

    def pular(self, checklist: Checklist, motivo: str) -> int:
        """Pula a etapa atual (só se não for obrigatória). Retorna o índice pulado."""
        if self.concluida(checklist):
            raise ValueError("Fechamento já concluído.")
        idx = self.etapa_atual
        if checklist.etapas[idx].obrigatoria:
            raise PermissionError("Esta etapa é obrigatória e não pode ser pulada.")
        self.puladas[idx] = motivo.strip() or "sem motivo informado"
        self.etapa_atual += 1
        self._ultimo_grupo = None
        self._ultima_etapa = None
        return idx

    def resumo(self, checklist: Checklist) -> str:
        linhas = [
            f"📋 {checklist.nome}",
            f"👤 Responsável: {self.responsavel}",
            f"🕐 Início: {self.iniciado_em.replace('T', ' ')}",
            "",
        ]
        for i, etapa in enumerate(checklist.etapas):
            if i in self.puladas:
                linhas.append(f"⏭️ {etapa.titulo} — PULADA ({self.puladas[i]})")
            else:
                n = len(self.fotos.get(i, []))
                linhas.append(f"✅ {etapa.titulo} — {n} foto(s)")
        return "\n".join(linhas)

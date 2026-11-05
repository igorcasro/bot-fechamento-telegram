"""Estado de um checklist em andamento (máquina de estados), sem dependência do Telegram.

Fluxo de cada etapa:
  1. status:  Concluído | Problema | Não se aplica
  2. Concluído  -> fotos conforme a etapa (obrigatória: precisa das fotos; opcional: pode
                   seguir sem foto; nenhuma: avança direto)
     Problema   -> observação (texto) e/ou fotos, e o funcionário toca em "Continuar"
                   (foto com legenda já basta: a legenda é a observação e a etapa fecha)
     Não se aplica -> avança direto
  Atalho: foto enviada antes de escolher o status conta como "Concluído" (a legenda vira
  observação), sem precisar tocar no botão.
Etapas sem resposta ao finalizar contam como "não realizadas".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .checklist import FOTO_NENHUMA, FOTO_OPCIONAL, Checklist


class Status(str, Enum):
    CONCLUIDO = "concluido"
    PROBLEMA = "problema"
    NAO_SE_APLICA = "nao_se_aplica"
    NAO_REALIZADO = "nao_realizado"


class EstadoInvalido(Exception):
    """A ação não faz sentido no estado atual (ex.: foto antes de escolher o status)."""


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


@dataclass
class FotoReg:
    caminho: str  # relativo à pasta de arquivo da loja
    hora: str  # ISO

    def to_dict(self) -> dict:
        return {"caminho": self.caminho, "hora": self.hora}


@dataclass
class Resposta:
    status: Status
    hora: str  # ISO, momento em que o status foi escolhido
    fotos: list[FotoReg] = field(default_factory=list)
    obs: list[str] = field(default_factory=list)
    fechada: bool = False

    def to_dict(self) -> dict:
        return {
            "status": self.status.value, "hora": self.hora, "fechada": self.fechada,
            "fotos": [f.to_dict() for f in self.fotos], "obs": list(self.obs),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Resposta":
        return cls(
            status=Status(d["status"]), hora=d["hora"], fechada=d.get("fechada", False),
            fotos=[FotoReg(**f) for f in d.get("fotos", [])], obs=list(d.get("obs", [])),
        )


@dataclass
class Sessao:
    tipo: str
    data: str  # AAAA-MM-DD (dia a que o checklist se refere)
    responsavel: str
    iniciado_em: str
    pasta: str  # relativa à pasta de arquivo da loja, ex.: 2026-11-03/fechamento_2238
    finalizado_em: str | None = None
    etapa_atual: int = 0
    respostas: dict[int, Resposta] = field(default_factory=dict)
    # juntar fotos de um álbum (várias fotos de uma vez) na etapa que acabou de fechar
    _ultimo_grupo: str | None = None
    _ultima_etapa: int | None = None

    @classmethod
    def nova(cls, cl: Checklist, responsavel: str, agora: datetime) -> "Sessao":
        assert cl.data is not None, "use Checklist.para_data() antes de iniciar"
        return cls(
            tipo=cl.tipo, data=cl.data.isoformat(), responsavel=responsavel,
            iniciado_em=_iso(agora),
            pasta=f"{cl.data.isoformat()}/{cl.tipo}_{agora:%H%M}",
        )

    # ---- serialização (dict simples, para pickle/JSON) -----------------
    def to_dict(self) -> dict:
        return {
            "tipo": self.tipo, "data": self.data, "responsavel": self.responsavel,
            "iniciado_em": self.iniciado_em, "pasta": self.pasta,
            "finalizado_em": self.finalizado_em, "etapa_atual": self.etapa_atual,
            "respostas": {str(k): v.to_dict() for k, v in self.respostas.items()},
            "_ultimo_grupo": self._ultimo_grupo, "_ultima_etapa": self._ultima_etapa,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Sessao":
        s = cls(
            tipo=d["tipo"], data=d["data"], responsavel=d["responsavel"],
            iniciado_em=d["iniciado_em"], pasta=d["pasta"],
            finalizado_em=d.get("finalizado_em"), etapa_atual=d["etapa_atual"],
        )
        s.respostas = {int(k): Resposta.from_dict(v) for k, v in d["respostas"].items()}
        s._ultimo_grupo = d.get("_ultimo_grupo")
        s._ultima_etapa = d.get("_ultima_etapa")
        return s

    # ---- consultas -----------------------------------------------------
    def concluida(self, cl: Checklist) -> bool:
        """Todas as etapas foram percorridas (falta só finalizar)."""
        return self.etapa_atual >= len(cl.etapas)

    @property
    def encerrada(self) -> bool:
        return self.finalizado_em is not None

    def resposta_atual(self, cl: Checklist) -> Resposta | None:
        """Resposta aberta da etapa atual (status escolhido, falta fotos/observação)."""
        if self.concluida(cl):
            return None
        r = self.respostas.get(self.etapa_atual)
        return r if r and not r.fechada else None

    def fase(self, cl: Checklist) -> str:
        """'status' | 'foto' | 'problema' | 'fim'."""
        if self.concluida(cl):
            return "fim"
        r = self.resposta_atual(cl)
        if r is None:
            return "status"
        return "problema" if r.status is Status.PROBLEMA else "foto"

    def fotos_faltando(self, cl: Checklist) -> int:
        r = self.resposta_atual(cl)
        if r is None or r.status is not Status.CONCLUIDO:
            return 0
        return max(0, cl.etapas[self.etapa_atual].fotos - len(r.fotos))

    def pode_continuar(self, cl: Checklist) -> bool:
        r = self.resposta_atual(cl)
        if r is None:
            return False
        if r.status is Status.PROBLEMA:
            return True
        etapa = cl.etapas[self.etapa_atual]
        return etapa.foto == FOTO_OPCIONAL or self.fotos_faltando(cl) == 0

    def etapa_destino(self, media_group_id: str | None = None) -> int:
        """Índice da etapa que receberia uma foto agora (considera a continuação de álbum)."""
        if (media_group_id and media_group_id == self._ultimo_grupo
                and self._ultima_etapa is not None):
            return self._ultima_etapa
        return self.etapa_atual

    def status_da_etapa(self, idx: int) -> Status:
        r = self.respostas.get(idx)
        return r.status if r and r.fechada else Status.NAO_REALIZADO

    def contagem(self, cl: Checklist) -> dict[Status, int]:
        c = {s: 0 for s in Status}
        for i in range(len(cl.etapas)):
            c[self.status_da_etapa(i)] += 1
        return c

    def total_fotos(self) -> int:
        return sum(len(r.fotos) for r in self.respostas.values())

    def problemas(self, cl: Checklist) -> list[tuple[int, Resposta]]:
        return [(i, r) for i, r in sorted(self.respostas.items())
                if r.fechada and r.status is Status.PROBLEMA]

    def nao_realizadas(self, cl: Checklist) -> list[int]:
        return [i for i in range(len(cl.etapas))
                if self.status_da_etapa(i) is Status.NAO_REALIZADO]

    def duracao_min(self, agora: datetime | None = None) -> int:
        fim = datetime.fromisoformat(self.finalizado_em) if self.finalizado_em else agora
        if fim is None:
            return 0
        return max(0, round((fim - datetime.fromisoformat(self.iniciado_em)).total_seconds() / 60))

    # ---- ações ---------------------------------------------------------
    def _fechar(self, idx: int) -> None:
        self.respostas[idx].fechada = True
        self.etapa_atual = idx + 1

    def responder(self, cl: Checklist, status: Status, agora: datetime) -> bool:
        """Registra o status da etapa atual. Retorna True se a etapa já fechou/avançou."""
        if self.encerrada or self.concluida(cl):
            raise EstadoInvalido("Este checklist já foi concluído.")
        if status not in (Status.CONCLUIDO, Status.PROBLEMA, Status.NAO_SE_APLICA):
            raise ValueError(f"Status inválido para resposta: {status}")
        idx = self.etapa_atual
        if idx in self.respostas:
            raise EstadoInvalido("Esta etapa já tem status; envie a foto ou toque em Continuar.")
        etapa = cl.etapas[idx]
        if status is Status.NAO_SE_APLICA and not etapa.nao_se_aplica:
            raise PermissionError("Esta etapa não pode ser marcada como 'Não se aplica'.")
        self.respostas[idx] = Resposta(status=status, hora=_iso(agora))
        self._ultimo_grupo = self._ultima_etapa = None
        if status is Status.NAO_SE_APLICA or (
            status is Status.CONCLUIDO and etapa.foto == FOTO_NENHUMA
        ):
            self._fechar(idx)
            return True
        return False

    def add_foto(
        self, cl: Checklist, caminho: str, agora: datetime,
        legenda: str | None = None, media_group_id: str | None = None,
    ) -> tuple[int, bool]:
        """Anexa foto. Retorna (índice da etapa que recebeu, etapa_fechou).

        Fotos de um álbum enviado logo após a etapa fechar são anexadas a essa etapa,
        em vez de "vazarem" para a próxima. Foto sem status escolhido marca a etapa como
        Concluída; foto com legenda numa etapa de Problema já a fecha.
        """
        foto = FotoReg(caminho=caminho, hora=_iso(agora))
        if (media_group_id and media_group_id == self._ultimo_grupo
                and self._ultima_etapa is not None):
            r = self.respostas[self._ultima_etapa]
            r.fotos.append(foto)
            if legenda:
                r.obs.append(legenda)
            return self._ultima_etapa, False

        if self.encerrada or self.concluida(cl):
            raise EstadoInvalido("Este checklist já foi concluído.")
        r = self.resposta_atual(cl)
        if r is None:  # foto antes do status = conclusão da etapa
            r = self.respostas[self.etapa_atual] = Resposta(status=Status.CONCLUIDO, hora=_iso(agora))
        r.fotos.append(foto)
        if legenda:
            r.obs.append(legenda)
        idx = self.etapa_atual
        fechar = (len(r.fotos) >= cl.etapas[idx].fotos if r.status is Status.CONCLUIDO
                  else bool(legenda))
        if fechar:
            self._fechar(idx)
            self._ultimo_grupo, self._ultima_etapa = media_group_id, idx
            return idx, True
        return idx, False

    def add_obs(self, cl: Checklist, texto: str) -> int:
        r = self.resposta_atual(cl)
        if r is None:
            raise EstadoInvalido("Escolha o status da etapa antes de escrever uma observação.")
        r.obs.append(texto.strip())
        return self.etapa_atual

    def continuar(self, cl: Checklist) -> int:
        """Fecha a etapa atual (Problema, ou Concluído com foto opcional/completa)."""
        if self.resposta_atual(cl) is None:
            raise EstadoInvalido("Não há etapa aguardando continuação.")
        if not self.pode_continuar(cl):
            raise PermissionError("Esta etapa exige foto antes de continuar.")
        idx = self.etapa_atual
        self._fechar(idx)
        self._ultimo_grupo = self._ultima_etapa = None
        return idx

    def finalizar(self, cl: Checklist, agora: datetime) -> None:
        """Encerra o checklist. Etapas sem resposta completa viram 'não realizadas'."""
        if self.encerrada:
            raise EstadoInvalido("Este checklist já foi finalizado.")
        r = self.resposta_atual(cl)
        if r is not None:
            if self.pode_continuar(cl):
                self.continuar(cl)
            else:  # concluído, mas sem as fotos obrigatórias
                del self.respostas[self.etapa_atual]
        self.finalizado_em = _iso(agora)

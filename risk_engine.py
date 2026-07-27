

import time
import threading
import logging
from collections import deque

import config

logger = logging.getLogger("dlp_monitor.risk_engine")


class Evento:
    def __init__(self, tipo: str, score: int, detalhe: str = ""):
        self.tipo = tipo
        self.score = score
        self.detalhe = detalhe
        self.timestamp = time.time()

    def __repr__(self):
        return f"<Evento {self.tipo} score={self.score} '{self.detalhe}'>"


class RiskEngine:
  

    def __init__(self, on_alert_callback):
      
        self._eventos = deque()
        self._lock = threading.Lock()
        self._on_alert = on_alert_callback
        self._ultima_evidencia = 0

    def registrar_evento(self, tipo: str, detalhe: str = "", multiplicador: int = 1):
        peso_base = config.PESOS_EVENTO.get(tipo, 1)
        score = peso_base * multiplicador
        evento = Evento(tipo, score, detalhe)

        with self._lock:
            self._limpar_janela()
            self._eventos.append(evento)
            score_total = sum(e.score for e in self._eventos)
            nivel = self._classificar(score_total)

        logger.info("Evento: %s | score_total_janela=%d | nivel=%s", evento, score_total, nivel)

        if nivel != "BAIXO":
            self._disparar_alerta(nivel, score_total)

    def _limpar_janela(self):
        agora = time.time()
        while self._eventos and (agora - self._eventos[0].timestamp) > config.JANELA_AGREGACAO_SEGUNDOS:
            self._eventos.popleft()

    def _classificar(self, score_total: int) -> str:
        if score_total >= config.LIMIAR_ALTO:
            return "CRITICO"
        if score_total >= config.LIMIAR_MEDIO:
            return "ALTO"
        if score_total >= config.LIMIAR_BAIXO:
            return "MEDIO"
        return "BAIXO"

    def _disparar_alerta(self, nivel: str, score_total: int):
        agora = time.time()
        # evita disparar evidência/alerta em excesso
        if agora - self._ultima_evidencia < config.INTERVALO_MIN_EVIDENCIA_SEGUNDOS:
            return
        self._ultima_evidencia = agora
        eventos_snapshot = list(self._eventos)
        self._on_alert(nivel, score_total, eventos_snapshot)

"""
Varre periodicamente os processos em execução e sinaliza aqueles
classificados como de risco em config.PROCESSOS_RISCO (gravadores de
tela, acesso remoto, sincronização de nuvem pessoal, etc.).
"""

import time
import logging
import threading

import config

logger = logging.getLogger("dlp_monitor.process")


class ProcessMonitor(threading.Thread):
    def __init__(self, risk_engine, intervalo=5.0):
        super().__init__(daemon=True)
        self.risk_engine = risk_engine
        self.intervalo = intervalo
        self._rodando = True
        self._ja_alertados_nesta_execucao = set()

    def parar(self):
        self._rodando = False

    def run(self):
        try:
            import psutil
        except ImportError:
            logger.error("Biblioteca 'psutil' não instalada — monitor de processos desativado. "
                         "Rode: pip install psutil")
            return

        logger.info("Monitor de processos iniciado.")
        while self._rodando:
            self._verificar_processos(psutil)
            time.sleep(self.intervalo)

    def _verificar_processos(self, psutil):
        nomes_em_execucao = set()
        for proc in psutil.process_iter(attrs=["name"]):
            nome = (proc.info.get("name") or "").lower()
            if nome:
                nomes_em_execucao.add(nome)

        for processo, peso in config.PROCESSOS_RISCO.items():
            if peso <= 0:
                continue
            if processo.lower() in nomes_em_execucao:
                if processo not in self._ja_alertados_nesta_execucao:
                    self.risk_engine.registrar_evento(
                        "PROCESSO_RISCO",
                        detalhe=f"processo de risco em execução: {processo}",
                        multiplicador=peso,
                    )
                    self._ja_alertados_nesta_execucao.add(processo)
            else:
                self._ja_alertados_nesta_execucao.discard(processo)

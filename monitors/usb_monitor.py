"""
Detecta conexão de novos dispositivos de armazenamento USB (pendrives, HDs
externos), um vetor clássico de exfiltração de dados.

Implementação simples baseada em polling das unidades de disco via psutil,
compatível com Windows/Linux/Mac (a forma de identificar "removível" varia
por SO — aqui usamos uma heurística básica que deve ser ajustada conforme
o ambiente real de produção).
"""

import time
import logging
import threading

logger = logging.getLogger("dlp_monitor.usb")


class UsbMonitor(threading.Thread):
    def __init__(self, risk_engine, intervalo=2.0):
        super().__init__(daemon=True)
        self.risk_engine = risk_engine
        self.intervalo = intervalo
        self._rodando = True
        self._dispositivos_conhecidos = set()

    def parar(self):
        self._rodando = False

    def run(self):
        try:
            import psutil
        except ImportError:
            logger.error("Biblioteca 'psutil' não instalada — monitor de USB desativado. "
                         "Rode: pip install psutil")
            return

        logger.info("Monitor de USB iniciado.")
        self._dispositivos_conhecidos = self._listar_removiveis(psutil)

        while self._rodando:
            atuais = self._listar_removiveis(psutil)
            novos = atuais - self._dispositivos_conhecidos
            for dispositivo in novos:
                self.risk_engine.registrar_evento(
                    "USB_CONECTADO",
                    detalhe=f"novo dispositivo removível detectado: {dispositivo}",
                )
            self._dispositivos_conhecidos = atuais
            time.sleep(self.intervalo)

    def _listar_removiveis(self, psutil):
        removiveis = set()
        for part in psutil.disk_partitions(all=False):
            opts = part.opts.lower()
            # Windows costuma expor 'removable' em opts; em Linux/Mac,
            # ajuste esta heurística para o seu caso (ex.: montagem em /media).
            if "removable" in opts or part.mountpoint.startswith("/media"):
                removiveis.add(part.device)
        return removiveis

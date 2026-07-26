"""
DLP Monitor — Ponto de entrada principal.

Inicializa todos os monitores (câmera, teclado, clipboard, USB, processos),
alimenta o motor de risco e dispara alertas ao administrador com evidências
(screenshot + foto da webcam) quando o grau de perigo ultrapassa o limiar
configurado em config.py.

IMPORTANTE (conformidade legal — LGPD):
Este software monitora ativamente tela, área de transferência e câmera do
usuário. Antes de utilizá-lo em ambiente corporativo:
  1. Informe claramente os colaboradores sobre o monitoramento (política
     de uso aceitável assinada, aviso no login, etc.).
  2. Restrinja o uso da câmera e coleta de evidências à finalidade de
     segurança da informação, com base legal e retenção adequadas.
  3. Consulte o time jurídico/DPO da empresa antes de colocar em produção.
"""

import logging
import signal
import sys
import time

import config
import evidence
import alert_manager
import alert_store
from risk_engine import RiskEngine

from monitors.clipboard_monitor import ClipboardMonitor
from monitors.keyboard_monitor import KeyboardMonitor
from monitors.usb_monitor import UsbMonitor
from monitors.process_monitor import ProcessMonitor
from monitors.camera_monitor import CameraMonitor


def configurar_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def ao_disparar_alerta(nivel, score_total, eventos):
    logger = logging.getLogger("dlp_monitor.main")
    logger.warning("Disparando alerta de nível %s (score=%d)", nivel, score_total)

    evidencias = evidence.capturar_evidencias()
    alert_manager.disparar(nivel, score_total, eventos, evidencias)


def main():
    configurar_logging()
    logger = logging.getLogger("dlp_monitor.main")
    logger.info("Iniciando DLP Monitor...")

    alert_store.inicializar_banco()

    engine = RiskEngine(on_alert_callback=ao_disparar_alerta)

    monitores = [
        ClipboardMonitor(engine),
        KeyboardMonitor(engine),
        UsbMonitor(engine),
        ProcessMonitor(engine),
        CameraMonitor(engine),
    ]

    for m in monitores:
        m.start()

    def encerrar(signum, frame):
        logger.info("Encerrando DLP Monitor...")
        for m in monitores:
            m.parar()
        sys.exit(0)

    signal.signal(signal.SIGINT, encerrar)
    signal.signal(signal.SIGTERM, encerrar)

    logger.info("DLP Monitor em execução. Pressione Ctrl+C para parar.")
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
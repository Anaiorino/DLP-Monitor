"""
Captura de evidências no momento do evento suspeito:
 - Screenshot da tela do usuário
 - Foto da webcam (se disponível)

Ambos são salvos com timestamp e retornados para anexo no alerta.
"""

import os
import time
import logging

import config

logger = logging.getLogger("dlp_monitor.evidence")


def _timestamp():
    return time.strftime("%Y%m%d_%H%M%S")


def capturar_screenshot():
    """Retorna o caminho do arquivo de print da tela, ou None em caso de falha."""
    try:
        import pyautogui
        caminho = os.path.join(config.EVIDENCE_DIR, f"print_{_timestamp()}.png")
        img = pyautogui.screenshot()
        img.save(caminho)
        logger.info("Screenshot salvo em %s", caminho)
        return caminho
    except Exception as exc:
        logger.error("Falha ao capturar screenshot: %s", exc)
        return None


def capturar_foto_webcam():
    """Retorna o caminho da foto da webcam, ou None se não houver câmera/falha."""
    try:
        import cv2
        cam = cv2.VideoCapture(0)
        # dá um pequeno tempo para a câmera ajustar exposição
        for _ in range(5):
            ok, frame = cam.read()
        ok, frame = cam.read()
        cam.release()
        if not ok:
            logger.warning("Não foi possível ler frame da webcam.")
            return None
        caminho = os.path.join(config.EVIDENCE_DIR, f"webcam_{_timestamp()}.jpg")
        cv2.imwrite(caminho, frame)
        logger.info("Foto de webcam salva em %s", caminho)
        return caminho
    except Exception as exc:
        logger.error("Falha ao capturar foto da webcam: %s", exc)
        return None


def capturar_evidencias():
    """Captura screenshot + foto da webcam. Retorna dict com os caminhos (podem ser None)."""
    return {
        "screenshot": capturar_screenshot(),
        "webcam": capturar_foto_webcam(),
    }

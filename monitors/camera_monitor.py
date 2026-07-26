"""
Usa a webcam para detectar comportamentos suspeitos:

 1. Mais de um rosto na frente da tela (possível "shoulder surfing" —
    alguém vendo informações sensíveis por cima do ombro do colaborador).
 2. Ausência prolongada do usuário com a sessão desbloqueada (risco de
    terceiros acessarem os dados).
 3. [Opcional/avançado] Detecção de objeto "celular" apontado para a tela,
    via um modelo de detecção de objetos (ex.: YOLO). Este projeto já traz
    o "gancho" pronto (`_detectar_objeto_suspeito`) — basta plugar um
    modelo treinado (não incluído aqui por tamanho/licença).

Usa apenas Haar Cascades (inclusos no OpenCV) para manter o projeto leve
e funcionando offline, sem downloads de modelos externos.
"""

import time
import logging
import threading

import cv2

import config

logger = logging.getLogger("dlp_monitor.camera")


class CameraMonitor(threading.Thread):
    def __init__(self, risk_engine, intervalo=2.0, tempo_ausencia_suspeita=120):
        super().__init__(daemon=True)
        self.risk_engine = risk_engine
        self.intervalo = intervalo
        self.tempo_ausencia_suspeita = tempo_ausencia_suspeita
        self._rodando = True
        self._ultima_vez_rosto_detectado = time.time()
        self._face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def parar(self):
        self._rodando = False

    def run(self):
        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            logger.error("Não foi possível abrir a webcam — monitor de câmera desativado.")
            return

        logger.info("Monitor de câmera iniciado.")
        try:
            while self._rodando:
                ok, frame = cam.read()
                if not ok:
                    time.sleep(self.intervalo)
                    continue

                self._analisar_frame(frame)
                time.sleep(self.intervalo)
        finally:
            cam.release()

    def _analisar_frame(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rostos = self._face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

        if len(rostos) >= 1:
            self._ultima_vez_rosto_detectado = time.time()

        if len(rostos) >= 2:
            self.risk_engine.registrar_evento(
                "CAMERA_ROSTO_EXTRA",
                detalhe=f"{len(rostos)} rostos detectados simultaneamente na webcam",
            )

        ausente_ha = time.time() - self._ultima_vez_rosto_detectado
        if ausente_ha > self.tempo_ausencia_suspeita:
            self.risk_engine.registrar_evento(
                "CAMERA_AUSENCIA_SUSPEITA",
                detalhe=f"nenhum rosto detectado há {int(ausente_ha)}s com sessão possivelmente ativa",
            )
            # evita repetir o mesmo alerta a cada frame
            self._ultima_vez_rosto_detectado = time.time()

        self._detectar_objeto_suspeito(frame)

    def _detectar_objeto_suspeito(self, frame):
        """
        Gancho para detecção de objetos (ex.: celular sendo usado para
        fotografar a tela). Para produção, integre um modelo de detecção
        de objetos (ex.: YOLOv8 via biblioteca 'ultralytics') e, ao
        detectar a classe 'cell phone' com confiança alta, chame:

            self.risk_engine.registrar_evento(
                "CAMERA_OBJETO_SUSPEITO",
                detalhe="celular detectado apontado para a tela",
            )

        Deixado como no-op por padrão para não exigir download de modelos
        pesados nem dependências extras neste projeto base.
        """
        return

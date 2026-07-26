"""
Usa a webcam para detectar comportamentos suspeitos:

 1. Mais de um rosto na frente da tela (possível "shoulder surfing").
 2. Ausência prolongada do usuário com a sessão desbloqueada.
 3. Celular (objeto) apontado para a tela — via YOLOv8 (classe "cell phone"
    do dataset COCO). Quando um celular é detectado, o monitor verifica
    (via screen_ocr.py) se a tela está exibindo dado sensível NAQUELE
    MOMENTO (CPF, telefone, endereço, campos de nome/RG). Só quando as
    duas coisas coincidem é que dispara o evento de maior gravidade —
    isso evita alarme falso de alguém apenas segurando o celular.

A detecção de objeto é opcional (config.ATIVAR_DETECCAO_CELULAR) porque
depende da biblioteca 'ultralytics' (pesada — baixa um modelo na primeira
execução). Se não estiver disponível, o monitor continua funcionando só
com detecção de rosto (Haar Cascade, leve e offline).
"""

import time
import logging
import threading

import cv2

import config
import screen_ocr

logger = logging.getLogger("dlp_monitor.camera")


class CameraMonitor(threading.Thread):
    def __init__(self, risk_engine, intervalo=1.0, tempo_ausencia_suspeita=120):
        super().__init__(daemon=True)
        self.risk_engine = risk_engine
        self.intervalo = intervalo
        self.tempo_ausencia_suspeita = tempo_ausencia_suspeita
        self._rodando = True
        self._ultima_vez_rosto_detectado = time.time()
        self._ultima_deteccao_celular = 0
        self._face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self._modelo_yolo = None  # carregado sob demanda em _carregar_modelo_objeto()

    def parar(self):
        self._rodando = False

    def run(self):
        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            logger.error("Não foi possível abrir a webcam — monitor de câmera desativado.")
            return

        if config.ATIVAR_DETECCAO_CELULAR:
            self._carregar_modelo_objeto()

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
            self._ultima_vez_rosto_detectado = time.time()

        if config.ATIVAR_DETECCAO_CELULAR and self._modelo_yolo is not None:
            self._detectar_celular(frame)

    # ------------------------------------------------------------------
    # Detecção de objeto (celular) + correlação com conteúdo da tela
    # ------------------------------------------------------------------
    def _carregar_modelo_objeto(self):
        try:
            from ultralytics import YOLO
            logger.info("Carregando modelo YOLO (%s) para detecção de celular... "
                        "na primeira vez isso baixa o modelo da internet.", config.YOLO_MODELO)
            self._modelo_yolo = YOLO(config.YOLO_MODELO)
            logger.info("Modelo YOLO carregado com sucesso.")
        except ImportError:
            logger.error("Biblioteca 'ultralytics' não instalada — detecção de celular "
                         "desativada. Rode: pip install ultralytics")
            self._modelo_yolo = None
        except Exception as exc:
            logger.error("Falha ao carregar modelo YOLO: %s", exc)
            self._modelo_yolo = None

    def _detectar_celular(self, frame):
        agora = time.time()
        if agora - self._ultima_deteccao_celular < config.INTERVALO_MIN_DETECCAO_CELULAR:
            return  # evita rodar o modelo pesado em todo frame

        try:
            resultados = self._modelo_yolo.predict(
                frame, verbose=False, conf=config.CONFIANCA_MINIMA_CELULAR
            )
        except Exception as exc:
            logger.error("Erro ao rodar detecção de objeto: %s", exc)
            return

        celular_detectado = False
        for resultado in resultados:
            for classe_id in resultado.boxes.cls.tolist():
                nome_classe = resultado.names[int(classe_id)]
                if nome_classe == "cell phone":
                    celular_detectado = True
                    break
            if celular_detectado:
                break

        if not celular_detectado:
            return

        self._ultima_deteccao_celular = agora
        logger.info("Celular detectado na webcam — verificando conteúdo atual da tela...")

        sensivel, motivo = screen_ocr.tela_contem_dado_sensivel()

        if sensivel:
            self.risk_engine.registrar_evento(
                "CAMERA_FOTO_DADOS_SENSIVEIS",
                detalhe=f"celular apontado para a tela enquanto ela exibia dado sensível ({motivo})",
            )
        else:
            # celular detectado, mas sem dado sensível confirmado na tela agora — risco menor
            self.risk_engine.registrar_evento(
                "CAMERA_OBJETO_SUSPEITO",
                detalhe="celular detectado apontado para a tela (conteúdo da tela não confirmado como sensível)",
            )
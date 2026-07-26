"""
Detecta teclas/atalhos associados à captura de tela:
 - PrintScreen
 - Win + Shift + S (Ferramenta de Captura do Windows)
 - Win + PrtScn
"""

import logging
import threading

logger = logging.getLogger("dlp_monitor.keyboard")


class KeyboardMonitor(threading.Thread):
    def __init__(self, risk_engine):
        super().__init__(daemon=True)
        self.risk_engine = risk_engine
        self._rodando = True
        self._teclas_pressionadas = set()

    def parar(self):
        self._rodando = False

    def run(self):
        try:
            import keyboard  # biblioteca 'keyboard' — pode exigir privilégios de admin
        except ImportError:
            logger.error("Biblioteca 'keyboard' não instalada — monitor de teclado desativado. "
                         "Rode: pip install keyboard")
            return

        logger.info("Monitor de teclado iniciado.")

        keyboard.on_press_key("print screen", lambda e: self._registrar("PrintScreen pressionado"))
        keyboard.add_hotkey("windows+shift+s", lambda: self._registrar("Ferramenta de Captura (Win+Shift+S) acionada"))
        keyboard.add_hotkey("windows+print screen", lambda: self._registrar("Win+PrtScn acionado"))

        # mantém a thread viva enquanto o monitor estiver ativo (os hotkeys
        # acima já rodam em background via callbacks da biblioteca 'keyboard')
        import time
        while self._rodando:
            time.sleep(0.5)

    def _registrar(self, detalhe):
        self.risk_engine.registrar_evento("PRINT_SCREEN", detalhe=detalhe)

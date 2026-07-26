"""
Monitora a área de transferência (Ctrl+C) em busca de palavras-chave e
padrões de dados sensíveis (CPF, cartão de crédito, chaves de API etc.).
"""

import re
import time
import logging
import threading

import config

logger = logging.getLogger("dlp_monitor.clipboard")


class ClipboardMonitor(threading.Thread):
    def __init__(self, risk_engine, intervalo=1.0):
        super().__init__(daemon=True)
        self.risk_engine = risk_engine
        self.intervalo = intervalo
        self._ultimo_conteudo = None
        self._rodando = True
        self._regex_compilados = {
            nome: re.compile(padrao) for nome, padrao in config.REGEX_SENSIVEIS.items()
        }

    def parar(self):
        self._rodando = False

    def run(self):
        try:
            import pyperclip
        except ImportError:
            logger.error("Biblioteca 'pyperclip' não instalada — monitor de clipboard desativado. "
                         "Rode: pip install pyperclip")
            return

        logger.info("Monitor de clipboard iniciado.")
        while self._rodando:
            try:
                conteudo = pyperclip.paste()
            except Exception:
                conteudo = None

            if conteudo and conteudo != self._ultimo_conteudo:
                self._ultimo_conteudo = conteudo
                self._analisar(conteudo)

            time.sleep(self.intervalo)

    def _analisar(self, texto: str):
        texto_lower = texto.lower()

        for palavra in config.KEYWORDS_SENSIVEIS:
            if palavra in texto_lower:
                self.risk_engine.registrar_evento(
                    "RECORTE_SENSIVEL",
                    detalhe=f"palavra-chave '{palavra}' copiada para a área de transferência",
                )
                return  # evita contar o mesmo recorte várias vezes

        for nome, regex in self._regex_compilados.items():
            if regex.search(texto):
                self.risk_engine.registrar_evento(
                    "RECORTE_SENSIVEL",
                    detalhe=f"padrão sensível detectado ({nome}) na área de transferência",
                )
                return

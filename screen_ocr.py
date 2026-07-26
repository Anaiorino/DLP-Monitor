"""
Verifica, via OCR (leitura óptica de caracteres), se a tela atual está
exibindo dados pessoais sensíveis no momento — CPF, telefone, e campos
rotulados como "nome", "endereço", "RG", etc.

Usado em conjunto com a detecção de celular na câmera: só faz sentido
disparar um alerta crítico de "foto tirada de dado sensível" quando as
DUAS coisas coincidem — celular apontado para a tela E a tela mostrando
algo sensível naquele instante.

Requer o motor Tesseract-OCR instalado no sistema (não é só biblioteca
Python) — ver instruções no README.
"""

import re
import logging

import config

logger = logging.getLogger("dlp_monitor.screen_ocr")

# Regex de dados sensíveis, focado no que aparece em documentos/cadastros BR
_REGEX_CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
_REGEX_TELEFONE = re.compile(r"\(?\d{2}\)?\s?9?\d{4}-?\d{4}\b")
_REGEX_CEP = re.compile(r"\b\d{5}-?\d{3}\b")

# Rótulos de campo que costumam anteceder dado pessoal em formulários/documentos
_LABELS_SENSIVEIS = [
    "cpf", "rg:", "nome completo", "nome:", "endereço", "endereco",
    "telefone", "celular:", "data de nascimento", "nascimento:",
]

_tesseract_configurado = False


def _configurar_tesseract():
    """Configura o caminho do executável do Tesseract, se definido em config.py."""
    global _tesseract_configurado
    if _tesseract_configurado:
        return
    try:
        import pytesseract
        if config.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD
    except ImportError:
        pass
    _tesseract_configurado = True


def _extrair_texto_da_tela():
    """Tira um screenshot e roda OCR nele. Retorna o texto em minúsculas, ou None se falhar."""
    _configurar_tesseract()
    try:
        import pyautogui
        import pytesseract
    except ImportError as exc:
        logger.error("Bibliotecas de OCR não instaladas (pyautogui/pytesseract): %s", exc)
        return None

    try:
        img = pyautogui.screenshot()
        texto = pytesseract.image_to_string(img, lang=config.OCR_IDIOMA)
        return texto.lower()
    except Exception as exc:
        logger.error("Falha ao rodar OCR na tela: %s (verifique se o Tesseract-OCR está "
                     "instalado no sistema, não só a biblioteca Python)", exc)
        return None


def tela_contem_dado_sensivel():
    """
    Retorna (True, motivo) se a tela atual parece conter dado pessoal sensível
    (CPF, telefone, CEP, ou um rótulo como 'nome completo'/'endereço').
    Retorna (False, None) caso contrário ou se o OCR falhar.
    """
    texto = _extrair_texto_da_tela()
    if not texto:
        return False, None

    if _REGEX_CPF.search(texto):
        return True, "CPF visível na tela"

    if _REGEX_TELEFONE.search(texto):
        return True, "número de telefone visível na tela"

    if _REGEX_CEP.search(texto):
        return True, "CEP/endereço visível na tela"

    for label in _LABELS_SENSIVEIS:
        if label in texto:
            return True, f"campo sensível visível na tela (contém '{label}')"

    return False, None
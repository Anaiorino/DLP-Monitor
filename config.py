
import os

# ---------------------------------------------------------------------------
# Diretorios
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EVIDENCE_DIR = os.path.join(BASE_DIR, "evidencias")
LOG_FILE = os.path.join(BASE_DIR, "dlp_monitor.log")
DB_PATH = os.path.join(BASE_DIR, "alertas.db")  # banco local lido pelo admin_panel.py

os.makedirs(EVIDENCE_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Email do adm ( alert_manager.py)
# ---------------------------------------------------------------------------
SMTP_HOST = os.environ.get("DLP_SMTP_HOST", "smtp.seudominio.com")
SMTP_PORT = int(os.environ.get("DLP_SMTP_PORT", 587))
SMTP_USER = os.environ.get("DLP_SMTP_USER", "alertas@seudominio.com")
SMTP_PASSWORD = os.environ.get("DLP_SMTP_PASSWORD", "")  # nunca deixe senha em texto puro no código
ADMIN_EMAIL = os.environ.get("DLP_ADMIN_EMAIL", "admin@seudominio.com")

# Alternativa: webhook (Slack/Teams/n8n)
WEBHOOK_URL = os.environ.get("DLP_WEBHOOK_URL", None)


PAINEL_SENHA = os.environ.get("DLP_PAINEL_SENHA", "")


KEYWORDS_SENSIVEIS = [
    "confidencial", "sigiloso", "interno", "não divulgar",
    "senha", "password", "contrato", "salario", "salário",
]


REGEX_SENSIVEIS = {
    "CPF": r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b",
    "CARTAO_CREDITO": r"\b(?:\d[ -]*?){13,16}\b",
    "CHAVE_API": r"\b(sk-|api_key|secret_key)[A-Za-z0-9_\-]{10,}\b",
}


PROCESSOS_RISCO = {
    "obs64.exe": 2,
    "obs32.exe": 2,
    "camtasia.exe": 2,
    "anydesk.exe": 3,
    "teamviewer.exe": 3,
    "discord.exe": 1,         
    "dropbox.exe": 1,
    "onedrive.exe": 0,         
}



ATIVAR_DETECCAO_CELULAR = os.environ.get("DLP_DETECCAO_CELULAR", "1") == "1"


YOLO_MODELO = os.environ.get("DLP_YOLO_MODELO", "yolov8n.pt")

CONFIANCA_MINIMA_CELULAR = 0.5


INTERVALO_MIN_DETECCAO_CELULAR = 2.0


TESSERACT_CMD = os.environ.get("DLP_TESSERACT_CMD", None)


OCR_IDIOMA = os.environ.get("DLP_OCR_IDIOMA", "por")


PESOS_EVENTO = {
    "PRINT_SCREEN": 3,
    "RECORTE_SENSIVEL": 4,
    "USB_CONECTADO": 3,
    "PROCESSO_RISCO": 2,   
    "CAMERA_ROSTO_EXTRA": 4,  
    "CAMERA_AUSENCIA_SUSPEITA": 1,
    "CAMERA_OBJETO_SUSPEITO": 5,   
    "CAMERA_FOTO_DADOS_SENSIVEIS": 12,  
}


LIMIAR_BAIXO = 3
LIMIAR_MEDIO = 6
LIMIAR_ALTO = 9

JANELA_AGREGACAO_SEGUNDOS = 30


INTERVALO_MIN_EVIDENCIA_SEGUNDOS = 15

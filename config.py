"""
Configurações centrais do DLP Monitor.
Ajuste os valores abaixo conforme a política de segurança da sua organização.
"""

import os

# ---------------------------------------------------------------------------
# Diretórios
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EVIDENCE_DIR = os.path.join(BASE_DIR, "evidencias")
LOG_FILE = os.path.join(BASE_DIR, "dlp_monitor.log")
DB_PATH = os.path.join(BASE_DIR, "alertas.db")  # banco local lido pelo admin_panel.py

os.makedirs(EVIDENCE_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# E-mail do administrador (usado pelo alert_manager.py)
# ---------------------------------------------------------------------------
SMTP_HOST = os.environ.get("DLP_SMTP_HOST", "smtp.seudominio.com")
SMTP_PORT = int(os.environ.get("DLP_SMTP_PORT", 587))
SMTP_USER = os.environ.get("DLP_SMTP_USER", "alertas@seudominio.com")
SMTP_PASSWORD = os.environ.get("DLP_SMTP_PASSWORD", "")  # nunca deixe senha em texto puro no código
ADMIN_EMAIL = os.environ.get("DLP_ADMIN_EMAIL", "admin@seudominio.com")

# Alternativa: webhook (Slack/Teams/n8n) — deixe None para desativar
WEBHOOK_URL = os.environ.get("DLP_WEBHOOK_URL", None)

# ---------------------------------------------------------------------------
# Painel do administrador (programa desktop separado, admin_panel.py)
# Senha local opcional pedida ao abrir o painel (não é autenticação de rede,
# é só uma barreira contra uso casual por quem sentar na máquina).
# Deixe vazio ("") para não pedir senha.
# ---------------------------------------------------------------------------
PAINEL_SENHA = os.environ.get("DLP_PAINEL_SENHA", "")

# ---------------------------------------------------------------------------
# Palavras-chave e padrões sensíveis monitorados na área de transferência
# ---------------------------------------------------------------------------
KEYWORDS_SENSIVEIS = [
    "confidencial", "sigiloso", "interno", "não divulgar",
    "senha", "password", "contrato", "salario", "salário",
]

# Regex de dados sensíveis (CPF, cartão de crédito, e-mail corporativo etc.)
REGEX_SENSIVEIS = {
    "CPF": r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b",
    "CARTAO_CREDITO": r"\b(?:\d[ -]*?){13,16}\b",
    "CHAVE_API": r"\b(sk-|api_key|secret_key)[A-Za-z0-9_\-]{10,}\b",
}

# ---------------------------------------------------------------------------
# Processos considerados de risco (gravação de tela, compartilhamento remoto,
# upload em massa para nuvem pessoal, etc.) — ajuste para a realidade da empresa
# ---------------------------------------------------------------------------
PROCESSOS_RISCO = {
    "obs64.exe": 2,
    "obs32.exe": 2,
    "camtasia.exe": 2,
    "anydesk.exe": 3,
    "teamviewer.exe": 3,
    "discord.exe": 1,          # pode ser usado p/ compartilhar tela
    "dropbox.exe": 1,
    "onedrive.exe": 0,         # geralmente corporativo, risco baixo
}

# ---------------------------------------------------------------------------
# Pesos usados no motor de risco (risk_engine.py)
# ---------------------------------------------------------------------------
PESOS_EVENTO = {
    "PRINT_SCREEN": 3,
    "RECORTE_SENSIVEL": 4,
    "USB_CONECTADO": 3,
    "PROCESSO_RISCO": 2,   # multiplicado pelo peso do processo específico
    "CAMERA_ROSTO_EXTRA": 4,   # mais de uma pessoa olhando a tela
    "CAMERA_AUSENCIA_SUSPEITA": 1,
    "CAMERA_OBJETO_SUSPEITO": 5,  # ex.: celular apontado para tela
}

# Limiares de classificação do score acumulado numa janela de tempo
LIMIAR_BAIXO = 3
LIMIAR_MEDIO = 6
LIMIAR_ALTO = 9
# acima de LIMIAR_ALTO => CRÍTICO

# Janela (segundos) usada para agregar eventos antes de classificar o risco
JANELA_AGREGACAO_SEGUNDOS = 30

# Intervalo mínimo entre capturas de evidência (evita spam de fotos/prints)
INTERVALO_MIN_EVIDENCIA_SEGUNDOS = 15
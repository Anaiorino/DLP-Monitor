"""
Envia o alerta ao administrador por e-mail (com evidências anexadas) e,
opcionalmente, para um webhook (Slack/Teams/n8n/etc).
"""

import logging
import smtplib
import json
import urllib.request
from email.message import EmailMessage

import config
import alert_store

logger = logging.getLogger("dlp_monitor.alert_manager")

EMOJI_NIVEL = {
    "MEDIO": "🟡",
    "ALTO": "🟠",
    "CRITICO": "🔴",
}


def _montar_corpo(nivel, score_total, eventos):
    linhas = [
        f"Grau de risco de vazamento: {nivel}",
        f"Score acumulado na janela: {score_total}",
        "",
        "Eventos que compõem este alerta:",
    ]
    for e in eventos:
        linhas.append(f" - {e.tipo} (score {e.score}) — {e.detalhe}")
    return "\n".join(linhas)


def enviar_email(nivel, score_total, eventos, evidencias):
    if not config.SMTP_PASSWORD:
        logger.warning("SMTP não configurado (DLP_SMTP_PASSWORD vazio) — pulando envio de e-mail. "
                        "Configure as variáveis de ambiente DLP_SMTP_*.")
        return False
    try:
        msg = EmailMessage()
        emoji = EMOJI_NIVEL.get(nivel, "⚠️")
        msg["Subject"] = f"{emoji} [DLP Monitor] Alerta de risco {nivel} de vazamento de dados"
        msg["From"] = config.SMTP_USER
        msg["To"] = config.ADMIN_EMAIL
        msg.set_content(_montar_corpo(nivel, score_total, eventos))

        for tipo, caminho in evidencias.items():
            if caminho:
                with open(caminho, "rb") as f:
                    dados = f.read()
                msg.add_attachment(dados, maintype="application", subtype="octet-stream",
                                    filename=caminho.split("/")[-1])

        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("E-mail de alerta enviado para %s", config.ADMIN_EMAIL)
        return True
    except Exception as exc:
        logger.error("Falha ao enviar e-mail de alerta: %s", exc)
        return False


def enviar_webhook(nivel, score_total, eventos, evidencias):
    if not config.WEBHOOK_URL:
        return False
    try:
        payload = {
            "nivel": nivel,
            "score_total": score_total,
            "eventos": [{"tipo": e.tipo, "score": e.score, "detalhe": e.detalhe} for e in eventos],
            "evidencias": evidencias,
        }
        req = urllib.request.Request(
            config.WEBHOOK_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=5)
        logger.info("Alerta enviado ao webhook.")
        return True
    except Exception as exc:
        logger.error("Falha ao enviar alerta ao webhook: %s", exc)
        return False


def disparar(nivel, score_total, eventos, evidencias):
    logger.warning("ALERTA %s | score=%d | eventos=%d", nivel, score_total, len(eventos))

    # Sempre grava no banco local — é o que alimenta o painel admin (admin_panel.py)
    try:
        alert_store.salvar_alerta(nivel, score_total, eventos, evidencias)
    except Exception as exc:
        logger.error("Falha ao salvar alerta no banco local: %s", exc)

    enviado_email = enviar_email(nivel, score_total, eventos, evidencias)
    enviado_webhook = enviar_webhook(nivel, score_total, eventos, evidencias)
    if not enviado_email and not enviado_webhook:
        logger.info("E-mail/webhook não configurados — alerta disponível apenas no painel admin local.")
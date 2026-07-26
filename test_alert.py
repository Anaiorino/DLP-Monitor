"""
Dispara um alerta de teste manualmente, sem precisar esperar uma detecção
real (PrintScreen, USB, clipboard, etc.). Útil para testar se o painel
admin (admin_panel.py) está recebendo e exibindo os alertas corretamente.

Uso:
    python test_alert.py                # alerta ALTO com evidências reais
    python test_alert.py --nivel CRITICO
    python test_alert.py --sem-evidencia # não tira print/foto, só testa o fluxo
"""

import argparse
import logging

import evidence
import alert_manager
from risk_engine import Evento

logging.basicConfig(level=logging.INFO,
                     format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")

NIVEIS_VALIDOS = ["MEDIO", "ALTO", "CRITICO"]

SCORE_POR_NIVEL = {
    "MEDIO": 4,
    "ALTO": 7,
    "CRITICO": 10,
}


def main():
    parser = argparse.ArgumentParser(description="Dispara um alerta de teste no DLP Monitor.")
    parser.add_argument("--nivel", choices=NIVEIS_VALIDOS, default="ALTO",
                         help="Grau de risco do alerta de teste (padrão: ALTO)")
    parser.add_argument("--sem-evidencia", action="store_true",
                         help="Não captura screenshot/webcam, só testa o fluxo de alerta")
    args = parser.parse_args()

    eventos_teste = [
        Evento("PRINT_SCREEN", 3, "teste manual: PrintScreen simulado"),
        Evento("RECORTE_SENSIVEL", 4, "teste manual: CPF simulado copiado para a área de transferência"),
    ]

    if args.sem_evidencia:
        evidencias = {"screenshot": None, "webcam": None}
        print("Gerando alerta de teste SEM capturar evidências reais...")
    else:
        print("Capturando evidências de teste (screenshot + webcam, se disponível)...")
        evidencias = evidence.capturar_evidencias()

    score_total = SCORE_POR_NIVEL[args.nivel]
    print(f"Disparando alerta de teste — nível={args.nivel}, score={score_total}")

    alert_manager.disparar(args.nivel, score_total, eventos_teste, evidencias)

    print("\n✅ Alerta de teste enviado! Abra (ou atualize) o admin_panel.py para conferir.")


if __name__ == "__main__":
    main()
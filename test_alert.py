"""
    python test_alert.py                     # alerta ALTO com evidências reais
    python test_alert.py --nivel CRITICO
    python test_alert.py --sem-evidencia      # não tira print/foto, só testa o fluxo
    python test_alert.py --cenario celular    # simula o alerta de "celular + tela sensível"
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

CENARIOS = {
    "generico": [
        Evento("PRINT_SCREEN", 3, "teste manual: PrintScreen simulado"),
        Evento("RECORTE_SENSIVEL", 4, "teste manual: CPF simulado copiado para a área de transferência"),
    ],
    "celular": [
        Evento("CAMERA_FOTO_DADOS_SENSIVEIS", 12,
               "teste manual: celular apontado para a tela enquanto ela exibia CPF visível na tela"),
    ],
}


def main():
    parser = argparse.ArgumentParser(description="Dispara um alerta de teste no DLP Monitor.")
    parser.add_argument("--nivel", choices=NIVEIS_VALIDOS, default="ALTO",
                         help="Grau de risco do alerta de teste (padrão: ALTO). Ignorado no cenário 'celular'.")
    parser.add_argument("--cenario", choices=list(CENARIOS.keys()), default="generico",
                         help="Qual conjunto de eventos simular (padrão: generico)")
    parser.add_argument("--sem-evidencia", action="store_true",
                         help="Não captura screenshot/webcam, só testa o fluxo de alerta")
    args = parser.parse_args()

    eventos_teste = CENARIOS[args.cenario]

    if args.sem_evidencia:
        evidencias = {"screenshot": None, "webcam": None}
        print("Gerando alerta de teste SEM capturar evidências reais...")
    else:
        print("Capturando evidências de teste (screenshot + webcam, se disponível)...")
        evidencias = evidence.capturar_evidencias()

    score_total = SCORE_POR_NIVEL[args.nivel] if args.cenario == "generico" else sum(e.score for e in eventos_teste)
    nivel = args.nivel if args.cenario == "generico" else "CRITICO"
    print(f"Disparando alerta de teste — cenário={args.cenario}, nível={nivel}, score={score_total}")

    alert_manager.disparar(nivel, score_total, eventos_teste, evidencias)

    print("\n Alerta de teste enviado.")


if __name__ == "__main__":
    main()


import sqlite3
import time
import json
import logging
import threading

import config

logger = logging.getLogger("dlp_monitor.alert_store")

_lock = threading.Lock()


def _conectar():
    conn = sqlite3.connect(config.DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")  
    return conn


def inicializar_banco():
    with _lock, _conectar() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alertas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                nivel TEXT NOT NULL,
                score_total INTEGER NOT NULL,
                eventos_json TEXT NOT NULL,
                screenshot_path TEXT,
                webcam_path TEXT,
                lido INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.commit()
    logger.info("Banco de alertas inicializado em %s", config.DB_PATH)


def salvar_alerta(nivel, score_total, eventos, evidencias):
    """Grava um novo alerta no banco. `eventos` é uma lista de objetos Evento."""
    eventos_serializados = [
        {"tipo": e.tipo, "score": e.score, "detalhe": e.detalhe, "timestamp": e.timestamp}
        for e in eventos
    ]
    with _lock, _conectar() as conn:
        conn.execute(
            """
            INSERT INTO alertas (timestamp, nivel, score_total, eventos_json, screenshot_path, webcam_path, lido)
            VALUES (?, ?, ?, ?, ?, ?, 0)
            """,
            (
                time.time(),
                nivel,
                score_total,
                json.dumps(eventos_serializados, ensure_ascii=False),
                evidencias.get("screenshot"),
                evidencias.get("webcam"),
            ),
        )
        conn.commit()
    logger.info("Alerta persistido no banco local (nivel=%s, score=%d)", nivel, score_total)


def listar_alertas(limite=200, apenas_nao_lidos=False):
   
    query = "SELECT id, timestamp, nivel, score_total, eventos_json, screenshot_path, webcam_path, lido FROM alertas"
    if apenas_nao_lidos:
        query += " WHERE lido = 0"
    query += " ORDER BY timestamp DESC LIMIT ?"

    with _lock, _conectar() as conn:
        conn.row_factory = sqlite3.Row
        linhas = conn.execute(query, (limite,)).fetchall()

    alertas = []
    for linha in linhas:
        alertas.append({
            "id": linha["id"],
            "timestamp": linha["timestamp"],
            "nivel": linha["nivel"],
            "score_total": linha["score_total"],
            "eventos": json.loads(linha["eventos_json"]),
            "screenshot_path": linha["screenshot_path"],
            "webcam_path": linha["webcam_path"],
            "lido": bool(linha["lido"]),
        })
    return alertas


def marcar_como_lido(alerta_id):
    with _lock, _conectar() as conn:
        conn.execute("UPDATE alertas SET lido = 1 WHERE id = ?", (alerta_id,))
        conn.commit()


def contar_nao_lidos():
    with _lock, _conectar() as conn:
        (total,) = conn.execute("SELECT COUNT(*) FROM alertas WHERE lido = 0").fetchone()
    return total

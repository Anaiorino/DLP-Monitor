"""
DLP Monitor — Painel do Administrador (programa desktop, sem rede/web).

Executa como um processo independente do monitor (main.py). Lê os alertas
diretamente do banco SQLite local (alertas.db) e exibe numa interface
gráfica nativa (Tkinter, incluso no Python — nenhuma dependência de
servidor/HTTP/porta de rede).

Uso:
    python admin_panel.py

Opcional: proteja o acesso ao painel definindo uma senha local — ver
config.PAINEL_SENHA. Como é um programa local (não web), a "senha" serve
apenas para impedir uso casual por quem sentar na máquina, não substitui
o controle de acesso do próprio sistema operacional (conta de usuário).
"""

import os
import time
import logging
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import config
import alert_store

logger = logging.getLogger("dlp_monitor.admin_panel")

CORES_NIVEL = {
    "BAIXO": "#3FA796",
    "MEDIO": "#E8B339",
    "ALTO": "#E8763F",
    "CRITICO": "#E14B4B",
}

INTERVALO_ATUALIZACAO_MS = 3000  # verifica novos alertas a cada 3s


class PainelAdmin(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DLP Monitor — Painel do Administrador")
        self.geometry("1100x650")
        self.configure(bg="#0B0F14")
        self._alerta_selecionado_id = None
        self._imagens_atuais = []  # mantém referência para o Tkinter não descartar as imagens

        self._montar_estilo()
        self._montar_layout()
        self._verificar_senha_opcional()
        self._atualizar_lista()
        self._agendar_atualizacao()

    # ------------------------------------------------------------------
    # Setup visual
    # ------------------------------------------------------------------
    def _montar_estilo(self):
        estilo = ttk.Style(self)
        estilo.theme_use("clam")

        estilo.configure("Treeview",
                          background="#12181F", foreground="#E4E9EF",
                          fieldbackground="#12181F", rowheight=28, borderwidth=0)
        estilo.configure("Treeview.Heading",
                          background="#181F27", foreground="#7C8798",
                          font=("Segoe UI", 9, "bold"), borderwidth=0)
        estilo.map("Treeview", background=[("selected", "#232B35")])

    def _montar_layout(self):
        # Barra superior
        topo = tk.Frame(self, bg="#0B0F14")
        topo.pack(fill="x", padx=16, pady=(14, 8))

        tk.Label(topo, text="DLP MONITOR", bg="#0B0F14", fg="#E4E9EF",
                 font=("Consolas", 16, "bold")).pack(side="left")
        tk.Label(topo, text="  ·  painel do administrador", bg="#0B0F14", fg="#7C8798",
                 font=("Segoe UI", 11)).pack(side="left")

        self.label_status = tk.Label(topo, text="", bg="#0B0F14", fg="#7C8798",
                                      font=("Consolas", 10))
        self.label_status.pack(side="right")

        # Corpo: lista à esquerda, detalhe à direita
        corpo = tk.Frame(self, bg="#0B0F14")
        corpo.pack(fill="both", expand=True, padx=16, pady=8)

        painel_lista = tk.Frame(corpo, bg="#0B0F14")
        painel_lista.pack(side="left", fill="both", expand=True)

        colunas = ("nivel", "quando", "score", "resumo")
        self.tree = ttk.Treeview(painel_lista, columns=colunas, show="headings", selectmode="browse")
        self.tree.heading("nivel", text="RISCO")
        self.tree.heading("quando", text="QUANDO")
        self.tree.heading("score", text="SCORE")
        self.tree.heading("resumo", text="RESUMO")
        self.tree.column("nivel", width=90, anchor="center")
        self.tree.column("quando", width=140, anchor="center")
        self.tree.column("score", width=70, anchor="center")
        self.tree.column("resumo", width=380, anchor="w")
        self.tree.pack(fill="both", expand=True, side="left")
        self.tree.bind("<<TreeviewSelect>>", self._ao_selecionar)

        scroll = ttk.Scrollbar(painel_lista, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")

        # Painel de detalhe
        self.painel_detalhe = tk.Frame(corpo, bg="#12181F", width=380)
        self.painel_detalhe.pack(side="right", fill="y", padx=(12, 0))
        self.painel_detalhe.pack_propagate(False)

        self._montar_detalhe_vazio()

    def _montar_detalhe_vazio(self):
        for widget in self.painel_detalhe.winfo_children():
            widget.destroy()
        tk.Label(self.painel_detalhe, text="Selecione um alerta\nà esquerda para ver detalhes",
                 bg="#12181F", fg="#7C8798", font=("Segoe UI", 10), justify="center").pack(
            expand=True)

    # ------------------------------------------------------------------
    # Senha local opcional
    # ------------------------------------------------------------------
    def _verificar_senha_opcional(self):
        if not config.PAINEL_SENHA:
            return
        senha = simpledialog.askstring("Acesso ao painel", "Senha do administrador:", show="*")
        if senha != config.PAINEL_SENHA:
            messagebox.showerror("Acesso negado", "Senha incorreta. O painel será fechado.")
            self.destroy()
            os._exit(1)

    # ------------------------------------------------------------------
    # Atualização periódica (polling local do SQLite, sem rede)
    # ------------------------------------------------------------------
    def _agendar_atualizacao(self):
        self.after(INTERVALO_ATUALIZACAO_MS, self._ciclo_atualizacao)

    def _ciclo_atualizacao(self):
        self._atualizar_lista()
        self._agendar_atualizacao()

    def _atualizar_lista(self):
        try:
            alertas = alert_store.listar_alertas(limite=300)
        except Exception as exc:
            self.label_status.config(text=f"erro ao ler banco: {exc}")
            return

        selecionado_antes = self._alerta_selecionado_id
        self.tree.delete(*self.tree.get_children())

        for alerta in alertas:
            quando = time.strftime("%d/%m %H:%M:%S", time.localtime(alerta["timestamp"]))
            resumo = alerta["eventos"][-1]["detalhe"] if alerta["eventos"] else ""
            tag = alerta["nivel"]
            item_id = self.tree.insert(
                "", "end", iid=str(alerta["id"]),
                values=(alerta["nivel"], quando, alerta["score_total"], resumo),
                tags=(tag,),
            )
            self.tree.tag_configure(tag, foreground=CORES_NIVEL.get(tag, "#E4E9EF"))

        naolidos = alert_store.contar_nao_lidos()
        self.label_status.config(
            text=f"{len(alertas)} alertas no total   ·   {naolidos} não lidos   ·   "
                 f"atualizado {time.strftime('%H:%M:%S')}"
        )

        if selecionado_antes and self.tree.exists(str(selecionado_antes)):
            self.tree.selection_set(str(selecionado_antes))

    # ------------------------------------------------------------------
    # Detalhe do alerta selecionado
    # ------------------------------------------------------------------
    def _ao_selecionar(self, _evento):
        selecao = self.tree.selection()
        if not selecao:
            return
        alerta_id = int(selecao[0])
        self._alerta_selecionado_id = alerta_id

        alertas = alert_store.listar_alertas(limite=300)
        alerta = next((a for a in alertas if a["id"] == alerta_id), None)
        if not alerta:
            return

        alert_store.marcar_como_lido(alerta_id)
        self._renderizar_detalhe(alerta)

    def _renderizar_detalhe(self, alerta):
        for widget in self.painel_detalhe.winfo_children():
            widget.destroy()
        self._imagens_atuais.clear()

        cor = CORES_NIVEL.get(alerta["nivel"], "#E4E9EF")
        cabecalho = tk.Frame(self.painel_detalhe, bg="#12181F")
        cabecalho.pack(fill="x", padx=14, pady=(14, 6))

        tk.Label(cabecalho, text=alerta["nivel"], bg=cor, fg="#0B0F14",
                 font=("Consolas", 11, "bold"), padx=8, pady=2).pack(side="left")
        tk.Label(cabecalho, text=f"  score {alerta['score_total']}", bg="#12181F", fg="#7C8798",
                 font=("Consolas", 10)).pack(side="left")

        quando = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(alerta["timestamp"]))
        tk.Label(self.painel_detalhe, text=quando, bg="#12181F", fg="#7C8798",
                 font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(0, 10))

        tk.Label(self.painel_detalhe, text="EVENTOS", bg="#12181F", fg="#7C8798",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=14)

        lista_eventos = tk.Frame(self.painel_detalhe, bg="#12181F")
        lista_eventos.pack(fill="x", padx=14, pady=(2, 10))
        for evento in alerta["eventos"]:
            linha = f"• {evento['tipo']} (peso {evento['score']}) — {evento['detalhe']}"
            tk.Label(lista_eventos, text=linha, bg="#12181F", fg="#E4E9EF",
                     font=("Segoe UI", 9), wraplength=340, justify="left").pack(anchor="w", pady=1)

        tk.Label(self.painel_detalhe, text="EVIDÊNCIAS", bg="#12181F", fg="#7C8798",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=14, pady=(4, 2))

        area_imagens = tk.Frame(self.painel_detalhe, bg="#12181F")
        area_imagens.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        self._exibir_miniatura(area_imagens, "Tela (screenshot)", alerta["screenshot_path"])
        self._exibir_miniatura(area_imagens, "Webcam", alerta["webcam_path"])

    def _exibir_miniatura(self, container, titulo, caminho):
        tk.Label(container, text=titulo, bg="#12181F", fg="#7C8798",
                 font=("Segoe UI", 8)).pack(anchor="w", pady=(6, 2))

        if not caminho or not os.path.exists(caminho):
            tk.Label(container, text="(sem imagem)", bg="#12181F", fg="#4A5563",
                     font=("Segoe UI", 9, "italic")).pack(anchor="w")
            return

        try:
            from PIL import Image, ImageTk
            img = Image.open(caminho)
            img.thumbnail((340, 220))
            foto = ImageTk.PhotoImage(img)
            self._imagens_atuais.append(foto)  # evita garbage collection

            label_img = tk.Label(container, image=foto, bg="#12181F", cursor="hand2")
            label_img.pack(anchor="w")
            label_img.bind("<Button-1>", lambda _e, c=caminho, t=titulo: self._abrir_visualizacao_grande(c, t))

            tk.Label(container, text="clique para ampliar", bg="#12181F", fg="#4A5563",
                     font=("Segoe UI", 7, "italic")).pack(anchor="w", pady=(0, 4))
        except ImportError:
            tk.Label(container, text=f"(instale 'pillow' para pré-visualizar: {caminho})",
                     bg="#12181F", fg="#4A5563", font=("Segoe UI", 8, "italic"),
                     wraplength=340, justify="left").pack(anchor="w")
        except Exception as exc:
            tk.Label(container, text=f"(erro ao abrir imagem: {exc})",
                     bg="#12181F", fg="#E14B4B", font=("Segoe UI", 8),
                     wraplength=340, justify="left").pack(anchor="w")

    # ------------------------------------------------------------------
    # Janela de visualização ampliada (abre ao clicar numa miniatura)
    # ------------------------------------------------------------------
    def _abrir_visualizacao_grande(self, caminho, titulo):
        if not caminho or not os.path.exists(caminho):
            return

        try:
            from PIL import Image, ImageTk
        except ImportError:
            messagebox.showerror("Pillow não instalado", "Instale a biblioteca 'pillow' para ampliar imagens.")
            return

        try:
            img_original = Image.open(caminho)
        except Exception as exc:
            messagebox.showerror("Erro ao abrir imagem", str(exc))
            return

        janela = tk.Toplevel(self)
        janela.title(f"{titulo} — {os.path.basename(caminho)}")
        janela.configure(bg="#0B0F14")

        # Redimensiona para caber confortavelmente na tela do usuário,
        # sem distorcer a imagem e sem ficar maior que a original.
        largura_max = int(self.winfo_screenwidth() * 0.85)
        altura_max = int(self.winfo_screenheight() * 0.85)

        img_ampliada = img_original.copy()
        img_ampliada.thumbnail((largura_max, altura_max - 60))  # reserva espaço p/ barra de título/rodapé

        foto_grande = ImageTk.PhotoImage(img_ampliada)
        # guarda a referência na própria janela para não ser descartada pelo garbage collector
        janela.imagem_referencia = foto_grande

        tk.Label(janela, text=titulo, bg="#0B0F14", fg="#E4E9EF",
                 font=("Segoe UI", 11, "bold")).pack(pady=(10, 4))

        tk.Label(janela, image=foto_grande, bg="#0B0F14").pack(padx=12, pady=(0, 6))

        largura_original, altura_original = img_original.size
        tk.Label(
            janela,
            text=f"Resolução original: {largura_original}x{altura_original}  ·  {caminho}",
            bg="#0B0F14", fg="#7C8798", font=("Consolas", 8),
        ).pack(pady=(0, 8))

        tk.Button(janela, text="Fechar", command=janela.destroy,
                  bg="#232B35", fg="#E4E9EF", activebackground="#2E3846",
                  relief="flat", padx=16, pady=4).pack(pady=(0, 12))

        janela.bind("<Escape>", lambda _e: janela.destroy())
        janela.transient(self)
        janela.grab_set()
        janela.focus_set()


def main():
    logging.basicConfig(level=logging.INFO,
                         format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
    alert_store.inicializar_banco()
    app = PainelAdmin()
    app.mainloop()


if __name__ == "__main__":
    main()
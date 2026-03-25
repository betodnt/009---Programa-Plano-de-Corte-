import os
import sys
import threading
import time
import tkinter as tk
import tkinter.font as tkfont
import xml.etree.ElementTree as ET
from datetime import datetime
from tkinter import ttk
from typing import Any, cast

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import ConfigManager
from core.locks import LocksManager

WARNING_THRESHOLD = 3600
REFRESH_INTERVAL_MS = 5000

BG_DARK = "#2b2b2b"
BG_CARD = "#3c3f41"
BG_HEADER = "#3c3f41"
FG_WHITE = "#ffffff"
FG_DIM = "#e0e0e0"
ACCENT = "#4a90e2"
GREEN = "#27ae60"
RED = "#c0392b"
ORANGE = "#f39c12"


class MonitorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Monitor de Operacoes em Tempo Real")
        self.geometry("820x500")
        self.minsize(600, 350)
        try:
            self.state("zoomed")
        except Exception:
            pass
        self.configure(bg=BG_DARK)

        today = datetime.now().strftime("%d/%m/%Y")
        self.entry_date_var = tk.StringVar(value=today)
        self.view_date = today
        self._last_xml_mtime = 0
        self._cached_history_items = []
        self._is_loading = False
        self._destroyed = False
        self._setup_styles()
        self._build_ui()
        self._load_icon()

        self.bind("<Configure>", self._on_resize)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._schedule_refresh()

    def _on_close(self):
        self._destroyed = True
        self.destroy()

    def _on_resize(self, event=None):
        if not hasattr(self, "tree") or not self.tree.winfo_ismapped():
            return
        self._adjust_tree_columns()

    def _adjust_tree_columns(self):
        try:
            total = self.tree.winfo_width()
            if total <= 100:
                return

            ratios = {
                "operador": 0.22,
                "maquina": 0.15,
                "pedido": 0.12,
                "plano": 0.34,
                "duracao": 0.10,
                "conclusao": 0.07,
            }

            if not hasattr(self, "_last_column_calc") or abs(total - self._last_column_calc) > 50:
                self._last_column_calc = total
                tkfont.Font(font=("Segoe UI", 11))
                for col, ratio in ratios.items():
                    header = self.tree.heading(col, "text")
                    min_width = max(60, len(str(header)) * 8)
                    width = max(min_width, int(total * ratio))
                    self.tree.column(col, width=width, stretch=True)
            else:
                for col, ratio in ratios.items():
                    self.tree.column(col, width=int(total * ratio), stretch=True)
        except Exception:
            pass

    def _load_icon(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ico_path = os.path.join(base_dir, "icon.ico")
        png_path = os.path.join(base_dir, "icon.png")
        try:
            if os.path.exists(ico_path):
                self.iconbitmap(ico_path)
            elif os.path.exists(png_path):
                img = tk.PhotoImage(file=png_path)
                self.iconphoto(True, img)
        except Exception:
            pass

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TFrame", background=BG_DARK)
        style.configure("Card.TFrame", background=BG_CARD, borderwidth=1, relief="flat")
        style.configure("Header.TFrame", background=BG_HEADER)
        style.configure("TLabel", background=BG_DARK, foreground=FG_DIM, font=("Segoe UI", 11))
        style.configure("Header.TLabel", background=BG_HEADER, foreground=FG_DIM, font=("Segoe UI", 13, "bold"))
        style.configure("Dim.TLabel", background=BG_DARK, foreground=FG_DIM, font=("Segoe UI", 10))
        style.configure("Status.TLabel", background=BG_DARK, foreground=FG_DIM, font=("Segoe UI", 10))
        style.configure(
            "Treeview",
            background=BG_DARK,
            foreground=FG_WHITE,
            fieldbackground=BG_DARK,
            borderwidth=0,
            rowheight=30,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Treeview.Heading",
            background=BG_CARD,
            foreground=FG_WHITE,
            relief="flat",
            font=("Segoe UI", 11, "bold"),
        )
        style.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", "#ffffff")])

        style.element_create("My.Vertical.Scrollbar.trough", "from", "default")
        style.element_create("My.Vertical.Scrollbar.thumb", "from", "default")
        style.layout(
            "My.Vertical.TScrollbar",
            cast(
                Any,
                [
                    (
                        "My.Vertical.Scrollbar.trough",
                        {
                            "children": [("My.Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})],
                            "sticky": "ns",
                        },
                    )
                ],
            ),
        )
        style.configure("My.Vertical.TScrollbar", background="#444444", troughcolor=BG_DARK, borderwidth=0, arrowsize=0, width=8)
        style.map("My.Vertical.TScrollbar", background=[("active", "#555555"), ("pressed", "#666666")])

    def _build_ui(self):
        header = ttk.Frame(self, style="Header.TFrame", padding=(20, 12))
        header.pack(fill="x")
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=0)
        header.columnconfigure(2, weight=1)

        ttk.Label(header, text="MONITOR DE OPERACOES", style="Header.TLabel").grid(row=0, column=0, sticky="w")

        frame_search = ttk.Frame(header, style="Header.TFrame")
        frame_search.grid(row=0, column=1, sticky="ew")
        ttk.Label(frame_search, text="Data:", style="Header.TLabel", font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        ttk.Entry(frame_search, textvariable=self.entry_date_var, width=12, font=("Segoe UI", 10)).pack(side="left")
        ttk.Button(frame_search, text="Buscar", command=self._on_search_click, width=8).pack(side="left", padx=(5, 0))

        frame_status = ttk.Frame(header, style="Header.TFrame")
        frame_status.grid(row=0, column=2, sticky="e")
        self.lbl_count = ttk.Label(frame_status, text="0 em operacao", background=BG_HEADER, foreground=ORANGE, font=("Segoe UI", 11, "bold"))
        self.lbl_count.pack(side="left", padx=(0, 20))
        self.lbl_status = ttk.Label(frame_status, text="", style="Header.TLabel", background=BG_HEADER, foreground=FG_DIM, font=("Segoe UI", 9))
        self.lbl_status.pack(side="left")

        body = ttk.Frame(self, style="Card.TFrame", padding=(12, 12))
        body.pack(fill="both", expand=True, padx=12, pady=(8, 10))
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)

        cols = ("operador", "maquina", "pedido", "plano", "duracao", "conclusao")
        self.tree = ttk.Treeview(body, columns=cols, show="headings")
        self.tree.heading("operador", text="OPERADOR")
        self.tree.heading("maquina", text="MAQUINA")
        self.tree.heading("pedido", text="PEDIDO")
        self.tree.heading("plano", text="PLANO (SAIDA CNC)")
        self.tree.heading("duracao", text="DURACAO")
        self.tree.heading("conclusao", text="CONCLUSAO")

        self.tree.column("operador", width=160, anchor="w", stretch=True)
        self.tree.column("maquina", width=130, anchor="center", stretch=True)
        self.tree.column("pedido", width=100, anchor="center", stretch=True)
        self.tree.column("plano", width=220, anchor="w", stretch=True)
        self.tree.column("duracao", width=90, anchor="center", stretch=True)
        self.tree.column("conclusao", width=90, anchor="center", stretch=True)

        self.tree.tag_configure("active", foreground=GREEN)
        self.tree.tag_configure("history", foreground=FG_WHITE)
        self.tree.tag_configure("delayed", foreground=RED)

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.after(100, self._adjust_tree_columns)

        sb = ttk.Scrollbar(body, orient=tk.VERTICAL, command=self.tree.yview, style="My.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")

        footer = ttk.Frame(self, style="Card.TFrame", padding=(14, 6))
        footer.pack(fill="x", padx=12, pady=(0, 8))
        ttk.Label(
            footer,
            text=f"Atualiza a cada 5 segundos  |  Arquivo: {ConfigManager.get_locks_file_path()}",
            style="Dim.TLabel",
        ).pack(side="left")

    def _on_search_click(self):
        self.view_date = self.entry_date_var.get().strip()
        self._last_xml_mtime = 0
        self._cached_history_items = []
        self._refresh()

    def _schedule_refresh(self):
        if self._destroyed:
            return
        self._refresh()
        self.after(REFRESH_INTERVAL_MS, self._schedule_refresh)

    def _refresh(self):
        if self._is_loading:
            return
        self._is_loading = True
        threading.Thread(target=self._load_data_thread, daemon=True).start()

    def _load_data_thread(self):
        payload = {
            "active_items": [],
            "history_items": [],
            "history_total": 0,
            "count": 0,
            "status_text": time.strftime("atualizado %H:%M:%S"),
            "status_color": FG_DIM,
        }
        try:
            today_str = datetime.now().strftime("%d/%m/%Y")
            locks = LocksManager.get_active_locks() if self.view_date == today_str else {}
            now = time.time()

            active_items = []
            for key, data in sorted(locks.items(), key=lambda item: item[1].get("timestamp", 0)):
                operador = data.get("operador") or "-"
                maquina = data.get("maquina") or "-"
                pedido = data.get("pedido") or "-"
                plano = data.get("saida") or "-"
                elapsed = int(now - data.get("timestamp", now))
                duracao = self._fmt_duration(elapsed)
                tags = ("delayed",) if elapsed > WARNING_THRESHOLD else ("active",)
                payload["active_items"].append(
                    {
                        "iid": key,
                        "values": (operador, maquina, pedido, plano, duracao, ""),
                        "tags": tags,
                    }
                )
                active_items.append(key)

            xml_path = ConfigManager.get_k8_data_path(self.view_date)
            history_items = []
            if os.path.exists(xml_path):
                try:
                    current_mtime = os.stat(xml_path).st_mtime
                    if current_mtime != self._last_xml_mtime or not self._cached_history_items:
                        tree = ET.parse(xml_path)
                        root = tree.getroot()
                        temp_items = []
                        for entrada in root.findall("Entrada"):
                            if entrada.find("DataHoraTermino") is None:
                                continue
                            operador = entrada.findtext("Operador", "-")
                            maquina = entrada.findtext("Maquina", "-")
                            pedido = entrada.findtext("Pedido", "-")
                            plano = entrada.findtext("Saida", "-")
                            duracao = entrada.findtext("TempoDecorrido", "-")
                            dt_term = entrada.findtext("DataHoraTermino", "")
                            hora_conclusao = dt_term.split(" ")[1] if " " in dt_term else dt_term
                            temp_items.append((operador, maquina, pedido, plano, duracao, hora_conclusao))
                        self._cached_history_items = temp_items[::-1]
                        self._last_xml_mtime = current_mtime
                    history_items = self._cached_history_items
                except Exception:
                    payload["status_text"] = "falha ao ler historico XML"
                    payload["status_color"] = RED
            else:
                self._cached_history_items = []
                self._last_xml_mtime = 0

            payload["history_items"] = history_items[:100]
            payload["history_total"] = len(history_items)
            payload["count"] = len(active_items)
        finally:
            self._is_loading = False
            if not self._destroyed:
                self.after(0, lambda: self._apply_loaded_data(payload))

    def _apply_loaded_data(self, payload):
        if self._destroyed or not hasattr(self, "tree"):
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        for item in payload["active_items"]:
            self.tree.insert("", "end", iid=item["iid"], values=item["values"], tags=item["tags"])

        for item in payload["history_items"]:
            self.tree.insert("", "end", values=item, tags=("history",))

        count = payload["count"]
        self.lbl_count.config(
            text=f"{count} ativos | {payload['history_total']} finalizados",
            foreground=GREEN if count > 0 else FG_DIM,
        )
        self.lbl_status.config(text=payload["status_text"], foreground=payload["status_color"])
        self.after(1, self._adjust_tree_columns)

    @staticmethod
    def _fmt_duration(seconds):
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"


if __name__ == "__main__":
    app = MonitorApp()
    app.mainloop()

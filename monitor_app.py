import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import threading
from typing import cast, Any
import time
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from core.config import ConfigManager

LOCK_TIMEOUT = 14400  # Aumentado para 4h (permite ver atrasos > 1h antes de expirar)
WARNING_THRESHOLD = 3600  # Destacar em vermelho após 1h (3600 segundos)
REFRESH_INTERVAL_MS = 5000  # Aumentado de 2000 para 5000ms para reduzir carga

BG_DARK   = "#2b2b2b"
BG_CARD   = "#3c3f41"
BG_HEADER = "#3c3f41"
FG_WHITE  = "#ffffff"
FG_DIM    = "#e0e0e0"
ACCENT    = "#4a90e2"
GREEN     = "#27ae60"
RED       = "#c0392b"
ORANGE    = "#f39c12"

def load_active_locks():
    locks_file = ConfigManager.get_locks_file_path()
    if not os.path.exists(locks_file):
        return {}
    try:
        with open(locks_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        now = time.time()
        valid = {}
        stale = []
        for k, v in data.items():
            if now - v.get("timestamp", 0) > LOCK_TIMEOUT:
                stale.append(k)
                continue
            # NOTA: Não verificamos PID aqui pois estamos em rede.
            # O PID 1234 da Maquina 1 não existe no PC do Monitor, ou é outro processo.
            valid[k] = v
            
        if stale:
            # O Monitor apenas lê, deixa a limpeza para as máquinas ativas para evitar conflito de escrita
            pass
        return valid
    except Exception:
        return {}


class MonitorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Monitor de Operacoes em Tempo Real")
        self.geometry("820x500")
        self.minsize(600, 350)
        # iniciar maximizado para aproveitar o espaço e responsividade
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
        self._is_loading = False  # Flag para evitar thread explosion
        self._setup_styles()
        self._build_ui()
        self._load_icon()

        # Responsividade: ajusta colunas do treeview ao redimensionar
        self.bind("<Configure>", self._on_resize)

        self._schedule_refresh()

    def _on_resize(self, event=None):
        # Pode ser invocado antes dos widgets estarem prontos
        if not hasattr(self, 'tree') or not self.tree.winfo_ismapped():
            return
        self._adjust_tree_columns()

    def _adjust_tree_columns(self):
        try:
            total = self.tree.winfo_width()
            if total <= 100:
                return

            # Otimização: só recalcular min_width se o conteúdo mudou significativamente
            if not hasattr(self, '_last_column_calc') or abs(total - self._last_column_calc) > 50:
                self._last_column_calc = total
                font = tkfont.Font(font=("Segoe UI", 11))

                # Proporções de coluna (soma = 1.0)
                ratios = {
                    'operador': 0.22,
                    'maquina': 0.15,
                    'pedido': 0.12,
                    'plano': 0.34,
                    'duracao': 0.10,
                    'conclusao': 0.07,
                }

                for col, ratio in ratios.items():
                    # Largura mínima simplificada (sem medir cada célula)
                    header = self.tree.heading(col, "text")
                    min_width = max(60, len(str(header)) * 8)  # Estimativa simples baseada no comprimento

                    width = max(min_width, int(total * ratio))
                    self.tree.column(col, width=width, stretch=True)
            else:
                # Apenas ajustar proporções sem recalcular min_width
                ratios = {
                    'operador': 0.22,
                    'maquina': 0.15,
                    'pedido': 0.12,
                    'plano': 0.34,
                    'duracao': 0.10,
                    'conclusao': 0.07,
                }
                for col, ratio in ratios.items():
                    width = int(total * ratio)
                    self.tree.column(col, width=width, stretch=True)
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
        bg_dark      = "#2b2b2b"
        bg_field     = "#3c3f41"
        fg_white     = "#ffffff"
        accent_blue  = "#4a90e2"
        accent_green = "#27ae60"
        accent_red   = "#c0392b"

        self.configure(bg=bg_dark)
        style.theme_use("clam")

        style.configure("TFrame", background=bg_dark)
        style.configure("Card.TFrame", background=BG_CARD, borderwidth=1, relief="flat")
        style.configure("Header.TFrame", background=BG_HEADER)

        style.configure("TLabel", background=bg_dark, foreground="#e0e0e0", font=("Segoe UI", 11))
        style.configure("Header.TLabel", background=BG_HEADER, foreground="#e0e0e0", font=("Segoe UI", 13, "bold"))
        style.configure("Dim.TLabel", background=bg_dark, foreground=FG_DIM, font=("Segoe UI", 10))
        style.configure("Status.TLabel", background=bg_dark, foreground=FG_DIM, font=("Segoe UI", 10))

        style.configure("Treeview",
            background=bg_dark,
            foreground=fg_white,
            fieldbackground=bg_dark,
            borderwidth=0,
            rowheight=30,  # Reduzido de 34 para 30 para economizar espaço
            font=("Segoe UI", 10)  # Reduzido de 11 para 10
        )
        style.configure("Treeview.Heading",
            background=bg_field,
            foreground=fg_white,
            relief="flat",
            font=("Segoe UI", 11, "bold")
        )
        style.map("Treeview",
            background=[("selected", accent_blue)],
            foreground=[("selected", "#ffffff")]
        )

        style.element_create("My.Vertical.Scrollbar.trough", "from", "default")
        style.element_create("My.Vertical.Scrollbar.thumb", "from", "default")
        style.layout("My.Vertical.TScrollbar", cast(Any, [  # type: ignore[arg-type]
            ("My.Vertical.Scrollbar.trough", {
                "children": [("My.Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})],  # cspell: ignore nswe
                "sticky": "ns"
            })
        ]))
        style.configure("My.Vertical.TScrollbar",
            background="#444444", troughcolor=bg_dark, borderwidth=0, arrowsize=0, width=8)
        style.map("My.Vertical.TScrollbar",
            background=[("active", "#555555"), ("pressed", "#666666")])

    def _build_ui(self):
        header = ttk.Frame(self, style="Header.TFrame", padding=(20, 12))
        header.pack(fill="x")

        # Usar grid para alinhar os 3 blocos principais: Título, Busca, Status
        header.columnconfigure(0, weight=1) # Espaço à esquerda do centro
        header.columnconfigure(1, weight=0) # Conteúdo central (Busca)
        header.columnconfigure(2, weight=1) # Espaço à direita do centro

        # Título (canto esquerdo)
        ttk.Label(header, text="MONITOR DE OPERACOES", style="Header.TLabel").grid(row=0, column=0, sticky="w")

        # Área de Filtro de Data (centralizado)
        frame_search = ttk.Frame(header, style="Header.TFrame")
        frame_search.grid(row=0, column=1, sticky="ew")

        ttk.Label(frame_search, text="Data:", style="Header.TLabel", font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        
        ent_date = ttk.Entry(frame_search, textvariable=self.entry_date_var, width=12, font=("Segoe UI", 10))
        ent_date.pack(side="left")
        
        btn_search = ttk.Button(frame_search, text="Buscar", command=self._on_search_click, width=8)
        btn_search.pack(side="left", padx=(5, 0))

        # Status (canto direito)
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
        self.tree.heading("maquina",  text="MAQUINA")
        self.tree.heading("pedido",   text="PEDIDO")
        self.tree.heading("plano",    text="PLANO (SAIDA CNC)")
        self.tree.heading("duracao",  text="DURACAO")
        self.tree.heading("conclusao", text="CONCLUSAO")

        self.tree.column("operador", width=160, anchor="w", stretch=True)
        self.tree.column("maquina",  width=130, anchor="center", stretch=True)
        self.tree.column("pedido",   width=100, anchor="center", stretch=True)
        self.tree.column("plano",    width=220, anchor="w", stretch=True)
        self.tree.column("duracao",  width=90,  anchor="center", stretch=True)
        self.tree.column("conclusao", width=90, anchor="center", stretch=True)

        self.tree.tag_configure("active", foreground=GREEN)
        self.tree.tag_configure("idle",   foreground=FG_DIM)
        self.tree.tag_configure("history", foreground=FG_WHITE)
        self.tree.tag_configure("delayed", foreground=RED)

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.after(100, self._adjust_tree_columns)

        sb = ttk.Scrollbar(body, orient=tk.VERTICAL, command=self.tree.yview,
                           style="My.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")

        footer = ttk.Frame(self, style="Card.TFrame", padding=(14, 6))
        footer.pack(fill="x", padx=12, pady=(0, 8))
        ttk.Label(footer, text=f"Atualiza a cada 5 segundos  |  Arquivo: {ConfigManager.get_locks_file_path()}",
                  style="Dim.TLabel").pack(side="left")

    def _on_search_click(self):
        # Atualiza a data de visualização e força o refresh
        self.view_date = self.entry_date_var.get().strip()
        self._last_xml_mtime = 0 # Força recarga do histórico
        self._cached_history_items = []
        self._refresh()

    def _schedule_refresh(self):
        self._refresh()
        self.after(REFRESH_INTERVAL_MS, self._schedule_refresh)

    def _refresh(self):
        # Se já estiver carregando (ex: rede lenta), não inicia outra thread
        if self._is_loading:
            return
            
        # Executa I/O em thread separada
        self._is_loading = True
        threading.Thread(target=self._load_data_thread, daemon=True).start()

    def _load_data_thread(self):
        try:
            # 1. Carrega Locks Ativos
            active_items = []
            today_str = datetime.now().strftime("%d/%m/%Y")
            
            # Se a data visualizada for hoje, carregamos os locks ativos
            if self.view_date == today_str:
                locks = load_active_locks()
            else:
                locks = {}

            # Coleta dados para atualizar na Main Thread (TKinter não é thread-safe)
            # Mas treeview.delete/insert muitas vezes funciona, porém o correto é usar after ou filas
            # Aqui manteremos a lógica atual mas protegida pelo try/finally
            
            # Limpa a árvore para redesenhar
            for item in self.tree.get_children():
                self.tree.delete(item)

            now = time.time()
            
            # Exibe Itens Ativos (Locks)
            for key, data in sorted(locks.items(), key=lambda x: x[1].get("timestamp", 0)):
                operador = data.get("operador") or "—"
                maquina  = data.get("maquina")  or "—"
                pedido   = data.get("pedido")   or "—"
                plano    = data.get("saida")    or "—"
                elapsed  = int(now - data.get("timestamp", now))
                duracao  = self._fmt_duration(elapsed)
                
                # Verifica se ultrapassou o limite de alerta
                tags = ("active",)
                if elapsed > WARNING_THRESHOLD:
                    tags = ("delayed",)
                    
                self.tree.insert("", "end", iid=key,
                                values=(operador, maquina, pedido, plano, duracao, ""),
                                tags=tags)
                active_items.append(key)

            # 2. Carrega Histórico (XML) usando ConfigManager
            xml_path = ConfigManager.get_k8_data_path(self.view_date)
            history_items = []
            
            if os.path.exists(xml_path):
                try:
                    current_mtime = os.stat(xml_path).st_mtime
                    # Só reprocessa o XML se o arquivo mudou ou se mudamos a data de visualização
                    if current_mtime != self._last_xml_mtime or not self._cached_history_items:
                        tree = ET.parse(xml_path)
                        root = tree.getroot()
                        temp_items = []
                        # Coleta todos para inverter a ordem (mais recentes no topo do histórico)
                        for entrada in root.findall("Entrada"):
                            if entrada.find("DataHoraTermino") is not None:
                                operador = entrada.findtext("Operador", "—")
                                maquina = entrada.findtext("Maquina", "—")
                                pedido = entrada.findtext("Pedido", "—")
                                plano = entrada.findtext("Saida", "—")
                                duracao = entrada.findtext("TempoDecorrido", "—")
                                dt_term = entrada.findtext("DataHoraTermino", "")
                                hora_conclusao = dt_term.split(' ')[1] if ' ' in dt_term else dt_term
                                temp_items.append((operador, maquina, pedido, plano, duracao, hora_conclusao))
                        
                        # Inverte para mostrar os últimos finalizados primeiro
                        self._cached_history_items = temp_items[::-1]
                        self._last_xml_mtime = current_mtime
                    
                    history_items = self._cached_history_items
                except Exception:
                    pass
            else:
                self._cached_history_items = []
                self._last_xml_mtime = 0

            # Renderiza Histórico (limite de 100 para não travar a UI)
            count_history = 0
            for item in history_items:
                if count_history >= 100: break
                self.tree.insert("", "end", values=item, tags=("history",))
                count_history += 1

            count = len(active_items)
            self.lbl_count.config(
                text=f"{count} ativos | {len(history_items)} finalizados",
                foreground=GREEN if count > 0 else FG_DIM
            )
            self.lbl_status.config(text=time.strftime("atualizado %H:%M:%S"))

            # Garantir ajuste final após atualização de dados
            self.after(1, self._adjust_tree_columns)
            
        finally:
            self._is_loading = False

    def _update_durations(self, locks):
        now = time.time()
        for key, data in locks.items():
            try:
                elapsed = int(now - data.get("timestamp", now))
                duracao = self._fmt_duration(elapsed)
                vals = list(self.tree.item(key, "values"))
                if len(vals) >= 5 and vals[4] != duracao:
                    vals[4] = duracao
                    self.tree.item(key, values=vals)
            except Exception:
                pass
        self.lbl_status.config(text=time.strftime("atualizado %H:%M:%S"))

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

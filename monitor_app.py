import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk
from typing import cast, Any
import time
import json
import xml.etree.ElementTree as ET
from datetime import datetime

def _get_locks_file():
    try:
        from core.config import ConfigManager
        return ConfigManager.get_locks_file_path()
    except Exception:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "active_locks.json")

def _get_xml_path_for_date(date_str):
    # Converte o formato de exibição (DD/MM/YYYY) para o formato de arquivo (YYYY-MM-DD)
    file_date_str = date_str
    try:
        dt = datetime.strptime(date_str, "%d/%m/%Y")
        file_date_str = dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    try:
        from core.config import ConfigManager
        # Tenta obter o caminho configurado. O ConfigManager._get_path é protegido, então acessamos via método público se possível ou recriamos a lógica parcial
        # Como get_k8_data_path usa datetime.now(), precisamos acessar a config bruta ou simular
        config_val = ConfigManager._get_path('DadosXml', '')
        if config_val and '{date}' in config_val:
            return config_val.replace('{date}', file_date_str)
        if not config_val or config_val.endswith('dados.xml'):
            # Caminho padrão ajustado para a data solicitada
            return ConfigManager._resolve_path(f'./public/dados/dados_{file_date_str}.xml')
        return config_val
    except Exception:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "public", "dados", f"dados_{file_date_str}.xml")

LOCK_TIMEOUT = 3600
REFRESH_INTERVAL_MS = 2000

BG_DARK   = "#1e1e2e"
BG_CARD   = "#2b2b3b"
BG_HEADER = "#12121f"
FG_WHITE  = "#e0e0e0"
FG_DIM    = "#888899"
ACCENT    = "#4a90e2"
GREEN     = "#27ae60"
RED       = "#c0392b"
ORANGE    = "#e67e22"


def _pid_alive(pid):
    try:
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, 0, int(pid))
        if not handle:
            return False
        code = ctypes.c_ulong(0)
        ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(handle)
        return code.value == STILL_ACTIVE
    except Exception:
        return True


def load_active_locks():
    locks_file = _get_locks_file()
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
            # Removed PID check for speed
            # pid = v.get("pid")
            # if pid and not _pid_alive(int(pid)):
            #     stale.append(k)
            #     continue
            valid[k] = v
        if stale:
            try:
                with open(locks_file, "w", encoding="utf-8") as f:
                    json.dump(valid, f, ensure_ascii=False, indent=2)
            except Exception:
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
        self.configure(bg=BG_DARK)

        today = datetime.now().strftime("%d/%m/%Y")
        self.entry_date_var = tk.StringVar(value=today)
        self.view_date = today
        self._last_locks = None
        self._setup_styles()
        self._build_ui()
        self._load_icon()
        self._schedule_refresh()

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
        style.configure("Card.TFrame", background=BG_CARD)
        style.configure("Header.TFrame", background=BG_HEADER)

        style.configure("TLabel", background=BG_DARK, foreground=FG_WHITE, font=("Segoe UI", 11))
        style.configure("Header.TLabel", background=BG_HEADER, foreground=FG_WHITE, font=("Segoe UI", 13, "bold"))
        style.configure("Dim.TLabel", background=BG_DARK, foreground=FG_DIM, font=("Segoe UI", 9))
        style.configure("Status.TLabel", background=BG_DARK, foreground=FG_DIM, font=("Segoe UI", 9))

        style.configure("Treeview",
            background=BG_CARD,
            foreground=FG_WHITE,
            fieldbackground=BG_CARD,
            borderwidth=0,
            rowheight=36,
            font=("Segoe UI", 11)
        )
        style.configure("Treeview.Heading",
            background=BG_HEADER,
            foreground=FG_WHITE,
            relief="flat",
            font=("Segoe UI", 10, "bold")
        )
        style.map("Treeview",
            background=[("selected", ACCENT)],
            foreground=[("selected", "#ffffff")]
        )

        style.element_create("Mon.Vertical.Scrollbar.trough", "from", "default")
        style.element_create("Mon.Vertical.Scrollbar.thumb", "from", "default")
        style.layout("Mon.Vertical.TScrollbar", cast(Any, [  # type: ignore[arg-type]
            ("Mon.Vertical.Scrollbar.trough", {
                "children": [("Mon.Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})],  # cspell: ignore nswe
                "sticky": "ns"
            })
        ]))
        style.configure("Mon.Vertical.TScrollbar",
            background="#444455", troughcolor=BG_DARK, borderwidth=0, arrowsize=0, width=8)
        style.map("Mon.Vertical.TScrollbar",
            background=[("active", "#555566"), ("pressed", "#666677")])

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

        body = ttk.Frame(self, padding=(16, 12))
        body.pack(fill="both", expand=True)
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
        self.tree.column("maquina",  width=130, anchor="center", stretch=False)
        self.tree.column("pedido",   width=100, anchor="center", stretch=False)
        self.tree.column("plano",    width=220, anchor="w", stretch=True)
        self.tree.column("duracao",  width=90,  anchor="center", stretch=False)
        self.tree.column("conclusao", width=90, anchor="center", stretch=False)

        self.tree.tag_configure("active", foreground=GREEN)
        self.tree.tag_configure("idle",   foreground=FG_DIM)
        self.tree.tag_configure("history", foreground=FG_WHITE)

        self.tree.grid(row=0, column=0, sticky="nsew")

        sb = ttk.Scrollbar(body, orient=tk.VERTICAL, command=self.tree.yview,
                           style="Mon.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")

        footer = ttk.Frame(self, padding=(16, 6))
        footer.pack(fill="x")
        ttk.Label(footer, text=f"Atualiza a cada 2 segundos  |  Arquivo: {_get_locks_file()}",
                  style="Dim.TLabel").pack(side="left")

    def _on_search_click(self):
        # Atualiza a data de visualização e força o refresh
        self.view_date = self.entry_date_var.get().strip()
        self._last_locks = None # Força redesenho
        self._refresh()

    def _schedule_refresh(self):
        self._refresh()
        self.after(REFRESH_INTERVAL_MS, self._schedule_refresh)

    def _refresh(self):
        # 1. Carrega Locks Ativos (apenas se estiver vendo o dia de hoje)
        active_items = []
        today_str = datetime.now().strftime("%d/%m/%Y")
        
        # Se a data visualizada for hoje, carregamos os locks ativos
        if self.view_date == today_str:
            locks = load_active_locks()
        else:
            locks = {}

        # Se nada mudou nos locks e estamos no modo "hoje", apenas atualizamos durações dos ativos
        # Mas como temos histórico misturado, precisamos verificar se vale a pena redesenhar tudo
        # Para simplificar, se houver locks, atualizamos as durações visualmente, mas se o xml mudou, teríamos que recarregar.
        # Vamos redesenhar sempre que houver mudança ou a cada ciclo para garantir que o XML novo apareça
        
        # Para evitar flicker excessivo, podemos checar mtime do XML, mas vamos simplificar redesenhando lista
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
            self.tree.insert("", "end", iid=key,
                             values=(operador, maquina, pedido, plano, duracao, ""),
                             tags=("active",))
            active_items.append(key)

        # 2. Carrega Histórico do XML da data selecionada
        xml_path = _get_xml_path_for_date(self.view_date)
        history_count = 0
        if os.path.exists(xml_path):
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()
                # Itera sobre as entradas finalizadas
                for entrada in root.findall("Entrada"):
                    # Filtra apenas se tiver DataHoraTermino (finalizado)
                    if entrada.find("DataHoraTermino") is not None:
                        operador = entrada.findtext("Operador", "—")
                        maquina = entrada.findtext("Maquina", "—")
                        pedido = entrada.findtext("Pedido", "—")
                        plano = entrada.findtext("Saida", "—")
                        duracao = entrada.findtext("TempoDecorrido", "—")
                        dt_term = entrada.findtext("DataHoraTermino", "")
                        hora_conclusao = dt_term.split(' ')[1] if ' ' in dt_term else dt_term
                        
                        # Inserir na treeview com tag history
                        self.tree.insert("", "end", 
                                         values=(operador, maquina, pedido, plano, duracao, hora_conclusao),
                                         tags=("history",))
                        history_count += 1
            except Exception:
                pass

        count = len(active_items)
        self.lbl_count.config(
            text=f"{count} ativos | {history_count} finalizados",
            foreground=GREEN if count > 0 else FG_DIM
        )
        self.lbl_status.config(text=time.strftime("atualizado %H:%M:%S"))

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

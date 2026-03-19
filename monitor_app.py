import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk
from typing import cast, Any
import time
import json

LOCKS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "active_locks.json")
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
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def load_active_locks():
    if not os.path.exists(LOCKS_FILE):
        return {}
    try:
        with open(LOCKS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        now = time.time()
        valid = {}
        stale = []
        for k, v in data.items():
            if now - v.get("timestamp", 0) > LOCK_TIMEOUT:
                stale.append(k)
                continue
            pid = v.get("pid")
            if pid and not _pid_alive(int(pid)):
                stale.append(k)
                continue
            valid[k] = v
        if stale:
            try:
                with open(LOCKS_FILE, "w", encoding="utf-8") as f:
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

        ttk.Label(header, text="MONITOR DE OPERACOES", style="Header.TLabel").pack(side="left")

        self.lbl_status = ttk.Label(header, text="", style="Header.TLabel",
                                    background=BG_HEADER, foreground=FG_DIM,
                                    font=("Segoe UI", 9))
        self.lbl_status.pack(side="right", padx=(0, 4))

        self.lbl_count = ttk.Label(header, text="0 em operacao",
                                   background=BG_HEADER, foreground=ORANGE,
                                   font=("Segoe UI", 11, "bold"))
        self.lbl_count.pack(side="right", padx=(0, 20))

        body = ttk.Frame(self, padding=(16, 12))
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)

        cols = ("operador", "maquina", "pedido", "plano", "duracao")
        self.tree = ttk.Treeview(body, columns=cols, show="headings")

        self.tree.heading("operador", text="OPERADOR")
        self.tree.heading("maquina",  text="MAQUINA")
        self.tree.heading("pedido",   text="PEDIDO")
        self.tree.heading("plano",    text="PLANO (SAIDA CNC)")
        self.tree.heading("duracao",  text="DURACAO")

        self.tree.column("operador", width=160, anchor="w", stretch=True)
        self.tree.column("maquina",  width=130, anchor="center", stretch=False)
        self.tree.column("pedido",   width=100, anchor="center", stretch=False)
        self.tree.column("plano",    width=220, anchor="w", stretch=True)
        self.tree.column("duracao",  width=90,  anchor="center", stretch=False)

        self.tree.tag_configure("active", foreground=GREEN)
        self.tree.tag_configure("idle",   foreground=FG_DIM)

        self.tree.grid(row=0, column=0, sticky="nsew")

        sb = ttk.Scrollbar(body, orient=tk.VERTICAL, command=self.tree.yview,
                           style="Mon.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")

        footer = ttk.Frame(self, padding=(16, 6))
        footer.pack(fill="x")
        ttk.Label(footer, text="Atualiza a cada 2 segundos  |  Arquivo: active_locks.json",
                  style="Dim.TLabel").pack(side="left")

    def _schedule_refresh(self):
        self._refresh()
        self.after(REFRESH_INTERVAL_MS, self._schedule_refresh)

    def _refresh(self):
        locks = load_active_locks()

        if locks == self._last_locks:
            self._update_durations(locks)
            return

        self._last_locks = {k: dict(v) for k, v in locks.items()}

        for item in self.tree.get_children():
            self.tree.delete(item)

        now = time.time()
        for key, data in sorted(locks.items(), key=lambda x: x[1].get("timestamp", 0)):
            operador = data.get("operador") or "—"
            maquina  = data.get("maquina")  or "—"
            pedido   = data.get("pedido")   or "—"
            plano    = data.get("saida")    or "—"
            elapsed  = int(now - data.get("timestamp", now))
            duracao  = self._fmt_duration(elapsed)
            self.tree.insert("", "end", iid=key,
                             values=(operador, maquina, pedido, plano, duracao),
                             tags=("active",))

        count = len(locks)
        self.lbl_count.config(
            text=f"{count} em operacao" if count != 1 else "1 em operacao",
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
                if len(vals) == 5 and vals[4] != duracao:
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

import time
from datetime import timedelta
from tkinter import ttk


class ActionPanel(ttk.Frame):
    def __init__(self, master, on_iniciar, on_finalizar, **kwargs):
        super().__init__(master, **kwargs)
        self.on_iniciar = on_iniciar
        self.on_finalizar = on_finalizar
        self.start_time = None
        self.running = False
        self.setup_ui()

    def setup_ui(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=0)

        self.lbl_status = ttk.Label(self, text="Verificando rede...", style="Section.TLabel")
        self.lbl_status.grid(row=0, column=0, sticky="w", padx=(12, 8), pady=(12, 18))

        self.lbl_timer = ttk.Label(self, text="00:00:00", style="Timer.TLabel")
        self.lbl_timer.grid(row=0, column=1, columnspan=2, sticky="e", padx=(8, 12), pady=(12, 18))

        self.btn_iniciar = ttk.Button(
            self,
            text="INICIAR",
            command=self.on_iniciar_click,
            style="Iniciar.Action.TButton",
        )
        self.btn_iniciar.grid(row=1, column=1, sticky="ew", padx=(8, 6), pady=(0, 12))

        self.btn_finalizar = ttk.Button(
            self,
            text="FINALIZAR",
            command=self.on_finalizar_click,
            style="Finalizar.Action.TButton",
        )
        self.btn_finalizar.grid(row=1, column=2, sticky="ew", padx=(6, 12), pady=(0, 12))
        self.btn_finalizar.state(["disabled"])

    def on_iniciar_click(self):
        if self.on_iniciar():
            self.btn_iniciar.state(["disabled"])
            self.btn_finalizar.state(["!disabled"])
            self.start_timer()

    def on_finalizar_click(self):
        self.stop_timer()
        self.on_finalizar()
        self.btn_iniciar.state(["!disabled"])
        self.btn_finalizar.state(["disabled"])

    def start_timer(self):
        if not self.running:
            self.start_time = time.time()
            self.running = True
            self.update_timer()

    def stop_timer(self):
        self.running = False

    def update_timer(self):
        if self.running and self.start_time:
            elapsed = int(time.time() - self.start_time)
            td = timedelta(seconds=elapsed)
            total_seconds = int(td.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            self.lbl_timer.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            self.after(1000, self.update_timer)

    def get_elapsed_time_string(self):
        return self.lbl_timer.cget("text")

    def set_status(self, text, level="info"):
        foreground = {
            "ok": "#7ed957",
            "warning": "#f39c12",
            "error": "#e74c3c",
            "info": "#d8d8d8",
        }.get(level, "#d8d8d8")
        self.lbl_status.config(text=text, foreground=foreground)

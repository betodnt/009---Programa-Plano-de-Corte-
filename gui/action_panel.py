import tkinter as tk
from tkinter import ttk
import time
from datetime import timedelta

class ActionPanel(ttk.Frame):
    def __init__(self, master, on_iniciar, on_finalizar, **kwargs):
        super().__init__(master, **kwargs)
        self.on_iniciar = on_iniciar
        self.on_finalizar = on_finalizar
        
        self.start_time = None
        self.running = False
        
        self.setup_ui()

    def setup_ui(self):
        # Weight 0 for action columns, weight 1 for spacer column (column 0)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=0)
        
        # Timer Display (Right aligned)
        self.lbl_timer = ttk.Label(self, text="00:00:00", style="Timer.TLabel")
        self.lbl_timer.grid(row=0, column=1, columnspan=2, pady=(0, 15), sticky="e")
        
        # Iniciar Button
        self.btn_iniciar = ttk.Button(self, text="INICIAR", command=self.on_iniciar_click, style="Iniciar.Action.TButton")
        self.btn_iniciar.grid(row=1, column=1, padx=5, sticky="ew")
        
        # Finalizar Button
        self.btn_finalizar = ttk.Button(self, text="FINALIZAR", command=self.on_finalizar_click, style="Finalizar.Action.TButton")
        self.btn_finalizar.grid(row=1, column=2, padx=5, sticky="ew")
        self.btn_finalizar.state(['disabled'])

    def on_iniciar_click(self):
        # Delegate logic up, only handle UI here if allowed
        if self.on_iniciar():
            self.btn_iniciar.state(['disabled'])
            self.btn_finalizar.state(['!disabled'])
            self.start_timer()

    def on_finalizar_click(self):
        # Stop timer first
        self.stop_timer()
        # Delegate logic up
        self.on_finalizar()
        
        self.btn_iniciar.state(['!disabled'])
        self.btn_finalizar.state(['disabled'])

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
            # Format to hh:mm:ss safely
            total_seconds = int(td.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            self.lbl_timer.config(text=time_str)
            self.after(1000, self.update_timer)

    def get_elapsed_time_string(self):
        return self.lbl_timer.cget("text")

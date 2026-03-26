import tkinter as tk
from tkinter import ttk

from core.config import ConfigManager
from core.locks import LocksManager


class FormPanel(ttk.Frame):
    def __init__(self, master, on_search_trigger, on_open_pdf, on_open_settings, **kwargs):
        super().__init__(master, **kwargs)
        self.on_search_trigger = on_search_trigger
        self.on_open_pdf = on_open_pdf
        self.on_open_settings = on_open_settings
        self._all_saidas = []
        self.setup_ui()

    def setup_ui(self):
        for col in range(4):
            self.columnconfigure(col, weight=1 if col < 2 else 0)

        machine_name = ConfigManager.get_current_machine()
        self.var_maquina = tk.StringVar(value=machine_name)

        lbl_op = ttk.Label(self, text="OPERADOR", style="Section.TLabel")
        lbl_op.grid(row=0, column=0, sticky="w", padx=(12, 10), pady=(12, 4))
        self.var_operador = tk.StringVar()
        self.cbox_operador = ttk.Combobox(self, textvariable=self.var_operador)
        self.cbox_operador.grid(row=1, column=0, sticky="ew", padx=(12, 10), pady=(0, 16))

        machine_frame = ttk.Frame(self, style="Inline.TFrame")
        machine_frame.grid(row=0, column=1, columnspan=2, rowspan=2, sticky="ew", padx=(10, 10), pady=(12, 16))
        machine_frame.columnconfigure(0, weight=1)

        self.lbl_machine_value = ttk.Label(machine_frame, text=machine_name, style="MachineValue.TLabel")
        self.lbl_machine_value.grid(row=0, column=0, sticky="w")

        self.btn_settings = tk.Button(
            machine_frame,
            text="⚙",
            font=("Segoe UI", 19),
            fg="white",
            bg="#2b2b2b",
            activebackground="#3c3f41",
            activeforeground="white",
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            command=self.on_open_settings,
        )
        self.btn_settings.grid(row=0, column=1, sticky="e", padx=(12, 0))

        lbl_tipo = ttk.Label(self, text="TIPO", style="Section.TLabel")
        lbl_tipo.grid(row=2, column=0, sticky="w", padx=(12, 10), pady=(2, 4))
        self.var_tipo = tk.StringVar(value="Avulso")
        self.cbox_tipo = ttk.Combobox(
            self,
            textvariable=self.var_tipo,
            state="readonly",
            values=["Avulso", "Estoque", "Pedido", "Reforma", "PPD"],
        )
        self.cbox_tipo.grid(row=3, column=0, sticky="ew", padx=(12, 10), pady=(0, 16))
        self.cbox_tipo.bind("<<ComboboxSelected>>", lambda _e: self.on_search_trigger())

        lbl_pedido = ttk.Label(self, text="PEDIDO", style="Section.TLabel")
        lbl_pedido.grid(row=2, column=1, sticky="w", padx=(10, 10), pady=(2, 4))
        self.var_pedido = tk.StringVar()
        self.ent_pedido = ttk.Entry(self, textvariable=self.var_pedido)
        self.ent_pedido.grid(row=3, column=1, columnspan=2, sticky="ew", padx=(10, 10), pady=(0, 16))
        self.ent_pedido.bind("<Return>", lambda _e: self.on_search_trigger())

        lbl_retalho = ttk.Label(self, text="CHAPA / RETALHO", style="Section.TLabel")
        lbl_retalho.grid(row=4, column=0, sticky="w", padx=(12, 10), pady=(2, 4))
        self.var_retalho = tk.StringVar(value="Chapa Inteira")
        self.cbox_retalho = ttk.Combobox(
            self,
            textvariable=self.var_retalho,
            state="readonly",
            values=["Chapa Inteira", "Retalho"],
        )
        self.cbox_retalho.grid(row=5, column=0, sticky="ew", padx=(12, 10), pady=(0, 16))

        lbl_saida = ttk.Label(self, text="SAIDA CNC A CORTAR", style="Section.TLabel")
        lbl_saida.grid(row=4, column=1, columnspan=2, sticky="w", padx=(10, 10), pady=(2, 4))

        saida_frame = ttk.Frame(self, style="Inline.TFrame")
        saida_frame.grid(row=5, column=1, columnspan=2, sticky="ew", padx=(10, 10), pady=(0, 16))
        saida_frame.columnconfigure(0, weight=1)

        self.var_saida = tk.StringVar()
        self.cbox_saida = ttk.Combobox(saida_frame, textvariable=self.var_saida, state="readonly")
        self.cbox_saida.grid(row=0, column=0, sticky="ew")

        self.btn_pdf = ttk.Button(saida_frame, text="PDF", command=self.on_open_pdf, style="Compact.TButton")
        self.btn_pdf.grid(row=0, column=1, padx=(10, 0))

    def update_machine_display(self):
        machine_name = ConfigManager.get_current_machine()
        self.lbl_machine_value.config(text=machine_name)
        self.var_maquina.set(machine_name)

    def update_saidas(self, results):
        self._all_saidas = list(results)
        maquina = self.var_maquina.get()
        locked_saidas = LocksManager.get_locked_saidas(maquina)
        self.apply_locked_saidas_filter(locked_saidas)

    def apply_locked_saidas_filter(self, locked_saidas):
        current_val = self.var_saida.get()
        available_saidas = [s for s in self._all_saidas if s not in locked_saidas]
        self.cbox_saida["values"] = available_saidas

        if available_saidas:
            if current_val in available_saidas:
                self.var_saida.set(current_val)
            else:
                self.cbox_saida.current(0)
            if hasattr(self.master, "action_panel"):
                self.master.action_panel.btn_iniciar.state(["!disabled"])
        else:
            self.var_saida.set("")
            if hasattr(self.master, "action_panel"):
                self.master.action_panel.btn_iniciar.state(["disabled"])

    def update_operators(self, names):
        self.cbox_operador["values"] = names

    def disable_fields(self):
        for widget in (self.cbox_operador, self.cbox_tipo, self.ent_pedido, self.cbox_retalho, self.cbox_saida):
            widget.config(state="disabled")

    def enable_fields(self):
        self.cbox_operador.config(state="normal")
        self.cbox_tipo.config(state="readonly")
        self.ent_pedido.config(state="normal")
        self.cbox_retalho.config(state="readonly")
        self.cbox_saida.config(state="readonly")

    def get_data(self):
        return {
            "operador": self.var_operador.get(),
            "maquina": self.var_maquina.get(),
            "tipo": self.var_tipo.get(),
            "pedido": self.var_pedido.get(),
            "retalho": self.var_retalho.get(),
            "saida": self.var_saida.get(),
        }

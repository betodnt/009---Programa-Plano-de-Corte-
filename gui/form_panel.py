import tkinter as tk
from tkinter import ttk
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
        # Configure grid expansion
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=0)
        self.columnconfigure(3, weight=0)
        
        # Row-based layout for more space
        
        # Operador & Máquina
        lbl_op = ttk.Label(self, text="OPERADOR")
        lbl_op.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 2))
        self.var_operador = tk.StringVar()
        self.cbox_operador = ttk.Combobox(self, textvariable=self.var_operador)
        self.cbox_operador.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 15))

        lbl_maq = ttk.Label(self, text="MÁQUINA")
        lbl_maq.grid(row=0, column=1, sticky="w", padx=10, pady=(10, 2))
        self.var_maquina = tk.StringVar(value="Bodor1 (12K)")
        self.cbox_maquina = ttk.Combobox(self, textvariable=self.var_maquina, state="readonly", values=["Bodor1 (12K)", "Bodor2 (6K)", "Dardi"])
        self.cbox_maquina.grid(row=1, column=1, sticky="ew", padx=10, pady=(0, 15))
        self.cbox_maquina.bind("<<ComboboxSelected>>", self._on_maquina_changed)
        
        # Botão de engrenagem à direita da máquina
        self.btn_settings = tk.Button(self, text="⚙", font=("Segoe UI", 22), fg="white", bg="#2b2b2b",
                                      activebackground="#3c3f41", activeforeground="white",
                                      relief="flat", borderwidth=0, cursor="hand2", command=self.on_open_settings)
        self.btn_settings.grid(row=0, column=2, padx=0, pady=0, sticky="ne")

        # Tipo & Pedido
        lbl_tipo = ttk.Label(self, text="TIPO")
        lbl_tipo.grid(row=2, column=0, sticky="w", padx=10, pady=(10, 2))
        self.var_tipo = tk.StringVar(value="Avulso")
        self.cbox_tipo = ttk.Combobox(self, textvariable=self.var_tipo, state="readonly", values=["Avulso", "Estoque", "Pedido", "Reforma", "PPD"])
        self.cbox_tipo.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 15))
        self.cbox_tipo.bind("<<ComboboxSelected>>", lambda e: self.on_search_trigger())

        lbl_pedido = ttk.Label(self, text="PEDIDO")
        lbl_pedido.grid(row=2, column=1, sticky="w", padx=10, pady=(10, 2))
        self.var_pedido = tk.StringVar()
        self.ent_pedido = ttk.Entry(self, textvariable=self.var_pedido)
        self.ent_pedido.grid(row=3, column=1, sticky="ew", padx=10, pady=(0, 15))
        self.ent_pedido.bind("<FocusOut>", lambda e: self.on_search_trigger())
        self.ent_pedido.bind("<Return>", lambda e: self.on_search_trigger())

        # Chapa/Retalho & Saída CNC
        lbl_retalho = ttk.Label(self, text="CHAPA / RETALHO")
        lbl_retalho.grid(row=4, column=0, sticky="w", padx=10, pady=(10, 2))
        self.var_retalho = tk.StringVar(value="Chapa Inteira")
        self.cbox_retalho = ttk.Combobox(self, textvariable=self.var_retalho, state="readonly", values=["Chapa Inteira", "Retalho"])
        self.cbox_retalho.grid(row=5, column=0, sticky="ew", padx=10, pady=(0, 15))

        # Saída CNC
        lbl_saida = ttk.Label(self, text="SAÍDA CNC A CORTAR")
        lbl_saida.grid(row=4, column=1, sticky="w", padx=10, pady=(10, 2))
        
        frame_saida_controls = ttk.Frame(self)
        frame_saida_controls.grid(row=5, column=1, sticky="ew", padx=10, pady=(0, 15))
        
        self.var_saida = tk.StringVar()
        self.cbox_saida = ttk.Combobox(frame_saida_controls, textvariable=self.var_saida, state="readonly")
        self.cbox_saida.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.btn_pdf = ttk.Button(frame_saida_controls, text="PDF", command=self.on_open_pdf, width=6)
        self.btn_pdf.pack(side="right")

    def update_saidas(self, results):
        """Atualiza lista de saídas, filtrando as que estão bloqueadas"""
        self._all_saidas = list(results)
        
        maquina = self.var_maquina.get()
        locked_saidas = LocksManager.get_locked_saidas(maquina)
        
        available_saidas = [s for s in self._all_saidas if s not in locked_saidas]
        current_selection = self.var_saida.get()
        
        # Só atualiza a lista visual se houver diferença para evitar piscar ou fechar o dropdown aberto
        if list(self.cbox_saida['values']) != available_saidas:
            self.cbox_saida['values'] = available_saidas
            
            # Tenta preservar a seleção atual se ela ainda estiver disponível
            if current_selection and current_selection in available_saidas:
                self.var_saida.set(current_selection)
            elif available_saidas:
                self.cbox_saida.current(0)
            else:
                self.var_saida.set('')

        # Atualiza estado do botão Iniciar
        if hasattr(self.master, 'action_panel'):
            # Se tem saídas e uma está selecionada (ou a primeira foi auto-selecionada)
            if available_saidas and self.var_saida.get():
                if self.master.action_panel.btn_iniciar.state() != ('!disabled',):
                     self.master.action_panel.btn_iniciar.state(['!disabled'])
            else:
                if self.master.action_panel.btn_iniciar.state() != ('disabled',):
                    self.master.action_panel.btn_iniciar.state(['disabled'])

    def update_operators(self, names):
        self.cbox_operador['values'] = names

    def disable_fields(self):
        for w in (self.cbox_operador, self.cbox_maquina, self.cbox_tipo, 
                 self.ent_pedido, self.cbox_retalho, self.cbox_saida):
            w.config(state="disabled")

    def enable_fields(self):
        self.cbox_operador.config(state="normal")
        self.cbox_maquina.config(state="readonly")
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
            "saida": self.var_saida.get()
        }
    
    def _on_maquina_changed(self, event=None):
        """Callback quando máquina é mudada - refaz filtragem de saídas"""
        self.update_saidas(self._all_saidas)

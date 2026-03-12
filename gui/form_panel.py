import tkinter as tk
from tkinter import ttk

class FormPanel(ttk.Frame):
    def __init__(self, master, on_search_trigger, on_open_pdf, **kwargs):
        super().__init__(master, **kwargs)
        self.on_search_trigger = on_search_trigger
        self.on_open_pdf = on_open_pdf
        
        self.setup_ui()

    def setup_ui(self):
        # Configure grid expansion
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)
        
        # ROW 1 =========================================================
        # Operador
        lbl_op = ttk.Label(self, text="Operador")
        lbl_op.grid(row=0, column=0, sticky="w", padx=5, pady=(5, 0))
        self.var_operador = tk.StringVar()
        self.ent_operador = ttk.Entry(self, textvariable=self.var_operador)
        self.ent_operador.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 10))

        # Máquina
        lbl_maq = ttk.Label(self, text="Máquina")
        lbl_maq.grid(row=0, column=1, sticky="w", padx=5, pady=(5, 0))
        self.var_maquina = tk.StringVar(value="Bodor1 (12K)")
        self.cbox_maquina = ttk.Combobox(self, textvariable=self.var_maquina, state="readonly", values=["Bodor1 (12K)", "Bodor2 (6K)", "Dardi"])
        self.cbox_maquina.grid(row=1, column=1, sticky="ew", padx=5, pady=(0, 10))

        # Tipo
        lbl_tipo = ttk.Label(self, text="Tipo de pedido")
        lbl_tipo.grid(row=0, column=2, sticky="w", padx=5, pady=(5, 0))
        self.var_tipo = tk.StringVar(value="Avulso")
        self.cbox_tipo = ttk.Combobox(self, textvariable=self.var_tipo, state="readonly", values=["Avulso", "Estoque", "Pedido", "Reforma", "PPD"])
        self.cbox_tipo.grid(row=1, column=2, sticky="ew", padx=5, pady=(0, 10))
        self.cbox_tipo.bind("<<ComboboxSelected>>", lambda e: self.on_search_trigger())

        # Pedido
        lbl_pedido = ttk.Label(self, text="Número de Pedido")
        lbl_pedido.grid(row=0, column=3, sticky="w", padx=5, pady=(5, 0))
        self.var_pedido = tk.StringVar()
        self.ent_pedido = ttk.Entry(self, textvariable=self.var_pedido)
        self.ent_pedido.grid(row=1, column=3, sticky="ew", padx=5, pady=(0, 10))
        self.ent_pedido.bind("<FocusOut>", lambda e: self.on_search_trigger())
        self.ent_pedido.bind("<Return>", lambda e: self.on_search_trigger())

        # ROW 2 =========================================================
        # Retalho
        lbl_retalho = ttk.Label(self, text="Chapa ou Retalho?")
        lbl_retalho.grid(row=2, column=0, sticky="w", padx=5, pady=(5, 0))
        self.var_retalho = tk.StringVar(value="Chapa Inteira")
        self.cbox_retalho = ttk.Combobox(self, textvariable=self.var_retalho, state="readonly", values=["Chapa Inteira", "Retalho"])
        self.cbox_retalho.grid(row=3, column=0, sticky="ew", padx=5, pady=(0, 10))

        # Saída CNC container
        frame_saida = ttk.Frame(self)
        frame_saida.grid(row=2, column=1, columnspan=3, rowspan=2, sticky="nsew", padx=5, pady=(5, 10))
        
        lbl_saida = ttk.Label(frame_saida, text="Saída CNC a cortar")
        lbl_saida.pack(anchor="w")
        
        frame_saida_controls = ttk.Frame(frame_saida)
        frame_saida_controls.pack(fill="x", expand=True)
        
        self.var_saida = tk.StringVar()
        self.cbox_saida = ttk.Combobox(frame_saida_controls, textvariable=self.var_saida, state="readonly")
        self.cbox_saida.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.btn_pdf = ttk.Button(frame_saida_controls, text="Abrir PDF", command=self.on_open_pdf, width=15)
        self.btn_pdf.pack(side="right")

    def update_saidas(self, results):
        self.cbox_saida['values'] = results
        if results:
            self.cbox_saida.current(0)
        else:
            self.var_saida.set('')

    def disable_fields(self):
        for w in (self.ent_operador, self.cbox_maquina, self.cbox_tipo, 
                 self.ent_pedido, self.cbox_retalho, self.cbox_saida):
            w.config(state="disabled")

    def enable_fields(self):
        self.ent_operador.config(state="normal")
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

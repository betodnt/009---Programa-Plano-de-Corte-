import tkinter as tk
from tkinter import ttk
import xml.etree.ElementTree as ET
import os

class HistoryPanel(ttk.Frame):
    def __init__(self, master, get_xml_path_func, **kwargs):
        super().__init__(master, **kwargs)
        self.get_xml_path_func = get_xml_path_func
        self.current_operator = ""
        self.setup_ui()
        # Removed refresh_history() from here to speed up startup

    def set_operator(self, operator_name):
        """Define o operador atual para filtrar o histórico."""
        if operator_name != self.current_operator:
            self.current_operator = operator_name
            self.refresh_history()

    def setup_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.lbl_title = ttk.Label(self, text="HISTÓRICO", font=("Segoe UI", 10, "bold"))
        self.lbl_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=(0, 4))

        columns = ("pedido", "saida", "tempo")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)

        self.tree.heading("pedido", text="PEDIDO")
        self.tree.heading("saida", text="SAÍDA")
        self.tree.heading("tempo", text="TEMPO")

        self.tree.column("pedido", width=80, anchor="center")
        self.tree.column("saida", width=120, anchor="w")
        self.tree.column("tempo", width=60, anchor="center")

        self.tree.grid(row=1, column=0, sticky="nswe")

        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview, style="My.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.after(100, self.update_scrollbar)

    def update_scrollbar(self, event=None):
        y_scroll = self.tree.yview()
        if y_scroll[0] <= 0 and y_scroll[1] >= 1:
            self.scrollbar.grid_remove()
        else:
            self.scrollbar.grid(row=1, column=1, sticky="ns")

    def refresh_history(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        xml_path = self.get_xml_path_func()
        if not os.path.exists(xml_path):
            return

        operator = self.current_operator.strip()

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            for entrada in root.findall("Entrada"):
                op = entrada.findtext("Operador", "").strip()
                if operator and op.lower() != operator.lower():
                    continue
                pedido = entrada.findtext("Pedido", "")
                saida = entrada.findtext("Saida", "")
                tempo = entrada.findtext("TempoDecorrido", "")

                if tempo:
                    self.tree.insert("", "end", values=(pedido, saida, tempo))

            self.after(100, self.update_scrollbar)
        except Exception as e:
            print(f"Error reading history XML: {e}")

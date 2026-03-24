import tkinter as tk
from tkinter import ttk
import xml.etree.ElementTree as ET
import os
import threading

class HistoryPanel(ttk.Frame):
    def __init__(self, master, get_xml_path_func, **kwargs):
        super().__init__(master, **kwargs)
        self.get_xml_path_func = get_xml_path_func
        self.current_operator = ""
        self._loading = False
        self.setup_ui()

    def set_operator(self, operator_name):
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
        if self._loading:
            return
        self._loading = True
        threading.Thread(target=self._load_history_data, daemon=True).start()

    def _load_history_data(self):
        xml_path = self.get_xml_path_func()
        rows = []
        if os.path.exists(xml_path):
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()
                operator = self.current_operator.strip()
                for entrada in root.findall("Entrada"):
                    op = entrada.findtext("Operador", "").strip()
                    if operator and op.lower() != operator.lower():
                        continue
                    pedido = entrada.findtext("Pedido", "")
                    saida = entrada.findtext("Saida", "")
                    tempo = entrada.findtext("TempoDecorrido", "")
                    if tempo:
                        rows.append((pedido, saida, tempo))
            except Exception as e:
                print(f"Error reading history XML: {e}")
        self.after(0, lambda: self._apply_history_rows(rows))

    def _apply_history_rows(self, rows):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in rows:
            self.tree.insert("", "end", values=row)
        self._loading = False
        self.after(100, self.update_scrollbar)

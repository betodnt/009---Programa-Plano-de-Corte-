import tkinter as tk
from tkinter import ttk
import xml.etree.ElementTree as ET
import os

class HistoryPanel(ttk.Frame):
    def __init__(self, master, get_xml_path_func, **kwargs):
        super().__init__(master, **kwargs)
        self.get_xml_path_func = get_xml_path_func
        self.setup_ui()
        self.refresh_history()

    def setup_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Treeview for history
        columns = ("pedido", "saida", "tempo")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        
        self.tree.heading("pedido", text="PEDIDO")
        self.tree.heading("saida", text="SAÍDA")
        self.tree.heading("tempo", text="TEMPO")

        self.tree.column("pedido", width=80, anchor="center")
        self.tree.column("saida", width=120, anchor="w")
        self.tree.column("tempo", width=60, anchor="center")

        self.tree.grid(row=0, column=0, sticky="nswe")

        # Scrollbar with custom style
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview, style="My.Vertical.TScrollbar")
        self.tree.configure(yscroll=scrollbar.set if 'scrollbar' in locals() else self.scrollbar.set)
        
        # Initial call to check if scrollbar is needed
        self.after(100, self.update_scrollbar)

    def update_scrollbar(self, event=None):
        """Hides scrollbar if not needed."""
        # Check if the treeview content is larger than its display area
        # tree.yview() returns (start, end) fraction
        y_scroll = self.tree.yview()
        if y_scroll[0] <= 0 and y_scroll[1] >= 1:
            self.scrollbar.grid_remove()
        else:
            self.scrollbar.grid(row=0, column=1, sticky="ns")

    def refresh_history(self):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        xml_path = self.get_xml_path_func()
        if not os.path.exists(xml_path):
            return

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Find all entries that have a completion time and belong to this instance
            current_pid = str(os.getpid())
            for entrada in root.findall("Entrada"):
                instancia = entrada.findtext("Instancia", "")
                if instancia != current_pid:
                    continue
                pedido = entrada.findtext("Pedido", "")
                saida = entrada.findtext("Saida", "")
                tempo = entrada.findtext("TempoDecorrido", "")
                
                if tempo: # Only show completed ones
                    self.tree.insert("", "end", values=(pedido, saida, tempo))
            
            # Update scrollbar after data load
            self.after(100, self.update_scrollbar)
        except Exception as e:
            print(f"Error reading history XML: {e}")

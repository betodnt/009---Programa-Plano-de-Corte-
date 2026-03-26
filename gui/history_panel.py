import os
import threading
import xml.etree.ElementTree as ET
from collections import deque
from tkinter import ttk


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

        self.lbl_title = ttk.Label(self, text="HISTORICO", style="Section.TLabel")
        self.lbl_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=(12, 12), pady=(12, 6))

        columns = ("pedido", "saida", "tempo")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=12)
        self.tree.heading("pedido", text="PEDIDO")
        self.tree.heading("saida", text="SAIDA")
        self.tree.heading("tempo", text="TEMPO")

        self.tree.column("pedido", width=86, anchor="center", stretch=True)
        self.tree.column("saida", width=146, anchor="w", stretch=True)
        self.tree.column("tempo", width=74, anchor="center", stretch=True)
        self.tree.grid(row=1, column=0, sticky="nsew", padx=(12, 0), pady=(0, 12))

        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview, style="My.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.bind("<Configure>", self._on_resize)
        self.after(100, self._adjust_columns)

    def _on_resize(self, _event=None):
        self._adjust_columns()

    def _adjust_columns(self):
        try:
            total = self.tree.winfo_width()
            if total <= 10:
                return

            ratios = {"pedido": 0.27, "saida": 0.51, "tempo": 0.22}
            for col, ratio in ratios.items():
                self.tree.column(col, width=max(70, int(total * ratio)), stretch=True)
        except Exception:
            pass

        self.after(100, self.update_scrollbar)

    def update_scrollbar(self, _event=None):
        y_scroll = self.tree.yview()
        if y_scroll[0] <= 0 and y_scroll[1] >= 1:
            self.scrollbar.grid_remove()
        else:
            self.scrollbar.grid(row=1, column=1, sticky="ns", padx=(0, 12), pady=(0, 12))

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
                target_op = self.current_operator.strip().lower()
                recent_rows = deque(maxlen=30)

                context = ET.iterparse(xml_path, events=("start", "end"))
                context = iter(context)
                _event, root = next(context)

                for event, elem in context:
                    if event == "end" and elem.tag == "Entrada":
                        op_text = elem.findtext("Operador", "")
                        if not target_op or (op_text and op_text.strip().lower() == target_op):
                            tempo = elem.findtext("TempoDecorrido", "")
                            if tempo:
                                pedido = elem.findtext("Pedido", "")
                                saida = elem.findtext("Saida", "")
                                recent_rows.append((pedido, saida, tempo))
                        root.clear()

                rows = list(recent_rows)
                rows.reverse()
            except Exception as exc:
                print(f"Error reading history XML: {exc}")
        self.after(0, lambda: self._apply_history_rows(rows))

    def _apply_history_rows(self, rows):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in rows:
            self.tree.insert("", "end", values=row)
        self._loading = False
        self.after(100, self.update_scrollbar)

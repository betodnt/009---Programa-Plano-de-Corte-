import tkinter as tk
from tkinter import ttk
import xml.etree.ElementTree as ET
import os
import threading
from collections import deque

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
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=12)  # Reduzido de 15 para 12

        self.tree.heading("pedido", text="PEDIDO")
        self.tree.heading("saida", text="SAÍDA")
        self.tree.heading("tempo", text="TEMPO")

        self.tree.column("pedido", width=80, anchor="center", stretch=True)
        self.tree.column("saida", width=120, anchor="w", stretch=True)
        self.tree.column("tempo", width=60, anchor="center", stretch=True)

        self.tree.grid(row=1, column=0, sticky="nswe")

        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview, style="My.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        # Responsivo: ajusta colunas ao redimensionar painel
        self.bind("<Configure>", self._on_resize)
        self.after(100, self._adjust_columns)

    def _on_resize(self, event=None):
        self._adjust_columns()

    def _adjust_columns(self):
        try:
            total = self.tree.winfo_width()
            if total <= 10:
                return

            # Otimização: só recalcular se largura mudou significativamente
            if not hasattr(self, '_last_width') or abs(total - self._last_width) > 30:
                self._last_width = total

                # Estimativa simples baseada no comprimento do texto
                ratios = {
                    'pedido': 0.26,
                    'saida': 0.54,
                    'tempo': 0.20,
                }
                for col, ratio in ratios.items():
                    header = self.tree.heading(col, "text")
                    min_width = max(60, len(str(header)) * 8)  # Estimativa simples
                    width = max(min_width, int(total * ratio))
                    self.tree.column(col, width=width, stretch=True)
            else:
                # Apenas ajustar proporções
                ratios = {
                    'pedido': 0.26,
                    'saida': 0.54,
                    'tempo': 0.20,
                }
                for col, ratio in ratios.items():
                    width = int(total * ratio)
                    self.tree.column(col, width=width, stretch=True)
        except Exception:
            pass

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
                # Otimização: iterparse carrega o XML via stream (baixo consumo de memória)
                # deque(maxlen=N) mantém automaticamente apenas os N últimos itens (mais recentes)
                target_op = self.current_operator.strip().lower()
                max_entries = 30
                recent_rows = deque(maxlen=max_entries)

                # events=("start", "end") permite limpar a raiz para liberar memória
                context = ET.iterparse(xml_path, events=("start", "end"))
                context = iter(context)
                event, root = next(context) # Pega a referência da raiz

                for event, elem in context:
                    if event == "end" and elem.tag == "Entrada":
                        op_text = elem.findtext("Operador", "")
                        # Filtra pelo operador (case insensitive)
                        if not target_op or (op_text and op_text.strip().lower() == target_op):
                            tempo = elem.findtext("TempoDecorrido", "")
                            # Só mostra finalizados (que tem tempo decorrido)
                            if tempo:
                                pedido = elem.findtext("Pedido", "")
                                saida = elem.findtext("Saida", "")
                                recent_rows.append((pedido, saida, tempo))
                        
                        root.clear() # Limpa memória processada imediatamente
                
                # Inverte para mostrar o mais recente no topo da lista
                rows = list(recent_rows)
                rows.reverse()
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

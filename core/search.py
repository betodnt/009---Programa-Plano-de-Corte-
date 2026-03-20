import os
import threading

class SearchFilesRunner:
    def __init__(self, pedido, tipo, base_path, on_progress_update, on_finished):
        self.pedido = pedido
        self.tipo = tipo
        self.base_path = base_path
        self._is_canceled = False
        self.on_progress_update = on_progress_update # callback(current, total)
        self.on_finished = on_finished               # callback(list_of_results)
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self):
        self.thread.start()

    def cancel(self):
        self._is_canceled = True

    def run(self):
        results = []
        try:
            files = [f for f in os.listdir(self.base_path) if f.lower().endswith(".cnc")]
        except Exception:
            if self.on_finished: self.on_finished(results)
            return

        total = len(files)
        prefix = ""
        if self.tipo == "Pedido": prefix = "P"
        elif self.tipo == "Avulso": prefix = "A"
        elif self.tipo == "Estoque": prefix = "E"
        elif self.tipo == "PPD": prefix = "PPD"
        elif self.tipo == "Reforma": prefix = "R"
        else:
            if self.on_finished: self.on_finished(results)
            return

        for i, filename in enumerate(files):
            if self._is_canceled:
                break
            
            parts = filename.split('_')
            for part in parts:
                if part.startswith(prefix) and part[1:] == self.pedido:
                    results.append(filename)
                    break
                    
            if i % 10 == 0:
                if self.on_progress_update:
                    self.on_progress_update(i+1, total)

        if self.on_progress_update:
            self.on_progress_update(total, total)
        if not self._is_canceled and self.on_finished:
            self.on_finished(results)


class SearchPdfRunner:
    def __init__(self, targets, start_path, on_finished):
        # targets pode ser uma string única ou uma lista de strings
        self.targets = [targets] if isinstance(targets, str) else targets
        self.start_path = start_path
        self._is_canceled = False
        self.on_finished = on_finished # callback(found_path)
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self):
        self.thread.start()

    def cancel(self):
        self._is_canceled = True

    def run(self):
        found_path = ""
        # Prepara targets em lowercase para comparação insensível a caixa
        targets_lower = [t.lower() for t in self.targets]
        
        for root, dirs, files in os.walk(self.start_path):
            if self._is_canceled:
                break
            
            # Verifica cada arquivo na pasta contra a lista de targets
            for f in files:
                if f.lower() in targets_lower:
                    found_path = os.path.join(root, f)
                    break
            
            if found_path:
                break
                
        if self.on_finished:
            self.on_finished(found_path)

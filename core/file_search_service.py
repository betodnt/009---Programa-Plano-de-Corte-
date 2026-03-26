import os
import threading
from dataclasses import dataclass

from core.config import ConfigManager


TIPO_PREFIX_MAP = {
    "Pedido": "P",
    "Avulso": "A",
    "Estoque": "E",
    "PPD": "PPD",
    "Reforma": "R",
}


@dataclass
class SearchRequest:
    pedido: str
    tipo: str
    base_path: str


class FileSearchService:
    @staticmethod
    def build_request(pedido, tipo, base_path=""):
        pedido = (pedido or "").strip()
        return SearchRequest(
            pedido=pedido,
            tipo=(tipo or "").strip(),
            base_path=base_path or ConfigManager.get_server_path(),
        )

    @staticmethod
    def validate_search(request):
        if not request.pedido:
            return False, ""
        if not os.path.exists(request.base_path):
            return False, (
                "O diretorio base para as saidas CNC nao existe:\n"
                f"{request.base_path}\n\nVerifique as configuracoes."
            )
        if request.tipo not in TIPO_PREFIX_MAP:
            return False, "Tipo de busca invalido."
        return True, ""

    @staticmethod
    def find_matching_saidas(request, progress_callback=None, cancel_check=None):
        try:
            files = [name for name in os.listdir(request.base_path) if name.lower().endswith(".cnc")]
        except Exception:
            return []

        prefix = TIPO_PREFIX_MAP.get(request.tipo, "")
        if not prefix:
            return []

        total = len(files)
        results = []
        for index, filename in enumerate(files, start=1):
            if cancel_check and cancel_check():
                break

            parts = filename.split("_")
            for part in parts:
                if part.startswith(prefix) and part[len(prefix) :] == request.pedido:
                    results.append(filename)
                    break

            if progress_callback and (index % 10 == 0 or index == total):
                progress_callback(index, total)

        return results

    @staticmethod
    def find_pdf(pdf_filename, start_path, cancel_check=None):
        if not pdf_filename:
            return ""

        for root, _dirs, files in os.walk(start_path):
            if cancel_check and cancel_check():
                break
            if pdf_filename in files:
                return os.path.join(root, pdf_filename)
        return ""


class SearchFilesRunner:
    def __init__(self, pedido, tipo, base_path, on_progress_update, on_finished):
        self.request = FileSearchService.build_request(pedido, tipo, base_path)
        self._is_canceled = False
        self.on_progress_update = on_progress_update
        self.on_finished = on_finished
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self):
        self.thread.start()

    def cancel(self):
        self._is_canceled = True

    def run(self):
        results = FileSearchService.find_matching_saidas(
            self.request,
            progress_callback=self.on_progress_update,
            cancel_check=lambda: self._is_canceled,
        )
        if not self._is_canceled and self.on_finished:
            self.on_finished(results)


class SearchPdfRunner:
    def __init__(self, pdf_filename, start_path, on_finished):
        self.pdf_filename = pdf_filename
        self.start_path = start_path
        self._is_canceled = False
        self.on_finished = on_finished
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self):
        self.thread.start()

    def cancel(self):
        self._is_canceled = True

    def run(self):
        found_path = FileSearchService.find_pdf(
            self.pdf_filename,
            self.start_path,
            cancel_check=lambda: self._is_canceled,
        )
        if self.on_finished:
            self.on_finished(found_path)

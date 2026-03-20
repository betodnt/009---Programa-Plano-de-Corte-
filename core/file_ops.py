import shutil
import threading
import logging
import os

class FileOperationRunner:
    def __init__(self, op_type, src, dst, on_finished):
        self.op_type = op_type # "COPY" or "MOVE"
        self.src = src
        self.dst = dst
        self.on_finished = on_finished # callback(error_string)
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self):
        self.thread.start()

    def run(self):
        try:
            # Ensure destination directory exists
            dst_dir = os.path.dirname(self.dst)
            if dst_dir and not os.path.exists(dst_dir):
                os.makedirs(dst_dir, exist_ok=True)
            
            if self.op_type == "COPY":
                shutil.copy2(self.src, self.dst)
            elif self.op_type == "MOVE":
                shutil.move(self.src, self.dst)
            if self.on_finished:
                self.on_finished("")
        except Exception as e:
            logging.error(f"Erro na operação de arquivo ({self.op_type}): {e}", exc_info=True)
            if self.on_finished:
                self.on_finished(f"Falha na operação: {str(e)}")

import sys
import os
import traceback
import logging
from logging.handlers import RotatingFileHandler
import tkinter as tk
import tkinter.messagebox as messagebox

# Adiciona o diretório atual ao sys.path para importações limpas
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app_window import AppWindow

if __name__ == "__main__":
    try:
        app = AppWindow()
        app.mainloop()
    except Exception as e:
        # If the app fails to start (e.g., missing dependencies or config issues), show a message.
        tb = traceback.format_exc()
        print(tb)
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Erro ao iniciar", f"O aplicativo não conseguiu iniciar:\n{e}\n\nVerifique o console para mais detalhes.")
        root.destroy()

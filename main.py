import sys
import os

# Adiciona o diretório atual ao sys.path para importações limpas
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app_window import AppWindow

if __name__ == "__main__":
    app = AppWindow()
    app.mainloop()

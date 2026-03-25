import sys
import os

# Adiciona o diretório atual ao sys.path para importações limpas
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app_window import AppWindow

if __name__ == "__main__":
    try:
        app = AppWindow()
        app.mainloop()
    except Exception as e:
        # Se o aplicativo não conseguir iniciar (ex: dependências ausentes ou problemas de configuração), mostra uma mensagem.
        import traceback, tkinter as tk, tkinter.messagebox as messagebox
        tb = traceback.format_exc()
        
        # Logging profissional: Grava em arquivo pois o console pode não estar visível
        print(tb)
        try:
            with open("error.log", "w") as f:
                f.write(f"Erro ao iniciar em {sys.argv[0]}:\n\n{tb}")
        except:
            pass

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Erro ao iniciar", f"O aplicativo não conseguiu iniciar:\n{e}\n\nVerifique 'error.log' para mais detalhes.")
        root.destroy()

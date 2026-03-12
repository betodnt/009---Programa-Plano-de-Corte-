import os
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from datetime import datetime

from core.config import ConfigManager
from core.database import DatabaseManager
from core.search import SearchFilesRunner, SearchPdfRunner
from core.file_ops import FileOperationRunner

from gui.form_panel import FormPanel
from gui.action_panel import ActionPanel

class ProgressDialog(tk.Toplevel):
    def __init__(self, master, title="Aguarde...", max_val=0):
        super().__init__(master)
        self.title(title)
        self.geometry("300x120")
        self.resizable(False, False)
        # Make it modal
        self.transient(master)
        self.grab_set()
        
        self.lbl_texto = ttk.Label(self, text="Aguarde...")
        self.lbl_texto.pack(pady=(15, 10))
        
        # se max_val for 0, usa modo inderteminado
        mode = 'determinate' if max_val > 0 else 'indeterminate'
        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=250, mode=mode)
        if max_val > 0:
            self.progress['maximum'] = max_val
        self.progress.pack()
        
        if max_val == 0:
            self.progress.start(15)

        self.btn_cancel = ttk.Button(self, text="Cancelar", command=self.on_cancel)
        self.btn_cancel.pack(pady=(10, 5))
        
        self.is_canceled = False
        
        # Center on parent
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - (self.winfo_width() // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def on_cancel(self):
        self.lbl_texto.config(text="Cancelando Busca...")
        self.btn_cancel.config(state="disabled")
        self.is_canceled = True

    def set_progress(self, current, text=None):
        if text:
            self.lbl_texto.config(text=text)
        self.progress['value'] = current

    def close(self):
        self.destroy()

class AppWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Controle de Corte e Dobra")
        self.geometry("800x500")
        
        ConfigManager.load_settings()
        
        self._setup_styles()
        self._build_ui()
        
        self.active_runner = None
        self.progress_win = None

    def _setup_styles(self):
        style = ttk.Style(self)
        
        # Cores base do seu style.css
        bg_dark = "#2b2b2b"      # Fundo principal
        bg_field = "#3c3f41"     # Fundo dos campos
        fg_white = "#ffffff"     # Texto geral
        accent_blue = "#4a90e2"  # Botão azul
        accent_green = "#27ae60" # Botão Iniciar
        accent_red = "#c0392b"   # Botão Finalizar
        accent_timer = "#f39c12" # Cor do cronômetro

        # Configurações globais
        self.configure(bg=bg_dark)
        style.theme_use('default') 
        
        # Estilo de Quadros (Frames)
        style.configure("TFrame", background=bg_dark)
        
        # Estilo de Labels
        style.configure("TLabel", background=bg_dark, foreground="#e0e0e0", font=("Segoe UI", 12))
        
        # Estilo de Campos de Entrada e Combobox
        # Nota: Tkinter nativo tem limitações no arredondamento, mas cores funcionam bem
        style.configure("TEntry", fieldbackground=bg_field, foreground=fg_white, insertcolor=fg_white)
        style.configure("TCombobox", fieldbackground=bg_field, foreground=fg_white, arrowcolor=fg_white)
        style.map("TCombobox", fieldbackground=[('readonly', bg_field)], foreground=[('readonly', fg_white)])

        # Botão Padrão (Azul)
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=5)
        
        # Estilo para os botões de ação (Iniciar/Finalizar)
        style.configure("Action.TButton", font=("Segoe UI", 14, "bold"), padding=10)
        
        # Iniciar (Verde)
        style.configure("Iniciar.Action.TButton", background=accent_green, foreground="white")
        style.map("Iniciar.Action.TButton", background=[('active', "#2ecc71"), ('disabled', "#555555")])
        
        # Finalizar (Vermelho)
        style.configure("Finalizar.Action.TButton", background=accent_red, foreground="white")
        style.map("Finalizar.Action.TButton", background=[('active', "#e74c3c"), ('disabled', "#555555")])
        
        # Timer (Label especial)
        style.configure("Timer.TLabel", foreground=accent_timer, font=("Segoe UI", 36, "bold"), background=bg_dark)


    def _build_ui(self):
        main_frame = ttk.Frame(self, padding="40 40 40 40")
        main_frame.pack(fill="both", expand=True)
        
        self.form_panel = FormPanel(main_frame, self.handle_search, self.handle_open_pdf)
        self.form_panel.pack(fill="x", pady=(0, 20))
        
        # Espaço reservado equivalendo ao Stretch
        spacer = ttk.Frame(main_frame)
        spacer.pack(fill="both", expand=True)
        
        self.action_panel = ActionPanel(main_frame, self.handle_iniciar, self.handle_finalizar)
        self.action_panel.pack(fill="x", pady=(20, 0))

    def handle_search(self):
        dados = self.form_panel.get_data()
        pedido = dados["pedido"]
        if not pedido: return
        
        tipo = dados["tipo"]
        base_path = ConfigManager.get_server_path()
        
        self.form_panel.update_saidas([])
        self.form_panel.disable_fields()
        self.action_panel.btn_iniciar.state(['disabled'])
        
        self.progress_win = ProgressDialog(self, title="Buscando arquivos Cnc...", max_val=0) # starts indeterminate
        
        self.active_runner = SearchFilesRunner(
            pedido=pedido, 
            tipo=tipo, 
            base_path=base_path,
            on_progress_update=self.on_search_progress,
            on_finished=self.on_search_finished
        )
        # In Tkinter, periodic checking for thread cancellation via UI flag
        self._check_runner_cancel()
        self.active_runner.start()

    def _check_runner_cancel(self):
        if self.progress_win and self.progress_win.is_canceled and self.active_runner:
            self.active_runner.cancel()
        if self.active_runner and self.active_runner.thread.is_alive():
            self.after(200, self._check_runner_cancel)

    def on_search_progress(self, current, total):
        # Must execute in main thread
        def safe_update():
            if self.progress_win and self.progress_win.winfo_exists():
                if self.progress_win.progress.cget("mode") == "indeterminate":
                    self.progress_win.progress.config(mode="determinate", maximum=total)
                    self.progress_win.progress.stop()
                self.progress_win.set_progress(current)
        self.after_idle(safe_update)

    def on_search_finished(self, results):
        def finalize():
            if self.progress_win:
                self.progress_win.close()
            self.form_panel.update_saidas(results)
            self.form_panel.enable_fields()
            self.action_panel.btn_iniciar.state(['!disabled'])
            
            if not results and not (self.progress_win and self.progress_win.is_canceled):
                messagebox.showinfo("Aviso", "Não foi encontrada nenhuma saída CNC para este pedido.")
                
            self.active_runner = None
            self.progress_win = None
            
        self.after_idle(finalize)


    def handle_iniciar(self):
        saida = self.form_panel.get_data()["saida"]
        if not saida: return False
        
        dados = self.form_panel.get_data()
        dt_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        file_path = ConfigManager.get_k8_data_path()
        
        sucesso, erro = DatabaseManager.save_entrada(
            file_path, dados["pedido"], dados["operador"], dados["maquina"],
            dados["retalho"], saida, dados["tipo"], dt_inicio
        )
        
        if not sucesso:
            messagebox.showwarning("Erro", erro)
            return False
            
        self.form_panel.disable_fields()
        
        # Cópia do arquivo
        src_path = os.path.join(ConfigManager.get_server_path(), saida)
        dst_path = os.path.join(ConfigManager.get_saidas_cnc_path(), saida)
        
        self.progress_win = ProgressDialog(self, title="Copiando arquivo CNC...", max_val=0)
        
        self.active_runner = FileOperationRunner("COPY", src_path, dst_path, self.on_file_op_finished)
        self.active_runner.start()
        
        return True

    def handle_finalizar(self):
        dados = self.form_panel.get_data()
        saida = dados["saida"]
        if not saida: return
        
        dt_termino = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tempo_decorrido = self.action_panel.get_elapsed_time_string()
        
        file_path = ConfigManager.get_k8_data_path()
        
        sucesso, erro = DatabaseManager.save_termino(
            file_path, dados["pedido"], dados["operador"], dados["maquina"], dt_termino, tempo_decorrido
        )
        
        if not sucesso:
            messagebox.showwarning("Erro", erro)
            # We don't return to allow restarting finisher? Wait, if failed, we should allow them to click again.
            self.action_panel.btn_finalizar.state(['!disabled'])
            self.action_panel.btn_iniciar.state(['disabled'])
            return
            
        # Move back
        src_path = os.path.join(ConfigManager.get_saidas_cnc_path(), saida)
        dst_path = os.path.join(ConfigManager.get_saidas_cortadas_path(), saida)
        
        self.progress_win = ProgressDialog(self, title="Movendo arquivo CNC...", max_val=0)
        
        self.active_runner = FileOperationRunner("MOVE", src_path, dst_path, lambda e: self.on_file_op_finished(e, "Corte Finalizado com sucesso!"))
        self.active_runner.start()

    def on_file_op_finished(self, err_msg, success_title="Sucesso"):
        def finalize():
            if self.progress_win:
                self.progress_win.close()
                
            if "Corte Finalizado" in success_title and not err_msg:
                self.form_panel.enable_fields()
                self.action_panel.btn_iniciar.state(['!disabled'])
                self.action_panel.btn_finalizar.state(['disabled'])
            elif err_msg:
                 # If it failed to start, revert ui
                 self.action_panel.stop_timer()
                 self.form_panel.enable_fields()
                 self.action_panel.lbl_timer.config(text="00:00:00")
            
            if err_msg:
                messagebox.showwarning("Aviso de Rede", err_msg)
            else:
                messagebox.showinfo("Sucesso", success_title)
                
            self.active_runner = None
            self.progress_win = None
        self.after_idle(finalize)


    def handle_open_pdf(self):
        saida = self.form_panel.get_data()["saida"]
        if not saida: return
        
        pdf_name = saida.split("_S")[0] + ".pdf"
        
        self.progress_win = ProgressDialog(self, title="Procurando PDF na Rede...", max_val=0)
        
        search_path = ConfigManager.get_plano_corte_path()
        self.active_runner = SearchPdfRunner(pdf_name, search_path, self.on_pdf_search_finished)
        self._check_runner_cancel()
        self.active_runner.start()
        
    def on_pdf_search_finished(self, found_path):
        def finalize():
            if self.progress_win:
                self.progress_win.close()
            if not found_path and not (self.progress_win and self.progress_win.is_canceled):
                messagebox.showwarning("Não Encontrado", "O arquivo PDF correspondente não foi encontrado na base.")
            elif found_path:
                webbrowser.open(f"file://{found_path}")
            
            self.active_runner = None
            self.progress_win = None
        self.after_idle(finalize)

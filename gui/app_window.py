import os
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from datetime import datetime
import sys
import threading
import time

from core.config import ConfigManager
from core.database import DatabaseManager
from core.search import SearchFilesRunner, SearchPdfRunner
from core.file_ops import FileOperationRunner
from core.operators import OperatorsManager
from core.locks import LocksManager

from gui.form_panel import FormPanel
from gui.action_panel import ActionPanel
from gui.history_panel import HistoryPanel
from gui.config_dialog import ConfigDialog


class ProgressDialog(tk.Toplevel):
    def __init__(self, master, title="Aguarde...", max_val=0):
        super().__init__(master)
        self.title(title)
        self.geometry("300x100")
        self.resizable(False, False)
        self.configure(bg="#2b2b2b")
        self.transient(master)
        self.grab_set()

        self.lbl_texto = tk.Label(self, text="Aguarde...", bg="#2b2b2b", fg="#ffffff",
                                  font=("Segoe UI", 11), justify="center")
        self.lbl_texto.pack(pady=(15, 10))

        mode = 'determinate' if max_val > 0 else 'indeterminate'
        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=250, mode=mode)
        if max_val > 0:
            self.progress['maximum'] = max_val
        self.progress.pack()

        if max_val == 0:
            self.progress.start(15)

        self.btn_cancel = ttk.Button(self, text="Cancelar", command=self.on_cancel)
        self.btn_cancel.pack(pady=(8, 4))

        self.is_canceled = False

        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - (self.winfo_width() // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def on_cancel(self):
        self.lbl_texto.config(text="Cancelando...")
        self.btn_cancel.config(state="disabled")
        self.is_canceled = True

    def set_progress(self, current, text=None):
        if text:
            self.lbl_texto.config(text=text)
        self.progress['value'] = current

    def close(self):
        try:
            self.destroy()
        except Exception:
            pass


class AppWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Controle de Corte e Dobra")
        self.geometry("1000x550")

        ConfigManager.load_settings()

        self._setup_styles()
        self._build_ui()
        self._load_icon()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.active_runner = None
        self.progress_win = None

        self.after(500, self._refresh_recent_operators)
        self.after(1000, self._update_saidas_if_needed)

    def _update_saidas_if_needed(self):
        # Move a verificação de locks (I/O de arquivo) para uma thread
        if self.form_panel._all_saidas and self.form_panel.cbox_saida.cget('state') == 'readonly':
            threading.Thread(target=self._background_check_locks, daemon=True).start()
        
        self.after(5000, self._update_saidas_if_needed)

    def _background_check_locks(self):
        try:
            # Apenas busca os locks, não atualiza UI aqui
            maquina = self.form_panel.var_maquina.get()
            locked_saidas = LocksManager.get_locked_saidas(maquina)
            # Agenda atualização da UI
            self.after_idle(lambda: self.form_panel.apply_locked_saidas_filter(locked_saidas))
        except Exception:
            pass

    def on_closing(self):
        if self.active_runner and self.active_runner.thread.is_alive():
            self.active_runner.cancel()
        LocksManager.release_all_locks_for_pid()
        self.quit()
        sys.exit(0)

    def _setup_styles(self):
        style = ttk.Style(self)
        bg_dark      = "#2b2b2b"
        bg_field     = "#3c3f41"
        fg_white     = "#ffffff"
        accent_blue  = "#4a90e2"
        accent_green = "#27ae60"
        accent_red   = "#c0392b"
        accent_timer = "#f39c12"

        self.configure(bg=bg_dark)
        style.theme_use('clam')

        style.configure("TFrame", background=bg_dark)
        style.configure("TLabel", background=bg_dark, foreground="#e0e0e0", font=("Segoe UI", 11))
        style.configure("TEntry",
            fieldbackground=bg_field, foreground=fg_white, insertcolor=fg_white,
            borderwidth=1, relief="flat", padding=5)
        style.configure("TCombobox",
            fieldbackground=bg_field, foreground=fg_white, background=bg_field,
            arrowcolor=fg_white, borderwidth=1, relief="flat", padding=4)
        style.map("TCombobox",
            fieldbackground=[('readonly', bg_field)],
            foreground=[('readonly', fg_white)],
            lightcolor=[('focus', accent_blue)],
            darkcolor=[('focus', accent_blue)])
        style.configure("TButton",
            font=("Segoe UI", 10, "bold"), padding=(20, 8),
            background=bg_field, foreground=fg_white, borderwidth=1, relief="flat")
        style.map("TButton",
            background=[('active', "#4e5254")],
            foreground=[('active', fg_white)],
            relief=[('pressed', 'groove'), ('!pressed', 'flat')])
        style.configure("Action.TButton", font=("Segoe UI", 12, "bold"), padding=(25, 12))
        style.configure("Iniciar.Action.TButton", background=accent_green, foreground="white", borderwidth=0)
        style.map("Iniciar.Action.TButton", background=[('active', "#2ecc71"), ('disabled', "#555555")])
        style.configure("Finalizar.Action.TButton", background=accent_red, foreground="white", borderwidth=0)
        style.map("Finalizar.Action.TButton", background=[('active', "#e74c3c"), ('disabled', "#555555")])
        style.configure("Timer.TLabel", foreground=accent_timer, font=("Segoe UI", 36, "bold"), background=bg_dark)
        style.configure("Treeview",
            background=bg_dark, foreground=fg_white, fieldbackground=bg_dark,
            borderwidth=0, font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
            background=bg_field, foreground=fg_white, relief="flat", font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[('selected', accent_blue)])

        style.element_create("My.Vertical.Scrollbar.trough", "from", "default")
        style.element_create("My.Vertical.Scrollbar.thumb", "from", "default")
        style.layout("My.Vertical.TScrollbar", [
            ('My.Vertical.Scrollbar.trough', {
                'children': [('My.Vertical.Scrollbar.thumb', {'expand': '1', 'sticky': 'nswe'})],
                'sticky': 'ns'
            })
        ])
        style.configure("My.Vertical.TScrollbar",
            background="#444444", troughcolor=bg_dark, borderwidth=0, arrowsize=0, width=8)
        style.map("My.Vertical.TScrollbar",
            background=[('active', "#555555"), ('pressed', "#666666")])

    def _load_icon(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        icon_path = os.path.join(base_dir, "icon.png")
        icon_ico_path = os.path.join(base_dir, "icon.ico")
        try:
            if os.path.exists(icon_path):
                self.icon_photo = tk.PhotoImage(file=icon_path)
                self.iconphoto(True, self.icon_photo)
            if os.path.exists(icon_ico_path):
                self.iconbitmap(icon_ico_path)
        except Exception as e:
            print(f"Erro ao carregar ícone: {e}")

    def open_settings(self):
        config_win = ConfigDialog(self)
        self.wait_window(config_win)
        # Atualizar a exibição da máquina após fechar as configurações
        self.form_panel.update_machine_display()

    def _build_ui(self):
        main_container = ttk.Frame(self, padding="10")
        main_container.pack(fill="both", expand=True)

        self.history_panel = HistoryPanel(main_container, ConfigManager.get_k8_data_path, width=280)
        self.history_panel.pack(side="left", fill="both", expand=False, padx=(0, 20))

        right_panel = ttk.Frame(main_container)
        right_panel.pack(side="right", fill="both", expand=True)

        self.form_panel = FormPanel(right_panel, self.handle_search, self.handle_open_pdf, self.open_settings)
        self.form_panel.pack(fill="x", pady=(0, 20))
        self.form_panel.cbox_operador.bind("<<ComboboxSelected>>", self._on_operator_changed)

        ttk.Frame(right_panel).pack(fill="both", expand=True)

        self.action_panel = ActionPanel(right_panel, self.handle_iniciar, self.handle_finalizar)
        self.action_panel.pack(fill="x", pady=(20, 20), padx=(0, 20))

    def handle_search(self):
        dados = self.form_panel.get_data()
        pedido = dados["pedido"]
        if not pedido:
            return

        base_path = ConfigManager.get_server_path()

        self.form_panel.update_saidas([])
        self.form_panel.disable_fields()
        self.action_panel.btn_iniciar.state(['disabled'])

        if not os.path.exists(base_path):
            messagebox.showwarning(
                "Caminho inválido",
                f"O diretório base para as saídas CNC não existe:\n{base_path}\n\nVerifique as configurações.")
            self.form_panel.enable_fields()
            self.action_panel.btn_iniciar.state(['!disabled'])
            return

        self.progress_win = ProgressDialog(self, title="Buscando arquivos CNC...", max_val=0)

        self.active_runner = SearchFilesRunner(
            pedido=pedido,
            tipo=dados["tipo"],
            base_path=base_path,
            on_progress_update=self.on_search_progress,
            on_finished=self.on_search_finished)
        self._check_runner_cancel()
        self.active_runner.start()

    def show_toast(self, message, duration=2000):
        toast = tk.Toplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        label = tk.Label(toast, text=message, bg="#34495e", fg="#ffffff",
                         padx=60, pady=30, font=("Segoe UI", 36, "bold"))
        label.pack()
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (label.winfo_reqwidth() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (label.winfo_reqheight() // 2)
        toast.geometry(f"+{x}+{y}")
        self.after(duration, toast.destroy)

    def _check_runner_cancel(self):
        if self.progress_win and self.progress_win.is_canceled and self.active_runner:
            self.active_runner.cancel()
        if self.active_runner and self.active_runner.thread.is_alive():
            self.after(200, self._check_runner_cancel)

    def on_search_progress(self, current, total):
        def safe_update():
            if self.progress_win:
                try:
                    if self.progress_win.progress.cget("mode") == "indeterminate":
                        self.progress_win.progress.config(mode="determinate", maximum=total)
                        self.progress_win.progress.stop()
                    self.progress_win.set_progress(current)
                except Exception:
                    pass
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

    def on_file_op_finished(self, err_msg, success_title):
        def finalize():
            if self.progress_win:
                self.progress_win.close()

            if err_msg:
                if success_title == "INICIADO":
                    dados = self.form_panel.get_data()
                    LocksManager.release_lock(dados["maquina"], dados["saida"])
                self.action_panel.stop_timer()
                self.action_panel.lbl_timer.config(text="00:00:00")
                self.form_panel.enable_fields()
                self.action_panel.btn_iniciar.state(['!disabled'])
                self.action_panel.btn_finalizar.state(['disabled'])
                messagebox.showwarning("Aviso de Rede", err_msg)
            else:
                if success_title == "INICIADO":
                    # Salva a entrada após a cópia bem-sucedida
                    dados = self.form_panel.get_data()
                    saida = dados["saida"]
                    dt_inicio = self.start_time.strftime("%Y-%m-%d %H:%M:%S")
                    file_path = ConfigManager.get_k8_data_path()
                    DatabaseManager.save_entrada(
                        file_path, dados["pedido"], dados["operador"], dados["maquina"],
                        dados["retalho"], saida, dados["tipo"], dt_inicio)
                    self.show_toast("Corte Iniciado!")
                    if saida:
                        nif_path = os.path.join(ConfigManager.get_server_path(),
                                                saida.replace(".cnc", ".nif"))
                        if os.path.exists(nif_path):
                            webbrowser.open(f"file://{nif_path}")
                else:
                    # Salva o término após a movimentação bem-sucedida
                    dados = self.form_panel.get_data()
                    dt_termino = self.end_time.strftime("%Y-%m-%d %H:%M:%S")
                    file_path = ConfigManager.get_k8_data_path()
                    ok, err = DatabaseManager.save_termino(
                        file_path, dados["pedido"], dados["operador"], dados["maquina"], dt_termino, self.elapsed_time)
                    LocksManager.release_lock(dados["maquina"], dados["saida"])
                    self.form_panel.update_saidas(self.form_panel._all_saidas)
                    self.history_panel.current_operator = dados["operador"]
                    self.history_panel.refresh_history()
                    self.form_panel.enable_fields()
                    self.action_panel.btn_iniciar.state(['!disabled'])
                    self.action_panel.btn_finalizar.state(['disabled'])
                    self.action_panel.lbl_timer.config(text="00:00:00")
                    messagebox.showinfo("Sucesso", success_title)

            self.active_runner = None
            self.progress_win = None
        self.after_idle(finalize)

    def handle_iniciar(self):
        dados = self.form_panel.get_data()
        saida = dados["saida"]
        if not saida:
            return False

        if not dados["operador"].strip():
            messagebox.showwarning("Operador obrigatório", "Informe o nome do operador antes de iniciar.")
            return False

        if LocksManager.is_locked(dados["maquina"], saida):
            messagebox.showwarning("Saída Indisponível",
                f"A saída '{saida}' já está sendo usada por outro operador na máquina '{dados['maquina']}'.\n\nEscolha outra saída ou aguarde a finalização.")
            return False

        self.start_time = datetime.now()
        dt_inicio = self.start_time.strftime("%Y-%m-%d %H:%M:%S")

        OperatorsManager.add_operator(dados["operador"])
        if not LocksManager.acquire_lock(dados["maquina"], saida, dados["operador"], dados["pedido"]):
            messagebox.showerror("Erro de Rede", "Não foi possível acessar o arquivo de controle na rede. Verifique se outra máquina está salvando dados.")
            return False

        self.form_panel.disable_fields()
        self._refresh_recent_operators()

        src_path = os.path.join(ConfigManager.get_server_path(), saida)
        dst_path = os.path.join(ConfigManager.get_saidas_cnc_path(), saida)
        
        # Garante que a pasta local de destino exista
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)

        self.progress_win = ProgressDialog(self, title="Copiando arquivo CNC...", max_val=0)
        self.active_runner = FileOperationRunner("COPY", src_path, dst_path,
                                                 lambda e: self.on_file_op_finished(e, "INICIADO"))
        self.active_runner.start()
        return True

    def handle_finalizar(self):
        dados = self.form_panel.get_data()
        saida = dados["saida"]
        if not saida:
            return

        # Ask for confirmation
        if not messagebox.askyesno("Confirmar Finalização", f"Tem certeza que deseja finalizar a saída '{saida}'?"):
            return

        self.end_time = datetime.now()
        self.elapsed_time = self.action_panel.get_elapsed_time_string()

        src_path = os.path.join(ConfigManager.get_saidas_cnc_path(), saida)
        dst_path = os.path.join(ConfigManager.get_saidas_cortadas_path(), saida)

        # Garante que a pasta de destino na rede/local exista
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)

        self.progress_win = ProgressDialog(self, title="Movendo arquivo CNC...", max_val=0)
        self.active_runner = FileOperationRunner("MOVE", src_path, dst_path,
                                                 lambda e: self.on_file_op_finished(e, "Corte Finalizado com sucesso!"))
        self.active_runner.start()

        self.after(700, self._refresh_recent_operators)

    def handle_open_pdf(self):
        saida = self.form_panel.get_data()["saida"]
        if not saida:
            return
        pdf_name = saida.replace(".cnc", ".pdf")
        self.progress_win = ProgressDialog(self, title="Procurando PDF na Rede...", max_val=0)
        search_path = ConfigManager.get_server_path()
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

    def _on_operator_changed(self, event=None):
        operator = self.form_panel.var_operador.get().strip()
        self.history_panel.set_operator(operator)

    def _refresh_recent_operators(self):
        operators = OperatorsManager.get_recent_operators(10)
        self.form_panel.update_operators(operators)
        
        if operators:
            # Seleciona o operador mais recente automaticamente
            self.form_panel.cbox_operador.current(0)
            # Força a atualização da variável para garantir que o _on_operator_changed receba o valor
            self.form_panel.var_operador.set(operators[0])
            self._on_operator_changed()

        # Carrega a visualização do histórico diário ao iniciar
        # Um pequeno delay garante que a interface gráfica esteja pronta antes de buscar os dados
        if hasattr(self.history_panel, 'refresh_history'):
            self.after(200, self.history_panel.refresh_history)

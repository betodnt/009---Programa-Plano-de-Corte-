import os
import sys
import threading
import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import messagebox, ttk

from core.application_service import ApplicationService
from core.config import ConfigManager
from core.file_ops import FileOperationRunner
from core.file_search_service import FileSearchService
from core.locks import LocksManager
from core.logging_service import LoggingService
from core.operation_service import OperationService
from core.operators import OperatorsManager
from core.search import SearchFilesRunner, SearchPdfRunner

from gui.action_panel import ActionPanel
from gui.config_dialog import ConfigDialog
from gui.form_panel import FormPanel
from gui.history_panel import HistoryPanel


class ProgressDialog(tk.Toplevel):
    def __init__(self, master, title="Aguarde...", max_val=0):
        super().__init__(master)
        self.title(title)
        self.geometry("300x100")
        self.resizable(False, False)
        self.configure(bg="#2b2b2b")
        self.transient(master)
        self.grab_set()

        self.lbl_texto = tk.Label(
            self,
            text="Aguarde...",
            bg="#2b2b2b",
            fg="#ffffff",
            font=("Segoe UI", 11),
            justify="center",
        )
        self.lbl_texto.pack(pady=(15, 10))

        mode = "determinate" if max_val > 0 else "indeterminate"
        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=250, mode=mode)
        if max_val > 0:
            self.progress["maximum"] = max_val
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
        self.progress["value"] = current

    def close(self):
        try:
            self.destroy()
        except Exception:
            pass


class AppWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Controle de Corte e Dobra")
        self.geometry("1120x640")
        self.minsize(1020, 600)

        ConfigManager.load_settings()

        self._setup_styles()
        self._build_ui()
        self._load_icon()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.active_runner = None
        self.progress_win = None
        self.active_operation_id = ""
        self.current_operation = None
        self.current_finish = None
        self._lock_heartbeat_stop = None
        self._lock_heartbeat_thread = None
        self._sync_in_progress = False

        self.after(500, self._refresh_recent_operators)
        self.after(1000, self._update_saidas_if_needed)
        self.after(1500, self._schedule_runtime_status)
        self.after(3000, self._schedule_pending_sync)

    def _update_saidas_if_needed(self):
        if self.form_panel._all_saidas and self.form_panel.cbox_saida.cget("state") == "readonly":
            threading.Thread(target=self._background_check_locks, daemon=True).start()

        self.after(5000, self._update_saidas_if_needed)

    def _background_check_locks(self):
        try:
            maquina = self.form_panel.var_maquina.get()
            locked_saidas = OperationService.get_locked_saidas(maquina)
            self.after_idle(lambda: self.form_panel.apply_locked_saidas_filter(locked_saidas))
        except Exception:
            pass

    def on_closing(self):
        if self.active_runner and self.active_runner.thread.is_alive():
            self.active_runner.cancel()
        self._stop_lock_heartbeat()
        LocksManager.release_all_locks_for_pid()
        LoggingService.write("application_closing", active_operation_id=self.active_operation_id)
        self.quit()
        sys.exit(0)

    def _start_lock_heartbeat(self, maquina, saida):
        self._stop_lock_heartbeat()
        stop_event = threading.Event()
        self._lock_heartbeat_stop = stop_event

        def _heartbeat():
            while not stop_event.wait(15):
                try:
                    if not LocksManager.touch_lock(maquina, saida):
                        break
                except Exception:
                    break

        self._lock_heartbeat_thread = threading.Thread(target=_heartbeat, daemon=True)
        self._lock_heartbeat_thread.start()

    def _stop_lock_heartbeat(self):
        if self._lock_heartbeat_stop:
            self._lock_heartbeat_stop.set()
        self._lock_heartbeat_stop = None
        self._lock_heartbeat_thread = None

    def _schedule_pending_sync(self):
        self._flush_pending_sync()
        self.after(15000, self._schedule_pending_sync)

    def _schedule_runtime_status(self):
        self._refresh_runtime_status()
        self.after(10000, self._schedule_runtime_status)

    def _refresh_runtime_status(self):
        status = ApplicationService.get_runtime_status()
        self.action_panel.set_status(status["summary"], status["level"])
        if status["queue_status"]["pending"] > 0:
            LoggingService.write("runtime_status_warning", status=status)

    def _flush_pending_sync(self):
        if self._sync_in_progress:
            return
        self._sync_in_progress = True

        def _worker():
            result = ApplicationService.flush_pending_sync()

            def _finish():
                self._sync_in_progress = False
                self._refresh_runtime_status()
                if result.get("synced", 0) > 0:
                    self.history_panel.refresh_history()
                    self.show_toast(f"{result['synced']} sincronizado(s)", duration=1500)

            self.after_idle(_finish)

        threading.Thread(target=_worker, daemon=True).start()

    def _setup_styles(self):
        style = ttk.Style(self)
        bg_dark = "#2b2b2b"
        bg_panel = "#2f3136"
        bg_field = "#3c3f41"
        fg_white = "#ffffff"
        fg_soft = "#d8d8d8"
        accent_blue = "#4a90e2"
        accent_green = "#27ae60"
        accent_red = "#c0392b"
        accent_timer = "#f39c12"

        self.configure(bg=bg_dark)
        style.theme_use("clam")

        style.configure("TFrame", background=bg_dark)
        style.configure("Panel.TFrame", background=bg_panel)
        style.configure("Inline.TFrame", background=bg_dark)
        style.configure("TLabel", background=bg_dark, foreground=fg_soft, font=("Segoe UI", 11))
        style.configure("Section.TLabel", background=bg_dark, foreground=fg_soft, font=("Segoe UI", 10, "bold"))
        style.configure("MachineValue.TLabel", background=bg_dark, foreground=fg_white, font=("Segoe UI", 28, "bold"))
        style.configure(
            "TEntry",
            fieldbackground=bg_field,
            foreground=fg_white,
            insertcolor=fg_white,
            borderwidth=1,
            relief="flat",
            padding=6,
        )
        style.configure(
            "TCombobox",
            fieldbackground=bg_field,
            foreground=fg_white,
            background=bg_field,
            arrowcolor=fg_white,
            borderwidth=1,
            relief="flat",
            padding=5,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", bg_field)],
            foreground=[("readonly", fg_white)],
            lightcolor=[("focus", accent_blue)],
            darkcolor=[("focus", accent_blue)],
        )
        style.configure(
            "TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(18, 8),
            background=bg_field,
            foreground=fg_white,
            borderwidth=1,
            relief="flat",
        )
        style.configure("Compact.TButton", font=("Segoe UI", 9, "bold"), padding=(12, 6), background=bg_field, foreground=fg_white)
        style.map(
            "TButton",
            background=[("active", "#4e5254")],
            foreground=[("active", fg_white)],
            relief=[("pressed", "groove"), ("!pressed", "flat")],
        )
        style.configure("Action.TButton", font=("Segoe UI", 12, "bold"), padding=(24, 12))
        style.configure("Iniciar.Action.TButton", background=accent_green, foreground="white", borderwidth=0)
        style.map("Iniciar.Action.TButton", background=[("active", "#2ecc71"), ("disabled", "#555555")])
        style.configure("Finalizar.Action.TButton", background=accent_red, foreground="white", borderwidth=0)
        style.map("Finalizar.Action.TButton", background=[("active", "#e74c3c"), ("disabled", "#555555")])
        style.configure("Timer.TLabel", foreground=accent_timer, font=("Segoe UI", 36, "bold"), background=bg_dark)
        style.configure("Treeview", background=bg_dark, foreground=fg_white, fieldbackground=bg_dark, borderwidth=0, rowheight=28, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=bg_field, foreground=fg_white, relief="flat", font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", accent_blue)])

        style.element_create("My.Vertical.Scrollbar.trough", "from", "default")
        style.element_create("My.Vertical.Scrollbar.thumb", "from", "default")
        style.layout(
            "My.Vertical.TScrollbar",
            [("My.Vertical.Scrollbar.trough", {"children": [("My.Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})], "sticky": "ns"})],
        )
        style.configure("My.Vertical.TScrollbar", background="#444444", troughcolor=bg_dark, borderwidth=0, arrowsize=0, width=8)
        style.map("My.Vertical.TScrollbar", background=[("active", "#555555"), ("pressed", "#666666")])

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
        except Exception as exc:
            print(f"Erro ao carregar icone: {exc}")

    def open_settings(self):
        config_win = ConfigDialog(self)
        self.wait_window(config_win)
        self.form_panel.update_machine_display()

    def _build_ui(self):
        main_container = ttk.Frame(self, padding=(12, 12, 12, 12))
        main_container.pack(fill="both", expand=True)
        main_container.columnconfigure(0, weight=3)
        main_container.columnconfigure(1, weight=7)
        main_container.rowconfigure(0, weight=1)

        history_card = ttk.Frame(main_container, style="Panel.TFrame")
        history_card.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        history_card.columnconfigure(0, weight=1)
        history_card.rowconfigure(0, weight=1)
        self.history_panel = HistoryPanel(history_card, ConfigManager.get_k8_data_path)
        self.history_panel.grid(row=0, column=0, sticky="nsew")

        right_panel = ttk.Frame(main_container)
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)
        right_panel.rowconfigure(1, weight=0)

        form_card = ttk.Frame(right_panel, style="Panel.TFrame")
        form_card.grid(row=0, column=0, sticky="nsew", pady=(0, 14))
        form_card.columnconfigure(0, weight=1)
        form_card.rowconfigure(0, weight=1)
        self.form_panel = FormPanel(form_card, self.handle_search, self.handle_open_pdf, self.open_settings)
        self.form_panel.grid(row=0, column=0, sticky="nsew")
        self.form_panel.cbox_operador.bind("<<ComboboxSelected>>", self._on_operator_changed)

        action_card = ttk.Frame(right_panel, style="Panel.TFrame")
        action_card.grid(row=1, column=0, sticky="ew")
        action_card.columnconfigure(0, weight=1)
        self.action_panel = ActionPanel(action_card, self.handle_iniciar, self.handle_finalizar)
        self.action_panel.grid(row=0, column=0, sticky="ew")

    def handle_search(self):
        dados = self.form_panel.get_data()
        request = FileSearchService.build_request(dados["pedido"], dados["tipo"])
        if not request.pedido:
            return

        ok, message = FileSearchService.validate_search(request)
        self.form_panel.update_saidas([])
        self.form_panel.disable_fields()
        self.action_panel.btn_iniciar.state(["disabled"])

        if not ok:
            LoggingService.write("search_validation_failed", pedido=request.pedido, tipo=request.tipo, message=message)
            messagebox.showwarning(
                "Caminho invalido",
                message,
            )
            self.form_panel.enable_fields()
            self.action_panel.btn_iniciar.state(["!disabled"])
            return

        self.progress_win = ProgressDialog(self, title="Buscando arquivos CNC...", max_val=0)
        LoggingService.write("search_started", pedido=request.pedido, tipo=request.tipo, base_path=request.base_path)
        self.active_runner = SearchFilesRunner(
            pedido=request.pedido,
            tipo=request.tipo,
            base_path=request.base_path,
            on_progress_update=self.on_search_progress,
            on_finished=self.on_search_finished,
        )
        self._check_runner_cancel()
        self.active_runner.start()

    def show_toast(self, message, duration=2000):
        toast = tk.Toplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        label = tk.Label(toast, text=message, bg="#34495e", fg="#ffffff", padx=60, pady=30, font=("Segoe UI", 36, "bold"))
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
            self.action_panel.btn_iniciar.state(["!disabled"])
            LoggingService.write("search_finished", total=len(results), results=results[:20])
            if not results and not (self.progress_win and self.progress_win.is_canceled):
                messagebox.showinfo("Aviso", "Nao foi encontrada nenhuma saida CNC para este pedido.")
            self.active_runner = None
            self.progress_win = None

        self.after_idle(finalize)

    def on_file_op_finished(self, err_msg, success_title):
        def finalize():
            if self.progress_win:
                self.progress_win.close()

            if err_msg:
                LoggingService.write("file_operation_failed", stage=success_title, error=err_msg, operation_id=self.active_operation_id)
                if success_title == "INICIADO":
                    dados = self.form_panel.get_data()
                    self._stop_lock_heartbeat()
                    OperationService.rollback_start(dados)
                    self.active_operation_id = ""
                    self.current_operation = None
                self.action_panel.stop_timer()
                self.action_panel.lbl_timer.config(text="00:00:00")
                self.form_panel.enable_fields()
                self.action_panel.btn_iniciar.state(["!disabled"])
                self.action_panel.btn_finalizar.state(["disabled"])
                messagebox.showwarning("Aviso de Rede", err_msg)
            else:
                LoggingService.write("file_operation_finished", stage=success_title, operation_id=self.active_operation_id)
                if success_title == "INICIADO":
                    dados = self.form_panel.get_data()
                    feedback = OperationService.complete_start(dados, self.current_operation)
                    if feedback.level == "warning":
                        messagebox.showwarning(feedback.dialog_title, feedback.dialog_message)
                    self.show_toast("Corte Iniciado!")
                    if feedback.nif_path:
                        webbrowser.open(f"file://{feedback.nif_path}")
                else:
                    dados = self.form_panel.get_data()
                    self._stop_lock_heartbeat()
                    feedback = OperationService.complete_finish(dados, self.current_finish, success_title)
                    self.active_operation_id = ""
                    self.current_operation = None
                    self.current_finish = None
                    self.form_panel.update_saidas(self.form_panel._all_saidas)
                    self.history_panel.current_operator = dados["operador"]
                    self.history_panel.refresh_history()
                    self.form_panel.enable_fields()
                    self.action_panel.btn_iniciar.state(["!disabled"])
                    self.action_panel.btn_finalizar.state(["disabled"])
                    self.action_panel.lbl_timer.config(text="00:00:00")
                    if feedback.level == "info":
                        messagebox.showinfo(feedback.dialog_title, feedback.dialog_message)
                    else:
                        messagebox.showwarning(feedback.dialog_title, feedback.dialog_message)

            self.active_runner = None
            self.progress_win = None

        self.after_idle(finalize)

    def handle_iniciar(self):
        dados = self.form_panel.get_data()
        if not dados["saida"]:
            return False

        operation_start, message = OperationService.prepare_start(dados)
        if not operation_start:
            if "ja esta sendo usada" in message:
                messagebox.showwarning("Saida Indisponivel", message)
            elif "Informe o nome do operador" in message:
                messagebox.showwarning("Operador obrigatorio", message)
            else:
                messagebox.showerror("Erro de Rede", message)
            return False

        self.current_operation = operation_start
        self.start_time = operation_start.start_time
        self.active_operation_id = operation_start.operation_id
        LoggingService.write("start_clicked", operation_id=self.active_operation_id, data=dados)
        self._start_lock_heartbeat(dados["maquina"], dados["saida"])

        self.form_panel.disable_fields()
        self._refresh_recent_operators()

        self.progress_win = ProgressDialog(self, title="Copiando arquivo CNC...", max_val=0)
        self.active_runner = FileOperationRunner(
            "COPY",
            operation_start.src_path,
            operation_start.dst_path,
            lambda err: self.on_file_op_finished(err, "INICIADO"),
        )
        self.active_runner.start()
        return True

    def handle_finalizar(self):
        dados = self.form_panel.get_data()
        saida = dados["saida"]
        if not saida:
            return

        if not messagebox.askyesno("Confirmar Finalizacao", f"Tem certeza que deseja finalizar a saida '{saida}'?"):
            return

        self.end_time = datetime.now()
        self.elapsed_time = self.action_panel.get_elapsed_time_string()
        LoggingService.write("finish_clicked", operation_id=self.active_operation_id, data=dados, elapsed_time=self.elapsed_time)
        self.current_finish = OperationService.prepare_finish(dados, self.active_operation_id, self.elapsed_time)
        if not self.current_finish:
            return

        self.progress_win = ProgressDialog(self, title="Movendo arquivo CNC...", max_val=0)
        self.active_runner = FileOperationRunner(
            "MOVE",
            self.current_finish.src_path,
            self.current_finish.dst_path,
            lambda err: self.on_file_op_finished(err, "Corte Finalizado com sucesso!"),
        )
        self.active_runner.start()

        self.after(700, self._refresh_recent_operators)

    def handle_open_pdf(self):
        saida = self.form_panel.get_data()["saida"]
        if not saida:
            return

        pdf_name = saida.replace(".cnc", ".pdf")
        self.progress_win = ProgressDialog(self, title="Procurando PDF na Rede...", max_val=0)
        search_path = ConfigManager.get_server_path()
        LoggingService.write("pdf_search_started", pdf_name=pdf_name, search_path=search_path)
        self.active_runner = SearchPdfRunner(pdf_name, search_path, self.on_pdf_search_finished)
        self._check_runner_cancel()
        self.active_runner.start()

    def on_pdf_search_finished(self, found_path):
        def finalize():
            if self.progress_win:
                self.progress_win.close()
            if not found_path and not (self.progress_win and self.progress_win.is_canceled):
                LoggingService.write("pdf_search_not_found", pdf_name=self.form_panel.get_data()["saida"].replace(".cnc", ".pdf"))
                messagebox.showwarning("Nao Encontrado", "O arquivo PDF correspondente nao foi encontrado na base.")
            elif found_path:
                LoggingService.write("pdf_search_found", found_path=found_path)
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
            self.form_panel.cbox_operador.current(0)
            self.form_panel.var_operador.set(operators[0])
            self._on_operator_changed()

        if hasattr(self.history_panel, "refresh_history"):
            self.after(200, self.history_panel.refresh_history)

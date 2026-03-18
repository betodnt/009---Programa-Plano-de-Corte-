import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import webbrowser
from datetime import datetime
import xml.etree.ElementTree as ET
import sys

from core.config import ConfigManager
from core.database import DatabaseManager
from core.search import SearchFilesRunner, SearchPdfRunner
from core.file_ops import FileOperationRunner
from core.operators import OperatorsManager
from core.locks import LocksManager

from gui.form_panel import FormPanel
from gui.action_panel import ActionPanel
from gui.history_panel import HistoryPanel

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
        
        self.btn_close = ttk.Button(self, text="Fechar", command=self.on_close)
        self.btn_close.pack(pady=(0, 5))
        
        self.is_canceled = False
        
        # Center on parent
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - (self.winfo_width() // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        # Remove modal
        # self.transient(master)
        # self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_cancel(self):
        self.lbl_texto.config(text="Cancelando Busca...")
        self.btn_cancel.config(state="disabled")
        self.is_canceled = True

    def on_close(self):
        self.destroy()

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
        self.geometry("1000x550") # Increased width for the new panel
        
        ConfigManager.load_settings()
        
        self._setup_styles()
        self._build_ui()
        self._load_icon()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.active_runner = None
        self.progress_win = None
        
        # Initial population of operator suggestions
        self.after(500, self._refresh_recent_operators)
        
        # Atualização periódica dos locks (a cada 5 segundos)
        self.after(1000, self._update_saidas_if_needed)

    def _update_saidas_if_needed(self):
        """Atualiza lista de saídas se houver mudanças nos locks"""
        try:
            # Só atualiza se há saídas no dropdown e campos estão habilitados
            current_saidas = self.form_panel.cbox_saida['values']
            if current_saidas and self.form_panel.cbox_saida.cget('state') == 'readonly':
                # Refaz a filtragem com locks atuais
                self.form_panel.update_saidas(list(current_saidas))
        except:
            pass  # Ignora erros para não quebrar a aplicação
        
        # Agenda próxima atualização em 5 segundos
        self.after(5000, self._update_saidas_if_needed)

    def on_closing(self):
        # Ensure all background processes are stopped
        if self.active_runner and self.active_runner.thread.is_alive():
            self.active_runner.cancel()
        self.quit()
        sys.exit(0)

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
        style.theme_use('clam') 
        
        # Estilo de Quadros (Frames)
        style.configure("TFrame", background=bg_dark)
        
        # Estilo de Labels
        style.configure("TLabel", background=bg_dark, foreground="#e0e0e0", font=("Segoe UI", 11))
        
        # Estilo de Campos de Entrada e Combobox (Refinado)
        style.configure("TEntry", 
            fieldbackground=bg_field, 
            foreground=fg_white, 
            insertcolor=fg_white,
            borderwidth=1,
            relief="flat",
            padding=5
        )
        
        style.configure("TCombobox", 
            fieldbackground=bg_field, 
            foreground=fg_white, 
            background=bg_field,
            arrowcolor=fg_white,
            borderwidth=1,
            relief="flat",
            padding=4
        )
        style.map("TCombobox", 
            fieldbackground=[('readonly', bg_field)], 
            foreground=[('readonly', fg_white)],
            lightcolor=[('focus', accent_blue)],
            darkcolor=[('focus', accent_blue)]
        )

        # Botão Padrão (Moderno e mais arredondado)
        style.configure("TButton", 
            font=("Segoe UI", 10, "bold"), 
            padding=(20, 8), 
            background=bg_field, 
            foreground=fg_white, 
            borderwidth=1, 
            relief="flat"
        )
        style.map("TButton", 
            background=[('active', "#4e5254")], 
            foreground=[('active', fg_white)],
            relief=[('pressed', 'groove'), ('!pressed', 'flat')]
        )
        
        # Botões de Ação (Mais robustos e suaves)
        style.configure("Action.TButton", font=("Segoe UI", 12, "bold"), padding=(25, 12))
        
        # Iniciar (Verde)
        style.configure("Iniciar.Action.TButton", background=accent_green, foreground="white", borderwidth=0)
        style.map("Iniciar.Action.TButton", background=[('active', "#2ecc71"), ('disabled', "#555555")])
        
        # Finalizar (Vermelho)
        style.configure("Finalizar.Action.TButton", background=accent_red, foreground="white", borderwidth=0)
        style.map("Finalizar.Action.TButton", background=[('active', "#e74c3c"), ('disabled', "#555555")])

        # Fim de Turno (Laranja)
        style.configure("FimTurno.Action.TButton", background="#f39c12", foreground="white", font=("Segoe UI", 11, "bold"), borderwidth=0)
        style.map("FimTurno.Action.TButton", background=[('active', "#e67e22"), ('disabled', "#555555")])
        
        # Timer (Label especial)
        style.configure("Timer.TLabel", foreground=accent_timer, font=("Segoe UI", 36, "bold"), background=bg_dark)

        # Style for Treeview (History)
        style.configure("Treeview", 
            background=bg_dark, 
            foreground=fg_white, 
            fieldbackground=bg_dark, 
            borderwidth=0,
            font=("Segoe UI", 10)
        )
        style.configure("Treeview.Heading", 
            background=bg_field, 
            foreground=fg_white, 
            relief="flat",
            font=("Segoe UI", 10, "bold")
        )
        style.map("Treeview", background=[('selected', accent_blue)])

        # Scrollbar Styling
        style.element_create("My.Vertical.Scrollbar.trough", "from", "default")
        style.element_create("My.Vertical.Scrollbar.thumb", "from", "default")
        
        style.layout("My.Vertical.TScrollbar", [
            ('My.Vertical.Scrollbar.trough', {
                'children': [
                    ('My.Vertical.Scrollbar.thumb', {'expand': '1', 'sticky': 'nswe'})
                ],
                'sticky': 'ns'
            })
        ])

        style.configure("My.Vertical.TScrollbar", 
            background="#444444", 
            troughcolor=bg_dark, 
            borderwidth=0, 
            arrowsize=0,
            width=8
        )
        style.map("My.Vertical.TScrollbar", 
            background=[('active', "#555555"), ('pressed', "#666666")]
        )

    def _load_icon(self):
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon.png")
        if os.path.exists(icon_path):
            try:
                self.icon_photo = tk.PhotoImage(file=icon_path)
                self.iconphoto(False, self.icon_photo)
                # Também definir para a barra de tarefas no Windows
                try:
                    self.iconbitmap(icon_path)
                except:
                    pass  # Ignorar se não for .ico
            except Exception as e:
                print(f"Erro ao carregar ícone: {e}")


    def _create_menu(self):
        menubar = tk.Menu(self)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Salvar Cópia XML", command=self.save_xml_copy)
        
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        
        self.config(menu=menubar)

    def save_xml_copy(self):
        xml_path = ConfigManager.get_k8_data_path()
        if not os.path.exists(xml_path):
            messagebox.showinfo("Aviso", "Não há dados para copiar.")
            return
        
        save_path = filedialog.asksaveasfilename(
            defaultextension=".xml",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
            title="Salvar Cópia do XML"
        )
        
        if save_path:
            try:
                import shutil
                shutil.copy2(xml_path, save_path)
                messagebox.showinfo("Sucesso", f"Cópia salva em: {save_path}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar cópia: {e}")

    def _build_ui(self):
        self._create_menu()
        
        main_container = ttk.Frame(self, padding="20")
        main_container.pack(fill="both", expand=True)
        
        # Left Panel: History (Slimmer width)
        self.history_panel = HistoryPanel(main_container, ConfigManager.get_k8_data_path, width=280)
        self.history_panel.pack(side="left", fill="both", expand=False, padx=(0, 20))
        
        # Right Panel: Operations
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side="right", fill="both", expand=True)
        
        self.form_panel = FormPanel(right_panel, self.handle_search, self.handle_open_pdf)
        self.form_panel.pack(fill="x", pady=(0, 20))
        
        # Stretch space
        spacer = ttk.Frame(right_panel)
        spacer.pack(fill="both", expand=True)
        
        self.action_panel = ActionPanel(right_panel, self.handle_iniciar, self.handle_finalizar)
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
        
        base_path = ConfigManager.get_server_path()
        if not os.path.exists(base_path):
            messagebox.showwarning(
                "Caminho inválido",
                f"O diretório base para as saídas CNC não existe:\n{base_path}\n\nVerifique as configurações em config.ini."
            )
            self.form_panel.enable_fields()
            self.action_panel.btn_iniciar.state(['!disabled'])
            return
        
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
        
    def show_toast(self, message, duration=2000):
        """Displays a non-blocking temporary message."""
        toast = tk.Toplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        
        # Style (3x larger as requested)
        bg_color = "#34495e"
        fg_color = "#ffffff"
        label = tk.Label(toast, text=message, bg=bg_color, fg=fg_color, 
                         padx=60, pady=30, font=("Segoe UI", 36, "bold"))
        label.pack()
        
        # Center relative to self
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (label.winfo_reqwidth() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (label.winfo_reqheight() // 2)
        toast.geometry(f"+{x}+{y}")
        
        # Auto-close
        self.after(duration, toast.destroy)

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

    def on_file_op_finished(self, err_msg, success_title):
        def finalize():
            if self.progress_win:
                self.progress_win.close()
            
            # Se foi finalizado com sucesso, libera o lock
            if not err_msg and success_title == "Corte Finalizado com sucesso!":
                dados = self.form_panel.get_data()
                LocksManager.release_lock(dados["maquina"], dados["saida"])
                
            if "Corte Finalizado" in success_title and not err_msg:
                self.form_panel.enable_fields()
                self.action_panel.btn_iniciar.state(['!disabled'])
                self.action_panel.btn_finalizar.state(['disabled'])
            elif err_msg:
                 # If it failed to start, revert ui and release lock if iniciado failed
                 if success_title == "INICIADO":
                     dados = self.form_panel.get_data()
                     LocksManager.release_lock(dados["maquina"], dados["saida"])
                 
                 self.action_panel.stop_timer()
                 self.form_panel.enable_fields()
                 self.action_panel.lbl_timer.config(text="00:00:00")
            
            if err_msg:
                messagebox.showwarning("Aviso de Rede", err_msg)
            else:
                if success_title == "INICIADO":
                    self.show_toast("Corte Iniciado!")
                    # Abrir o arquivo .nif correspondente
                    saida = self.form_panel.get_data()["saida"]
                    if saida:
                        nif_name = saida.replace(".cnc", ".nif")
                        nif_path = os.path.join(ConfigManager.get_server_path(), nif_name)
                        if os.path.exists(nif_path):
                            webbrowser.open(f"file://{nif_path}")
                else:
                    messagebox.showinfo("Sucesso", success_title)
                    # Reset timer only on successful finalization
                    if "Finalizado" in success_title:
                        self.action_panel.lbl_timer.config(text="00:00:00")
                
            self.active_runner = None
            self.progress_win = None
        self.after_idle(finalize)

    def handle_iniciar(self):
        saida = self.form_panel.get_data()["saida"]
        if not saida: return False
        
        dados = self.form_panel.get_data()
        
        # Verifica se a combinação máquina+saída já está bloqueada por outra instância
        if LocksManager.is_locked(dados["maquina"], saida):
            messagebox.showwarning("Saída Indisponível", 
                f"A saída '{saida}' já está sendo usada por outro operador na máquina '{dados['maquina']}'.\n\nEscolha outra saída ou aguarde a finalização.")
            return False
        
        dt_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        file_path = ConfigManager.get_k8_data_path()
        
        sucesso, erro = DatabaseManager.save_entrada(
            file_path, dados["pedido"], dados["operador"], dados["maquina"],
            dados["retalho"], saida, dados["tipo"], dt_inicio
        )
        
        if not sucesso:
            messagebox.showwarning("Erro", erro)
            return False
        
        # Salva operador no histórico persistente
        OperatorsManager.add_operator(dados["operador"])
        
        # Adquire lock para máquina + saída
        LocksManager.acquire_lock(dados["maquina"], saida)
            
        self.form_panel.disable_fields()
        self._refresh_recent_operators() # Update on start too
        
        # Cópia do arquivo
        src_path = os.path.join(ConfigManager.get_server_path(), saida)
        dst_path = os.path.join(ConfigManager.get_saidas_cnc_path(), saida)
        
        self.progress_win = ProgressDialog(self, title="Copiando arquivo CNC...", max_val=0)
        
        self.active_runner = FileOperationRunner("COPY", src_path, dst_path, lambda e: self.on_file_op_finished(e, "INICIADO"))
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
        
        # Refresh history after a small delay to ensure XML is written
        self.after(500, self.history_panel.refresh_history)
        self.after(600, self._refresh_recent_operators)

    def handle_open_pdf(self):
        saida = self.form_panel.get_data()["saida"]
        if not saida: return
        
        pdf_name = saida.split("_S")[0] + ".pdf"
        
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

    def _refresh_recent_operators(self):
        """Finds the last 3 unique operators from recent history and XML files."""
        operators = []
        
        # 1. Primeiro tenta os operadores salvos no histórico persistente
        persistent_operators = OperatorsManager.get_recent_operators(3)
        operators.extend(persistent_operators)
        
        # 2. Se precisar mais, tenta dos XMLs recentes
        if len(operators) < 3:
            xml_path = ConfigManager.get_k8_data_path()
            if os.path.exists(xml_path):
                self._extract_operators_from_file(xml_path, operators)
            
            # 3. Se ainda precisar mais, escaneia diretório
            if len(operators) < 3:
                data_dir = os.path.dirname(xml_path)
                if os.path.exists(data_dir):
                    files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.startswith("dados_") and f.endswith(".xml")]
                    files.sort(key=os.path.getmtime, reverse=True)
                    
                    for f in files:
                        if f == xml_path: continue
                        self._extract_operators_from_file(f, operators)
                        if len(operators) >= 3:
                            break
        
        self.form_panel.update_operators(operators[:3])

    def _extract_operators_from_file(self, file_path, operators_list):
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            current_pid = str(os.getpid())
            for entrada in reversed(root.findall("Entrada")):
                instancia = entrada.findtext("Instancia", "")
                if instancia != current_pid:
                    continue
                op = entrada.findtext("Operador", "")
                if op and op not in operators_list:
                    operators_list.append(op)
                    if len(operators_list) >= 10: # limit scan
                        break
        except Exception:
            pass

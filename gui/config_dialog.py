import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from core.config import ConfigManager

class ConfigDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Login - Acesso Restrito")
        self.geometry("350x200")
        self.resizable(False, False)
        
        # Torna a janela modal
        self.transient(master)
        self.grab_set()

        self.configure(bg="#2b2b2b")
        
        # Carrega configurações atuais
        self.current_settings = ConfigManager.get_all_settings()
        
        self.entries = {}
        
        self._build_login_ui()
        
        # Centralizar a janela
        self._center_window(master)

    def _center_window(self, master):
        self.update_idletasks()
        try:
            x = master.winfo_x() + (master.winfo_width() // 2) - (self.winfo_width() // 2)
            y = master.winfo_y() + (master.winfo_height() // 2) - (self.winfo_height() // 2)
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

    def _build_login_ui(self):
        self.login_frame = ttk.Frame(self, padding="20")
        self.login_frame.pack(fill="both", expand=True)
        
        style = ttk.Style()
        style.configure("Login.TLabel", background="#2b2b2b", foreground="#ffffff", font=("Segoe UI", 10))
        
        # Título
        lbl = ttk.Label(self.login_frame, text="Autenticação Necessária", font=("Segoe UI", 12, "bold"), background="#2b2b2b", foreground="#ffffff")
        lbl.pack(pady=(0, 20))

        # Campos
        frm_fields = ttk.Frame(self.login_frame)
        frm_fields.pack(fill="x", pady=5)
        
        ttk.Label(frm_fields, text="Usuário:", style="Login.TLabel", width=10).grid(row=0, column=0, sticky="w", pady=5)
        self.ent_user = ttk.Entry(frm_fields)
        self.ent_user.grid(row=0, column=1, sticky="ew", pady=5)
        
        ttk.Label(frm_fields, text="Senha:", style="Login.TLabel", width=10).grid(row=1, column=0, sticky="w", pady=5)
        
        # Frame container para senha e botão de olho
        frm_pass = ttk.Frame(frm_fields)
        frm_pass.grid(row=1, column=1, sticky="ew", pady=5)
        frm_pass.columnconfigure(0, weight=1)
        
        self.ent_pass = ttk.Entry(frm_pass, show="*")
        self.ent_pass.grid(row=0, column=0, sticky="ew")
        
        # Botão para alternar visibilidade (usando tk.Button para estilização mais fácil do background)
        self.btn_eye = tk.Button(frm_pass, text="👁", width=3, cursor="hand2",
                                 command=self._toggle_password_visibility,
                                 relief="flat", bg="#3c3f41", fg="white",
                                 activebackground="#505355", activeforeground="white",
                                 font=("Segoe UI", 10))
        self.btn_eye.grid(row=0, column=1, padx=(5, 0))
        
        frm_fields.columnconfigure(1, weight=1)
        
        self.ent_pass.bind('<Return>', lambda e: self._attempt_login())
        self.ent_user.focus()

        # Botões
        btn_frame = ttk.Frame(self.login_frame)
        btn_frame.pack(fill="x", pady=(20, 0))
        
        btn_login = ttk.Button(btn_frame, text="Entrar", command=self._attempt_login)
        btn_login.pack(side="right", padx=5)
        btn_cancel = ttk.Button(btn_frame, text="Cancelar", command=self.destroy)
        btn_cancel.pack(side="right")

    def _toggle_password_visibility(self):
        if self.ent_pass.cget('show') == '*':
            self.ent_pass.config(show='')
            self.btn_eye.config(text="🔒") # Ícone indicando que está visível (clique para bloquear/esconder)
        else:
            self.ent_pass.config(show='*')
            self.btn_eye.config(text="👁")

    def _attempt_login(self):
        u = self.ent_user.get().strip()
        p = self.ent_pass.get().strip()
        
        valid_user, valid_pass = ConfigManager.get_admin_credentials()
        
        if u == valid_user and p == valid_pass:
            self.login_frame.destroy()
            self._init_config_screen()
        else:
            messagebox.showerror("Acesso Negado", "Usuário ou senha incorretos.", parent=self)
            self.ent_pass.delete(0, 'end')
            self.ent_pass.focus()

    def _init_config_screen(self):
        self.title("Configurações de Diretórios")
        self.geometry("700x800")
        self.resizable(False, True)
        self._build_ui()
        self._center_window(self.master)

    def _build_ui(self):
        # Botões do rodapé sempre presos no fundo
        btn_frame = ttk.Frame(self, padding="10")
        btn_frame.pack(side="bottom", fill="x")
        
        btn_save = ttk.Button(btn_frame, text="Salvar", command=self._save_settings)
        btn_save.pack(side="right", padx=(10, 0))
        
        btn_cancel = ttk.Button(btn_frame, text="Cancelar", command=self.destroy)
        btn_cancel.pack(side="right")

        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(side="top", fill="both", expand=True)

        lbl_title = ttk.Label(main_frame, text="Configurar caminho", font=("Segoe UI", 16, "bold"), justify="center", anchor="center")
        lbl_title.pack(pady=(0, 20), anchor="center")

        # Definição dos campos para a interface
        fields = [
            ("acervosaidascnc", "Caminho do Servidor (Acervo CNC):", "Pasta onde estão os arquivos originais (.cnc)"),
            ("saidascnc", "Pasta Local (Saídas CNC):", "Pasta temporária para onde são copiados os arquivos a cortar"),
            ("saidascortadas", "Saídas Cortadas:", "Pasta para onde os arquivos vão após o término do corte"),
            ("dadosxml", "Caminho do Banco XML:", "Arquivo de banco de dados (ex: .../dados_{date}.xml)"),
            ("planocorte", "Plano de Corte (PDFs):", "Pasta base onde estão os PDFs"),
            ("current_machine", "Máquina Atual:", "Selecione a máquina que será usada no aplicativo"),
            ("available_machines", "Máquinas Disponíveis:", "Lista de máquinas separadas por vírgula (ex: Bodor1 (12K), Bodor2 (6K))")
        ]

        grid_frame = ttk.Frame(main_frame)
        grid_frame.pack(fill="x", expand=True)
        grid_frame.columnconfigure(0, weight=1)

        for i, (key, label_text, tooltip) in enumerate(fields):
            # Label para o título do campo
            lbl = ttk.Label(grid_frame, text=label_text, font=("Segoe UI", 10, "bold"))
            lbl.grid(row=i*3, column=0, sticky="w", pady=(10, 0))
            
            if key == "current_machine":
                # Combobox para seleção da máquina atual
                available_machines = ConfigManager.get_available_machines()
                current_machine = ConfigManager.get_current_machine()
                machine_var = tk.StringVar(value=current_machine)
                machine_combo = ttk.Combobox(grid_frame, textvariable=machine_var, values=available_machines, state="readonly", width=47)
                machine_combo.grid(row=i*3+1, column=0, sticky="ew", pady=(2, 5), padx=(0, 10))
                self.entries[key.lower()] = machine_var
            else:
                # Entry para o caminho
                entry_var = tk.StringVar()
                # Pega o valor atual (ignora case insensitive pois o configparser salva chave minúscula por padrão)
                val = self.current_settings.get(key.lower(), self.current_settings.get(key, ""))
                entry_var.set(val)
                
                entry = ttk.Entry(grid_frame, textvariable=entry_var, width=50)
                entry.grid(row=i*3+1, column=0, sticky="ew", pady=(2, 5), padx=(0, 10))
                
                # Mapeia a variável pelo nome da chave para salvar depois
                self.entries[key.lower()] = entry_var

            # Botão de procurar (só para caminhos, não para máquina)
            if key not in ["current_machine", "available_machines"]:
                btn_browse = ttk.Button(grid_frame, text="Procurar...", width=12,
                                        command=lambda k=key.lower(): self._browse_path(k))
                btn_browse.grid(row=i*3+1, column=1, pady=(2, 5))
            
            # Label de dica explicativa
            lbl_tip = ttk.Label(grid_frame, text=tooltip, font=("Segoe UI", 8), foreground="#aaaaaa")
            lbl_tip.grid(row=i*3+2, column=0, columnspan=2, sticky="w", pady=(0, 5))

    def _browse_path(self, key):
        initial_dir = self.entries[key].get()
        
        if key == "dadosxml": # Tratamento especial caso o usuário queira escolher um arquivo que já existe ou definir a pasta
            file_path = filedialog.asksaveasfilename(
                parent=self,
                title="Selecione ou digite o nome do XML",
                initialdir=initial_dir if "{" not in initial_dir else "",
                defaultextension=".xml",
                filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
            )
            if file_path:
                self.entries[key].set(file_path)
        else:
            folder_path = filedialog.askdirectory(parent=self, title="Selecione a Pasta", initialdir=initial_dir)
            if folder_path:
                # Converter barras para o padrão do SO se necessário, mas o Python e o ConfigManager lidam com as duas
                # Para ser consistente, vamos gravar no formato de string raw
                self.entries[key].set(folder_path)

    def _save_settings(self):
        new_settings = {}
        for key, var in self.entries.items():
            new_val = var.get().strip()
            # Permitir que current_machine e available_machines estejam vazios (usarão padrão)
            if not new_val and key not in ["current_machine", "available_machines"]:
                messagebox.showwarning("Aviso", f"O campo associado à chave '{key}' não pode estar vazio.", parent=self)
                return
            new_settings[key] = new_val

        try:
            ConfigManager.save_settings(new_settings)
            messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!", parent=self)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao salvar as configurações:\n{e}", parent=self)

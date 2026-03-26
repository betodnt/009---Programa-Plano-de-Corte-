import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core.application_service import ApplicationService
from core.config import ConfigManager


class ConfigDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Login - Acesso Restrito")
        self.geometry("350x200")
        self.resizable(False, False)

        self.transient(master)
        self.grab_set()
        self.configure(bg="#2b2b2b")

        self.current_settings = ConfigManager.get_all_settings()
        self.entries = {}

        self._build_login_ui()
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

        lbl = ttk.Label(
            self.login_frame,
            text="Autenticacao Necessaria",
            font=("Segoe UI", 12, "bold"),
            background="#2b2b2b",
            foreground="#ffffff",
        )
        lbl.pack(pady=(0, 20))

        frm_fields = ttk.Frame(self.login_frame)
        frm_fields.pack(fill="x", pady=5)

        ttk.Label(frm_fields, text="Usuario:", style="Login.TLabel", width=10).grid(row=0, column=0, sticky="w", pady=5)
        self.ent_user = ttk.Entry(frm_fields)
        self.ent_user.grid(row=0, column=1, sticky="ew", pady=5)

        ttk.Label(frm_fields, text="Senha:", style="Login.TLabel", width=10).grid(row=1, column=0, sticky="w", pady=5)

        frm_pass = ttk.Frame(frm_fields)
        frm_pass.grid(row=1, column=1, sticky="ew", pady=5)
        frm_pass.columnconfigure(0, weight=1)

        self.ent_pass = ttk.Entry(frm_pass, show="*")
        self.ent_pass.grid(row=0, column=0, sticky="ew")

        self.btn_eye = tk.Button(
            frm_pass,
            text="👁",
            width=3,
            cursor="hand2",
            command=self._toggle_password_visibility,
            relief="flat",
            bg="#3c3f41",
            fg="white",
            activebackground="#505355",
            activeforeground="white",
            font=("Segoe UI", 10),
        )
        self.btn_eye.grid(row=0, column=1, padx=(5, 0))

        frm_fields.columnconfigure(1, weight=1)

        self.ent_pass.bind("<Return>", lambda _e: self._attempt_login())
        self.ent_user.focus()

        btn_frame = ttk.Frame(self.login_frame)
        btn_frame.pack(fill="x", pady=(20, 0))

        ttk.Button(btn_frame, text="Entrar", command=self._attempt_login).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="right")

    def _toggle_password_visibility(self):
        if self.ent_pass.cget("show") == "*":
            self.ent_pass.config(show="")
            self.btn_eye.config(text="🔒")
        else:
            self.ent_pass.config(show="*")
            self.btn_eye.config(text="👁")

    def _attempt_login(self):
        user = self.ent_user.get().strip()
        password = self.ent_pass.get().strip()

        valid_user, valid_pass = ConfigManager.get_admin_credentials()
        if user == valid_user and password == valid_pass:
            self.login_frame.destroy()
            self._init_config_screen()
            return

        messagebox.showerror("Acesso Negado", "Usuario ou senha incorretos.", parent=self)
        self.ent_pass.delete(0, "end")
        self.ent_pass.focus()

    def _init_config_screen(self):
        self.title("Configuracoes de Diretorios")
        self.geometry("760x860")
        self.resizable(False, True)
        self._build_ui()
        self._center_window(self.master)

    def _build_ui(self):
        btn_frame = ttk.Frame(self, padding="10")
        btn_frame.pack(side="bottom", fill="x")

        ttk.Button(btn_frame, text="Salvar", command=self._save_settings).pack(side="right", padx=(10, 0))
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="right")
        ttk.Button(btn_frame, text="Diagnostico", command=self._show_diagnostics).pack(side="left")

        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(side="top", fill="both", expand=True)

        ttk.Label(
            main_frame,
            text="Configurar caminhos locais e de rede",
            font=("Segoe UI", 16, "bold"),
            justify="center",
            anchor="center",
        ).pack(pady=(0, 20), anchor="center")

        fields = [
            ("acervosaidascnc", "Acervo CNC na rede:", "Pasta UNC com os arquivos .cnc originais."),
            ("saidascnc", "Saidas CNC locais:", "Pasta local da maquina. Aceita {machine}."),
            ("saidascortadas", "Saidas cortadas:", "Destino final dos arquivos apos o corte."),
            ("dadosxml", "Banco XML compartilhado:", "Arquivo na rede. Aceita {date}."),
            ("locksfile", "Arquivo de locks compartilhado:", "Arquivo JSON unico na rede para coordenacao entre maquinas."),
            ("offlinequeuedir", "Fila offline local:", "Pasta local para contingencia quando a rede cair. Aceita {machine}."),
            ("planocorte", "Plano de corte (PDFs):", "Pasta base dos PDFs."),
            ("machine_name", "Nome da maquina:", "Nome exibido na tela principal quando PCP_MACHINE_ID nao estiver definido."),
            ("current_machine", "Maquina atual:", "Fallback usado quando PCP_MACHINE_ID nao estiver definido."),
            ("available_machines", "Maquinas disponiveis:", "Lista separada por virgula."),
        ]

        grid_frame = ttk.Frame(main_frame)
        grid_frame.pack(fill="x", expand=True)
        grid_frame.columnconfigure(0, weight=1)

        for i, (key, label_text, tooltip) in enumerate(fields):
            ttk.Label(grid_frame, text=label_text, font=("Segoe UI", 10, "bold")).grid(
                row=i * 3, column=0, sticky="w", pady=(10, 0)
            )

            if key == "current_machine":
                available_machines = ConfigManager.get_available_machines()
                machine_var = tk.StringVar(value=ConfigManager.get_current_machine())
                machine_combo = ttk.Combobox(
                    grid_frame,
                    textvariable=machine_var,
                    values=available_machines,
                    state="readonly",
                    width=55,
                )
                machine_combo.grid(row=i * 3 + 1, column=0, sticky="ew", pady=(2, 5), padx=(0, 10))
                self.entries[key] = machine_var
            else:
                entry_var = tk.StringVar()
                entry_var.set(self.current_settings.get(key.lower(), self.current_settings.get(key, "")))

                ttk.Entry(grid_frame, textvariable=entry_var, width=60).grid(
                    row=i * 3 + 1, column=0, sticky="ew", pady=(2, 5), padx=(0, 10)
                )
                self.entries[key] = entry_var

            if key not in ["current_machine", "available_machines"]:
                ttk.Button(
                    grid_frame,
                    text="Procurar...",
                    width=12,
                    command=lambda k=key: self._browse_path(k),
                ).grid(row=i * 3 + 1, column=1, pady=(2, 5))

            ttk.Label(grid_frame, text=tooltip, font=("Segoe UI", 8), foreground="#aaaaaa").grid(
                row=i * 3 + 2, column=0, columnspan=2, sticky="w", pady=(0, 5)
            )

    def _browse_path(self, key):
        initial_dir = self.entries[key].get()

        if key in ["dadosxml", "locksfile"]:
            extension = ".xml" if key == "dadosxml" else ".json"
            filetypes = [("Arquivo configuravel", f"*{extension}"), ("All files", "*.*")]
            file_path = filedialog.asksaveasfilename(
                parent=self,
                title="Selecione ou digite o nome do arquivo",
                initialdir=initial_dir if "{" not in initial_dir else "",
                defaultextension=extension,
                filetypes=filetypes,
            )
            if file_path:
                self.entries[key].set(file_path)
            return

        folder_path = filedialog.askdirectory(parent=self, title="Selecione a pasta", initialdir=initial_dir)
        if folder_path:
            self.entries[key].set(folder_path)

    def _save_settings(self):
        new_settings = {}
        for key, var in self.entries.items():
            value = var.get().strip()
            if not value and key not in ["current_machine", "available_machines"]:
                messagebox.showwarning("Aviso", f"O campo '{key}' nao pode ficar vazio.", parent=self)
                return
            new_settings[key] = value

        try:
            ConfigManager.save_settings(new_settings)
            messagebox.showinfo("Sucesso", "Configuracoes salvas com sucesso.", parent=self)
            self.destroy()
        except Exception as exc:
            messagebox.showerror("Erro", f"Ocorreu um erro ao salvar as configuracoes:\n{exc}", parent=self)

    def _show_diagnostics(self):
        report = ApplicationService.get_diagnostics_report()
        messagebox.showinfo("Diagnostico do Sistema", report, parent=self)

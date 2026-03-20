import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.scrolledtext as st
from core.config import ConfigManager

class ConfigDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Configurações de Diretórios")
        self.geometry("700x680")
        self.resizable(False, False)
        
        # Make it modal
        self.transient(master)
        self.grab_set()

        self.configure(bg="#2b2b2b")
        
        # Carrega configurações atuais
        self.current_settings = ConfigManager.get_all_settings()
        
        self.entries = {}
        
        self._build_ui()
        
        # Centralizar a janela
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - (self.winfo_width() // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        # Botões do rodapé sempre presos no fundo
        btn_frame = ttk.Frame(self, padding="10")
        btn_frame.pack(side="bottom", fill="x")
        
        btn_save = ttk.Button(btn_frame, text="Salvar", command=self._save_settings)
        btn_save.pack(side="right", padx=(10, 0))
        
        btn_cancel = ttk.Button(btn_frame, text="Cancelar", command=self.destroy)
        btn_cancel.pack(side="right")

        # Criação das Abas
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        # Aba Geral
        self.tab_general = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(self.tab_general, text="Geral")
        self._setup_general_tab(self.tab_general)

        # Aba Logs
        self.tab_logs = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_logs, text="Logs do Sistema")
        self._setup_logs_tab(self.tab_logs)

    def _setup_general_tab(self, parent):
        lbl_title = ttk.Label(parent, text="Configurar caminhos", font=("Segoe UI", 16, "bold"), justify="center", anchor="center")
        lbl_title.pack(pady=(0, 20), anchor="center")

        grid_frame = ttk.Frame(parent)
        grid_frame.pack(fill="x", expand=True)

        # Definição dos campos para a interface
        fields = [
            ("acervosaidascnc", "Caminho do Servidor (Acervo CNC):", "Pasta onde estão os arquivos originais (.cnc)"),
            ("saidascnc", "Pasta Local (Saídas CNC):", "Pasta temporária para onde são copiados os arquivos a cortar"),
            ("saidascortadas", "Saídas Cortadas:", "Pasta para onde os arquivos vão após o término do corte"),
            ("dadosxml", "Caminho do Banco XML:", "Arquivo de banco de dados (ex: .../dados_{date}.xml)"),
            ("planocorte", "Plano de Corte (PDFs):", "Pasta base onde estão os PDFs (suporta placeholders: {year}, {month}, {month_name}, {day}, {date}, {date_br})")
        ]

        for i, (key, label_text, tooltip) in enumerate(fields):
            # Label para o título do campo
            lbl = ttk.Label(grid_frame, text=label_text, font=("Segoe UI", 10, "bold"))
            lbl.grid(row=i*3, column=0, sticky="w", pady=(10, 0))
            
            # Entry para o caminho
            entry_var = tk.StringVar()
            # Pega o valor atual (ignora case insensitive pois o configparser salva chave minúscula por padrão)
            val = self.current_settings.get(key.lower(), self.current_settings.get(key, ""))
            entry_var.set(val)
            
            entry = ttk.Entry(grid_frame, textvariable=entry_var, width=50)
            entry.grid(row=i*3+1, column=0, sticky="ew", pady=(2, 5), padx=(0, 10))
            
            # Mapeia a variável pelo nome da chave para salvar depois
            self.entries[key.lower()] = entry_var

            # Botão de procurar
            btn_browse = ttk.Button(grid_frame, text="Procurar...", width=12,
                                    command=lambda k=key.lower(): self._browse_path(k))
            btn_browse.grid(row=i*3+1, column=1, pady=(2, 5))
            
            # Label de dica explicativa
            lbl_tip = ttk.Label(grid_frame, text=tooltip, font=("Segoe UI", 8), foreground="#aaaaaa")
            lbl_tip.grid(row=i*3+2, column=0, columnspan=2, sticky="w", pady=(0, 5))

        grid_frame.columnconfigure(0, weight=1)

    def _setup_logs_tab(self, parent):
        # Botões de controle do log
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill="x", pady=(0, 5))

        btn_refresh = ttk.Button(controls_frame, text="Atualizar Logs", command=self._load_logs)
        btn_refresh.pack(side="left", padx=(0, 10))
        
        btn_clear = ttk.Button(controls_frame, text="Limpar Visualização", command=lambda: self.txt_logs.delete('1.0', tk.END))
        btn_clear.pack(side="left")

        # Área de texto com scroll
        self.txt_logs = st.ScrolledText(parent, wrap=tk.WORD, font=("Consolas", 9), bg="#1e1e1e", fg="#e0e0e0")
        self.txt_logs.pack(fill="both", expand=True)
        
        # Carrega logs iniciais
        self._load_logs()

    def _load_logs(self):
        self.txt_logs.delete('1.0', tk.END)
        
        # Caminho relativo baseado na raiz do projeto
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_path = os.path.join(base_dir, "logs", "app_errors.log")
        
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if not content:
                        content = "<Arquivo de log vazio>"
                    self.txt_logs.insert(tk.END, content)
                    # Rola para o final para ver os erros mais recentes
                    self.txt_logs.see(tk.END)
            except Exception as e:
                self.txt_logs.insert(tk.END, f"Erro ao ler arquivo de log: {e}")
        else:
            self.txt_logs.insert(tk.END, "Nenhum arquivo de log encontrado (logs/app_errors.log).")

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
                # Para ser consistente, vamos gravar como raw string form
                self.entries[key].set(folder_path)

    def _save_settings(self):
        new_settings = {}
        for key, var in self.entries.items():
            new_val = var.get().strip()
            if not new_val:
                messagebox.showwarning("Aviso", f"O campo associado à chave '{key}' não pode estar vazio.", parent=self)
                return
            new_settings[key] = new_val

        try:
            ConfigManager.save_settings(new_settings)
            
            # Dica visual: pode ser necessário reiniciar (recarregar ConfigManager)
            ConfigManager.load_settings()
            
            messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!", parent=self)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao salvar as configurações:\n{e}", parent=self)

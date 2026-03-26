import configparser
import os
import shutil
import sys

# Diretorio do projeto em desenvolvimento.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Diretorio do executavel quando empacotado.
APP_ROOT = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else PROJECT_ROOT
# Diretorio onde o PyInstaller expande recursos.
RESOURCE_ROOT = getattr(sys, "_MEIPASS", PROJECT_ROOT)
# O config em execucao fica fora do bundle, ao lado do .exe.
CONFIG_FILE = os.getenv("PCP_CONFIG_FILE", os.path.join(APP_ROOT, "config.ini"))


class ConfigManager:
    _config_cache = None

    @staticmethod
    def _resource_path(*parts):
        return os.path.join(RESOURCE_ROOT, *parts)

    @staticmethod
    def _app_path(*parts):
        return os.path.join(APP_ROOT, *parts)

    @staticmethod
    def _copy_bundled_public_if_needed():
        source_public = ConfigManager._resource_path("Public")
        target_public = ConfigManager._app_path("Public")
        if source_public == target_public:
            return
        if os.path.exists(target_public) or not os.path.exists(source_public):
            return
        try:
            shutil.copytree(source_public, target_public)
        except Exception:
            pass

    @staticmethod
    def _ensure_runtime_layout():
        ConfigManager._copy_bundled_public_if_needed()
        local_dirs = [
            ConfigManager._app_path("Public"),
            ConfigManager._app_path("Public", "acervo_cnc"),
            ConfigManager._app_path("Public", "saidas_cnc"),
            ConfigManager._app_path("Public", "saidas_cortadas"),
            ConfigManager._app_path("Public", "plano_corte"),
            ConfigManager._app_path("Public", "dados"),
            ConfigManager._app_path("Public", "app_data"),
            ConfigManager._app_path("Public", "app_data", "logs"),
        ]
        for directory in local_dirs:
            try:
                os.makedirs(directory, exist_ok=True)
            except OSError:
                pass

    @staticmethod
    def _resolve_path(path_str):
        """Converte caminhos relativos em absolutos e preserva caminhos UNC."""
        if not path_str:
            return path_str
        if path_str.startswith("\\\\") or path_str.startswith("//"):
            return path_str
        normalized = path_str.replace("/", os.sep).replace("\\", os.sep)
        if normalized.startswith(f".{os.sep}"):
            return os.path.join(APP_ROOT, normalized[2:])
        if os.path.isabs(path_str):
            return path_str
        return path_str

    @staticmethod
    def _format_template(value, extra_vars=None):
        if not value:
            return value

        template_vars = {}
        if extra_vars:
            template_vars.update(extra_vars)

        if "machine" not in template_vars:
            machine_id = os.getenv("PCP_MACHINE_ID")
            if machine_id:
                template_vars["machine"] = machine_id
            else:
                ConfigManager._ensure_loaded()
                config = ConfigManager._config_cache
                if config and config.has_section("Machine"):
                    template_vars["machine"] = config.get("Machine", "current_machine", fallback="Bodor1 (12K)")
                else:
                    template_vars["machine"] = "Bodor1 (12K)"

        try:
            return str(value).format(**template_vars)
        except KeyError:
            return value

    @staticmethod
    def _create_default_config():
        ConfigManager._ensure_runtime_layout()
        config = configparser.ConfigParser()
        config["Paths"] = {
            # Defaults portateis; em rede compartilhada, troque por caminhos UNC.
            "AcervoSaidasCNC": "./Public/acervo_cnc",
            "SaidasCnc": "./Public/saidas_cnc",
            "SaidasCortadas": "./Public/saidas_cortadas",
            "PlanoCorte": "./Public/plano_corte",
            "DadosXml": "./Public/dados/dados_{date}.xml",
            "LocksFile": "./Public/app_data/active_locks.json",
            "OfflineQueueDir": "./Public/app_data/offline_queue/{machine}",
            "LogsDir": "./Public/app_data/logs",
        }
        config["Machine"] = {
            "machine_name": "Bodor1 (12K)",
            "current_machine": "Bodor1 (12K)",
            "available_machines": "Bodor1 (12K), Bodor2 (6K), Bodor3 (4K), Bodor4 (3K), Trumpf1, Trumpf2",
        }
        config["Auth"] = {
            "admin_user": "PCP01",
            "admin_pass": "pcp0126",
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as configfile:
            config.write(configfile)

    @staticmethod
    def _ensure_loaded():
        """Garante que as configuracoes foram carregadas na memoria."""
        if ConfigManager._config_cache is None:
            ConfigManager.load_settings()

    @staticmethod
    def load_settings():
        ConfigManager._ensure_runtime_layout()
        if not os.path.exists(CONFIG_FILE):
            ConfigManager._create_default_config()

        config = configparser.ConfigParser()
        config.read(CONFIG_FILE, encoding="utf-8")

        if not config.has_section("Paths") or not config.has_option("Paths", "SaidasCnc"):
            ConfigManager._create_default_config()
            config.read(CONFIG_FILE, encoding="utf-8")

        ConfigManager._config_cache = config

    @staticmethod
    def _get_path(key, default_val, extra_vars=None):
        ConfigManager._ensure_loaded()
        config = ConfigManager._config_cache
        if config and config.has_section("Paths"):
            path = config.get("Paths", key, fallback=default_val).strip('"').strip("'")
            return ConfigManager._resolve_path(ConfigManager._format_template(path, extra_vars))
        return ConfigManager._resolve_path(ConfigManager._format_template(default_val, extra_vars))

    @staticmethod
    def get_server_path():
        return ConfigManager._get_path("AcervoSaidasCNC", "./Public/acervo_cnc")

    @staticmethod
    def get_saidas_cnc_path():
        return ConfigManager._get_path("SaidasCnc", "./Public/saidas_cnc")

    @staticmethod
    def get_saidas_cortadas_path():
        return ConfigManager._get_path("SaidasCortadas", "./Public/saidas_cortadas")

    @staticmethod
    def get_k8_data_path(target_date=None):
        """Retorna o caminho do XML de dados. Aceita datetime ou string YYYY-MM-DD opcional."""
        from datetime import datetime

        if target_date is None:
            target_date = datetime.now()

        if hasattr(target_date, "strftime"):
            date_str = target_date.strftime("%Y-%m-%d")
        else:
            try:
                dt_obj = datetime.strptime(str(target_date), "%d/%m/%Y")
                date_str = dt_obj.strftime("%Y-%m-%d")
            except ValueError:
                date_str = str(target_date)

        env_xml = os.getenv("PCP_DADOS_XML")
        if env_xml:
            return ConfigManager._resolve_path(ConfigManager._format_template(env_xml, {"date": date_str}))

        config_val = ConfigManager._get_path("DadosXml", "", {"date": date_str})

        if not config_val or config_val.endswith("dados.xml"):
            return ConfigManager._resolve_path(
                ConfigManager._format_template(f"./Public/dados/dados_{date_str}.xml", {"date": date_str})
            )

        return config_val

    @staticmethod
    def get_plano_corte_path():
        return ConfigManager._get_path("PlanoCorte", "./Public/plano_corte")

    @staticmethod
    def get_locks_file_path():
        env_locks = os.getenv("PCP_LOCKS_FILE")
        if env_locks:
            return ConfigManager._resolve_path(ConfigManager._format_template(env_locks))
        return ConfigManager._get_path("LocksFile", "./Public/app_data/active_locks.json")

    @staticmethod
    def get_offline_queue_dir():
        env_queue = os.getenv("PCP_OFFLINE_QUEUE_DIR")
        if env_queue:
            return ConfigManager._resolve_path(ConfigManager._format_template(env_queue))
        return ConfigManager._get_path("OfflineQueueDir", "./Public/app_data/offline_queue/{machine}")

    @staticmethod
    def get_logs_dir():
        env_logs = os.getenv("PCP_LOGS_DIR")
        if env_logs:
            return ConfigManager._resolve_path(ConfigManager._format_template(env_logs))
        return ConfigManager._get_path("LogsDir", "./Public/app_data/logs")

    @staticmethod
    def get_current_machine():
        """Retorna a maquina atualmente selecionada."""
        if os.getenv("PCP_MACHINE_ID"):
            return os.getenv("PCP_MACHINE_ID")

        ConfigManager._ensure_loaded()
        config = ConfigManager._config_cache
        if config and config.has_section("Machine"):
            machine_name = config.get("Machine", "machine_name", fallback="").strip('"').strip("'")
            if machine_name:
                return machine_name
            machine = config.get("Machine", "current_machine", fallback="").strip('"').strip("'")
            if machine:
                return machine
        machines = ConfigManager.get_available_machines()
        return machines[0] if machines else "Bodor1 (12K)"

    @staticmethod
    def get_available_machines():
        """Retorna a lista de maquinas disponiveis."""
        default_machines = [
            "Bodor1 (12K)",
            "Bodor2 (6K)",
            "Bodor3 (4K)",
            "Bodor4 (3K)",
            "Trumpf1",
            "Trumpf2",
        ]
        ConfigManager._ensure_loaded()
        config = ConfigManager._config_cache
        if config and config.has_section("Machine") and config.has_option("Machine", "available_machines"):
            machines_str = config.get("Machine", "available_machines").strip('"').strip("'")
            if machines_str:
                return [m.strip() for m in machines_str.split(",")]
        return default_machines

    @staticmethod
    def get_admin_credentials():
        """Retorna (usuario, senha) priorizando: Env Var > Config.ini > Default."""
        env_user = os.getenv("PCP_ADMIN_USER")
        env_pass = os.getenv("PCP_ADMIN_PASS")
        if env_user and env_pass:
            return env_user, env_pass

        ConfigManager._ensure_loaded()
        config = ConfigManager._config_cache
        if config and config.has_section("Auth"):
            return config.get("Auth", "admin_user", fallback="PCP01"), config.get(
                "Auth", "admin_pass", fallback="pcp0126"
            )

        return "PCP01", "pcp0126"

    @staticmethod
    def get_all_settings():
        """Retorna todos os caminhos configurados no config.ini como um dicionario."""
        ConfigManager._ensure_loaded()
        config = ConfigManager._config_cache

        settings = {}
        if config.has_section("Paths"):
            for key in config.options("Paths"):
                settings[key] = config.get("Paths", key)
        if config.has_section("Machine"):
            for key in config.options("Machine"):
                settings[key] = config.get("Machine", key)
        return settings

    @staticmethod
    def save_settings(new_settings):
        """Salva as configuracoes atualizadas no config.ini."""
        ConfigManager._ensure_runtime_layout()
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_FILE):
            config.read(CONFIG_FILE, encoding="utf-8")

        if not config.has_section("Paths"):
            config.add_section("Paths")
        if not config.has_section("Machine"):
            config.add_section("Machine")

        for key, value in new_settings.items():
            if key in ["machine_name", "current_machine", "available_machines"]:
                config.set("Machine", key, str(value))
            else:
                config.set("Paths", key, str(value))

        with open(CONFIG_FILE, "w", encoding="utf-8") as configfile:
            config.write(configfile)

        ConfigManager.load_settings()

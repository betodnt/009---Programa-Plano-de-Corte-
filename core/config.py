import os
import configparser

# Obtém o caminho absoluto para o diretório raiz do projeto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_FILE = os.path.join(PROJECT_ROOT, "config.ini")

class ConfigManager:
    _config_cache = None

    @staticmethod
    def _resolve_path(path_str):
        """Converte caminhos relativos em absolutos, preservando caminhos de rede (UNC)"""
        if path_str.startswith('./'):
            return os.path.join(PROJECT_ROOT, path_str[2:])
        # Se for um caminho UNC (\\servidor\pasta), retorna como está
        if path_str.startswith('\\\\') or path_str.startswith('//'):
            return path_str
        return path_str
    
    @staticmethod
    def _create_default_config():
        config = configparser.ConfigParser()
        config['Paths'] = {
            # Use uma string raw para que as barras invertidas não sejam tratadas como sequências de escape.
            'AcervoSaidasCNC': r'V:\8. CONTROLE DE PRODUÇÃO\1. SAÍDAS A CORTAR',
            'SaidasCnc': './Public/saidas_cnc',
            'SaidasCortadas': r'V:\8. CONTROLE DE PRODUÇÃO\2. SAÍDAS CORTADAS',
            'PlanoCorte': './Public/plano_corte',
            'DadosXml': r'V:\8. CONTROLE DE PRODUÇÃO\3. DADOS/dados_{date}.xml', # Placeholder para template
            'LocksFile': './active_locks.json'
        }
        config['Machine'] = {
            'current_machine': 'Bodor1 (12K)',
            'available_machines': 'Bodor1 (12K), Bodor2 (6K), Bodor3 (4K), Trumpf1, Trumpf2'
        }
        config['Auth'] = {
            'admin_user': 'PCP01',
            'admin_pass': 'pcp0126'
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile:
            config.write(configfile)

    @staticmethod
    def _ensure_loaded():
        """Garante que as configurações foram carregadas na memória"""
        if ConfigManager._config_cache is None:
            ConfigManager.load_settings()

    @staticmethod
    def load_settings():
        if not os.path.exists(CONFIG_FILE):
            ConfigManager._create_default_config()
            
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE, encoding='utf-8')
        
        # Verifica se falta alguma chave
        if not config.has_section('Paths') or not config.has_option('Paths', 'SaidasCnc'):
            ConfigManager._create_default_config()
            config.read(CONFIG_FILE, encoding='utf-8')

        ConfigManager._config_cache = config

    @staticmethod
    def _get_path(key, default_val):
        ConfigManager._ensure_loaded()
        config = ConfigManager._config_cache
        if config and config.has_section('Paths'):
            path = config.get('Paths', key, fallback=default_val).strip('"').strip("'")
            return ConfigManager._resolve_path(path)
        return ConfigManager._resolve_path(default_val)

    @staticmethod
    def get_server_path():
        return ConfigManager._get_path('AcervoSaidasCNC', r'V:\8. CONTROLE DE PRODUÇÃO\1. SAÍDAS A CORTAR')

    @staticmethod
    def get_saidas_cnc_path():
        return ConfigManager._get_path('SaidasCnc', './public/saidas_cnc')

    @staticmethod
    def get_saidas_cortadas_path():
        return ConfigManager._get_path('SaidasCortadas', './public/saidas_cortadas')

    @staticmethod
    def get_k8_data_path(target_date=None):
        """Retorna o caminho do XML de dados. Aceita datetime ou string YYYY-MM-DD opcional."""
        from datetime import datetime
        if target_date is None:
            target_date = datetime.now()
        
        # Se for objeto datetime, converte. Se for string, assume que já é ou ajusta.
        if hasattr(target_date, 'strftime'):
            date_str = target_date.strftime("%Y-%m-%d")
        else:
            # Se vier string formato brasileiro, tenta converter, senão usa como está
            try:
                dt_obj = datetime.strptime(str(target_date), "%d/%m/%Y")
                date_str = dt_obj.strftime("%Y-%m-%d")
            except ValueError:
                date_str = str(target_date)

        env_xml = os.getenv("PCP_DADOS_XML")
        if env_xml:
            return ConfigManager._resolve_path(env_xml.replace("{date}", date_str))
        
        # Forçamos arquivos diários, então verificamos se a configuração tem um template ou usamos o padrão diário
        config_val = ConfigManager._get_path('DadosXml', '')
        if config_val and '{date}' in config_val:
            return config_val.replace('{date}', date_str)
            
        # Se a configuração tiver um "dados.xml" estático, nós o sobrescrevemos para ser diário
        if not config_val or config_val.endswith('dados.xml'):
            return ConfigManager._resolve_path(f'./public/dados/dados_{date_str}.xml')
            
        return config_val

    @staticmethod
    def get_plano_corte_path():
        return ConfigManager._get_path('PlanoCorte', './public/plano_corte')

    @staticmethod
    def get_locks_file_path():
        env_locks = os.getenv("PCP_LOCKS_FILE")
        if env_locks:
            return ConfigManager._resolve_path(env_locks)
        return ConfigManager._get_path('LocksFile', './active_locks.json')

    @staticmethod
    def get_current_machine():
        """Retorna a máquina atualmente selecionada"""
        # 0. Permite sobrescrever via variável de ambiente (útil para testes de múltiplas instâncias)
        if os.getenv("PCP_MACHINE_ID"):
            return os.getenv("PCP_MACHINE_ID")
            
        ConfigManager._ensure_loaded()
        config = ConfigManager._config_cache
        if config and config.has_section('Machine') and config.has_option('Machine', 'current_machine'):
            machine = config.get('Machine', 'current_machine').strip('"').strip("'")
            if machine:
                return machine
        # Fallback para a primeira máquina disponível
        machines = ConfigManager.get_available_machines()
        return machines[0] if machines else "Bodor1 (12K)"

    @staticmethod
    def get_available_machines():
        """Retorna a lista de máquinas disponíveis"""
        # Lista padrão de máquinas
        default_machines = [
            "Bodor1 (12K)",
            "Bodor2 (6K)",
            "Bodor3 (4K)",
            "Trumpf1",
            "Trumpf2"
        ]
        # Se houver máquinas configuradas no config.ini, usar elas
        ConfigManager._ensure_loaded()
        config = ConfigManager._config_cache
        if config and config.has_section('Machine') and config.has_option('Machine', 'available_machines'):
            machines_str = config.get('Machine', 'available_machines').strip('"').strip("'")
            if machines_str:
                return [m.strip() for m in machines_str.split(',')]
        return default_machines

    @staticmethod
    def get_admin_credentials():
        """Retorna (usuario, senha) priorizando: Env Var > Config.ini > Default"""
        # 1. Tenta Variáveis de Ambiente (Mais seguro)
        env_user = os.getenv("PCP_ADMIN_USER")
        env_pass = os.getenv("PCP_ADMIN_PASS")
        if env_user and env_pass:
            return env_user, env_pass

        # 2. Tenta Config.ini
        ConfigManager._ensure_loaded()
        config = ConfigManager._config_cache
        if config and config.has_section('Auth'):
            return config.get('Auth', 'admin_user', fallback='PCP01'), \
                   config.get('Auth', 'admin_pass', fallback='pcp0126')
        
        # 3. Fallback Hardcoded (para compatibilidade imediata)
        return "PCP01", "pcp0126"

    @staticmethod
    def get_all_settings():
        """Retorna todos os caminhos configurados no config.ini como um dicionário"""
        ConfigManager._ensure_loaded()
        config = ConfigManager._config_cache
        
        settings = {}
        if config.has_section('Paths'):
            for key in config.options('Paths'):
                settings[key] = config.get('Paths', key)
        if config.has_section('Machine'):
            for key in config.options('Machine'):
                settings[key] = config.get('Machine', key)
        return settings

    @staticmethod
    def save_settings(new_settings):
        """Salva as configurações atualizadas no config.ini"""
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_FILE):
            config.read(CONFIG_FILE, encoding='utf-8')
            
        if not config.has_section('Paths'):
            config.add_section('Paths')
        if not config.has_section('Machine'):
            config.add_section('Machine')

        for key, value in new_settings.items():
            if key in ['current_machine', 'available_machines']:
                config.set('Machine', key, str(value))
            else:
                config.set('Paths', key, str(value))

        with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile:
            config.write(configfile)
            
        # Recarrega as configurações na memória para atualizar o cache
        ConfigManager.load_settings()

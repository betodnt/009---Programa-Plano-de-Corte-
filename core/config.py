import os
import configparser

# Get the absolute path to the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_FILE = os.path.join(PROJECT_ROOT, "config.ini")

class ConfigManager:
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
            # Use a raw string so backslashes are not treated as escape sequences.
            'AcervoSaidasCNC': r'V:\8. CONTROLE DE PRODUÇÃO\1. SAÍDAS A CORTAR',
            'SaidasCnc': './Public/saidas_cnc',
            'SaidasCortadas': r'V:\8. CONTROLE DE PRODUÇÃO\2. SAÍDAS CORTADAS',
            'PlanoCorte': './Public/plano_corte',
            'DadosXml': r'V:\8. CONTROLE DE PRODUÇÃO\3. DADOS/dados_{date}.xml' # Template placeholder
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile:
            config.write(configfile)

    @staticmethod
    def load_settings():
        if not os.path.exists(CONFIG_FILE):
            ConfigManager._create_default_config()
            return
            
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE, encoding='utf-8')
        
        # Check if missing key
        if not config.has_section('Paths') or not config.has_option('Paths', 'SaidasCnc'):
            ConfigManager._create_default_config()

    @staticmethod
    def _get_path(key, default_val):
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_FILE):
            config.read(CONFIG_FILE, encoding='utf-8')
            if config.has_section('Paths'):
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
    def get_k8_data_path():
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # We want to force daily files, so we check if the config has a template or just use daily default
        config_val = ConfigManager._get_path('DadosXml', '')
        if config_val and '{date}' in config_val:
            return config_val.replace('{date}', date_str)
            
        # If config has a static "dados.xml", we override it to be daily
        if not config_val or config_val.endswith('dados.xml'):
            return ConfigManager._resolve_path(f'./public/dados/dados_{date_str}.xml')
            
        return config_val

    @staticmethod
    def get_plano_corte_path():
        return ConfigManager._get_path('PlanoCorte', './public/plano_corte')

    @staticmethod
    def get_all_settings():
        """Retorna todos os caminhos configurados no config.ini como um dicionário"""
        if not os.path.exists(CONFIG_FILE):
            ConfigManager._create_default_config()

        config = configparser.ConfigParser()
        config.read(CONFIG_FILE, encoding='utf-8')
        
        settings = {}
        if config.has_section('Paths'):
            for key in config.options('Paths'):
                settings[key] = config.get('Paths', key)
        return settings

    @staticmethod
    def save_settings(new_settings):
        """Salva as configurações atualizadas no config.ini"""
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_FILE):
            config.read(CONFIG_FILE, encoding='utf-8')
            
        if not config.has_section('Paths'):
            config.add_section('Paths')

        for key, value in new_settings.items():
            config.set('Paths', key, str(value))

        with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile:
            config.write(configfile)

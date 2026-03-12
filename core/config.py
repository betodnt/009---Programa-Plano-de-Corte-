import os
import configparser

CONFIG_FILE = "config.ini"

# Get the absolute path to the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class ConfigManager:
    @staticmethod
    def _resolve_path(path_str):
        """Converte caminhos relativos em absolutos baseado no diretório do projeto"""
        if path_str.startswith('./'):
            return os.path.join(PROJECT_ROOT, path_str[2:])
        return path_str
    
    @staticmethod
    def _create_default_config():
        config = configparser.ConfigParser()
        config['Paths'] = {
            'AcervoSaidasCNC': './public/saidas_a_cortar',
            'SaidasCnc': './public/saidas_cnc',
            'SaidasCortadas': './public/saidas_cortadas',
            'PlanoCorte': './public/plano_corte',
            'DadosXml': './public/dados/dados.xml'
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
        return ConfigManager._get_path('AcervoSaidasCNC', './public/saidas_a_cortar')

    @staticmethod
    def get_saidas_cnc_path():
        return ConfigManager._get_path('SaidasCnc', './public/saidas_cnc')

    @staticmethod
    def get_saidas_cortadas_path():
        return ConfigManager._get_path('SaidasCortadas', './public/saidas_cortadas')

    @staticmethod
    def get_k8_data_path():
        return ConfigManager._get_path('DadosXml', './public/dados/dados.xml')

    @staticmethod
    def get_plano_corte_path():
        return ConfigManager._get_path('PlanoCorte', './public/plano_corte')

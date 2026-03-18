import json
import os

OPERATORS_FILE = "recent_operators.json"

class OperatorsManager:
    """Gerencia histórico persistente de operadores"""
    
    @staticmethod
    def load_operators():
        """Carrega últimos 3 operadores do arquivo"""
        if not os.path.exists(OPERATORS_FILE):
            return []
        try:
            with open(OPERATORS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('operators', [])
        except:
            return []
    
    @staticmethod
    def add_operator(operator_name):
        """Adiciona operador ao início da lista (mais recente)"""
        if not operator_name:
            return
        
        operators = OperatorsManager.load_operators()
        
        # Remove se já existe (para evitar duplicatas)
        if operator_name in operators:
            operators.remove(operator_name)
        
        # Adiciona no início
        operators.insert(0, operator_name)
        
        # Mantém apenas últimos 10
        operators = operators[:10]
        
        # Salva
        os.makedirs(os.path.dirname(OPERATORS_FILE) or '.', exist_ok=True)
        with open(OPERATORS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'operators': operators}, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def get_recent_operators(max_count=3):
        """Retorna últimos N operadores"""
        operators = OperatorsManager.load_operators()
        return operators[:max_count]

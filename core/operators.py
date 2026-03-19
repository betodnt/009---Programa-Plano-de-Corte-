import json
import os

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPERATORS_FILE = os.path.join(_PROJECT_ROOT, "recent_operators.json")

class OperatorsManager:

    @staticmethod
    def load_operators():
        if not os.path.exists(OPERATORS_FILE):
            return []
        try:
            with open(OPERATORS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('operators', [])
        except Exception:
            return []

    @staticmethod
    def add_operator(operator_name):
        if not operator_name:
            return
        operators = OperatorsManager.load_operators()
        if operator_name in operators:
            operators.remove(operator_name)
        operators.insert(0, operator_name)
        operators = operators[:10]
        with open(OPERATORS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'operators': operators}, f, ensure_ascii=False, indent=2)

    @staticmethod
    def get_recent_operators(max_count=10):
        return OperatorsManager.load_operators()[:max_count]

import pytest
import json
from core.operators import OperatorsManager

@pytest.fixture
def temp_operators_file(tmp_path, monkeypatch):
    operators_file = tmp_path / "recent_operators.json"
    monkeypatch.setattr("core.operators.OPERATORS_FILE", str(operators_file))
    return operators_file

def test_load_operators_empty(temp_operators_file):
    operators = OperatorsManager.load_operators()
    assert operators == []

def test_add_operator(temp_operators_file):
    OperatorsManager.add_operator("Operador1")
    operators = OperatorsManager.load_operators()
    assert operators == ["Operador1"]

def test_add_operator_duplicate_moves_to_front(temp_operators_file):
    OperatorsManager.add_operator("Operador1")
    OperatorsManager.add_operator("Operador2")
    OperatorsManager.add_operator("Operador1")  # Duplicate
    operators = OperatorsManager.load_operators()
    assert operators == ["Operador1", "Operador2"]

def test_add_operator_limits_to_10(temp_operators_file):
    for i in range(12):
        OperatorsManager.add_operator(f"Operador{i}")
    operators = OperatorsManager.load_operators()
    assert len(operators) == 10
    assert operators[0] == "Operador11"  # Most recent first

def test_get_recent_operators(temp_operators_file):
    for i in range(5):
        OperatorsManager.add_operator(f"Operador{i}")
    recent = OperatorsManager.get_recent_operators(3)
    assert recent == ["Operador4", "Operador3", "Operador2"]

def test_get_recent_operators_more_than_available(temp_operators_file):
    OperatorsManager.add_operator("Operador1")
    recent = OperatorsManager.get_recent_operators(5)
    assert recent == ["Operador1"]

def test_load_operators_with_existing_file(temp_operators_file):
    data = {"operators": ["Op1", "Op2"]}
    with open(temp_operators_file, "w", encoding="utf-8") as f:
        json.dump(data, f)
    operators = OperatorsManager.load_operators()
    assert operators == ["Op1", "Op2"]
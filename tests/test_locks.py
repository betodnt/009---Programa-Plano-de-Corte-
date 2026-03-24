import pytest
import os
import json
import time
from core.locks import LocksManager

@pytest.fixture
def temp_locks_file(tmp_path, monkeypatch):
    locks_file = tmp_path / "active_locks.json"
    monkeypatch.setattr("core.locks.LOCKS_FILE", str(locks_file))
    return locks_file

def test_acquire_lock(temp_locks_file):
    LocksManager.acquire_lock("Maquina1", "Saida1", "Operador1", "Pedido1")
    assert temp_locks_file.exists()
    with open(temp_locks_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "Maquina1|Saida1" in data
    lock_data = data["Maquina1|Saida1"]
    assert lock_data["maquina"] == "Maquina1"
    assert lock_data["saida"] == "Saida1"
    assert lock_data["operador"] == "Operador1"
    assert lock_data["pedido"] == "Pedido1"
    assert "timestamp" in lock_data

def test_release_lock(temp_locks_file):
    LocksManager.acquire_lock("Maquina1", "Saida1")
    LocksManager.release_lock("Maquina1", "Saida1")
    with open(temp_locks_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "Maquina1|Saida1" not in data

def test_release_all_locks_for_pid(temp_locks_file):
    LocksManager.acquire_lock("Maquina1", "Saida1")
    LocksManager.acquire_lock("Maquina2", "Saida2")
    LocksManager.release_all_locks_for_pid()
    with open(temp_locks_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Como são nossos locks, eles devem ser removidos
    assert len(data) == 0

def test_is_locked(temp_locks_file):
    assert not LocksManager.is_locked("Maquina1", "Saida1")
    LocksManager.acquire_lock("Maquina1", "Saida1")
    # Como é o nosso próprio lock, is_locked retorna False
    assert not LocksManager.is_locked("Maquina1", "Saida1")

def test_get_locked_saidas(temp_locks_file):
    LocksManager.acquire_lock("Maquina1", "Saida1")
    LocksManager.acquire_lock("Maquina1", "Saida2")
    LocksManager.acquire_lock("Maquina2", "Saida3")
    locked = LocksManager.get_locked_saidas("Maquina1")
    # Como são nossos próprios locks, não são considerados bloqueados para outros
    assert locked == []

def test_clean_expired_locks(temp_locks_file, monkeypatch):
    # Simula o tempo para testar a expiração
    monkeypatch.setattr("core.locks.LOCK_TIMEOUT", 1)  # 1 second timeout
    LocksManager.acquire_lock("Maquina1", "Saida1")
    time.sleep(2)  # Wait for expiration
    # A próxima operação deve limpar os locks expirados
    LocksManager.acquire_lock("Maquina2", "Saida2")
    with open(temp_locks_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "Maquina1|Saida1" not in data
    assert "Maquina2|Saida2" in data
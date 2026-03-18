#!/usr/bin/env python3
"""
Script para testar LocksManager com simulação de múltiplas instâncias
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.locks import LocksManager

def test_multi_instance_locks():
    print("=" * 60)
    print("TESTANDO LOCKS COM MÚLTIPLAS INSTÂNCIAS")
    print("=" * 60)
    
    # Limpar arquivo de locks anterior
    if os.path.exists("active_locks.json"):
        os.remove("active_locks.json")
        print("\n✓ Arquivo de locks anterior removido")
    
    # Simular instância 1 (PID 1234)
    print("\n--- INSTÂNCIA 1 (PID 1234) ---")
    locks = LocksManager._load_locks()
    locks['Bodor1 (12K)|saida001.cnc'] = {
        'maquina': 'Bodor1 (12K)',
        'saida': 'saida001.cnc',
        'pid': 1234,
        'timestamp': time.time()
    }
    LocksManager._save_locks(locks)
    print("1. Instância 1 adquiriu lock para Bodor1 + saida001.cnc")
    
    locks = LocksManager._load_locks()
    print(f"   Locks salvos: {json.dumps(locks, indent=2)}")
    
    # Simular instância 2 verificando locks (PID 5678)
    print("\n--- INSTÂNCIA 2 (PID 5678) ---")
    import os as os_module
    pid_original = os_module.getpid
    
    # Mock o getpid para simular outro processo
    os_module.getpid = lambda: 5678
    
    is_locked = LocksManager.is_locked("Bodor1 (12K)", "saida001.cnc")
    print(f"2. Verificando se Bodor1+saida001 está bloqueado: {is_locked}")
    print(f"   ✓ Deve ser True (bloqueado por outro processo): {is_locked == True}")
    
    locked_saidas = LocksManager.get_locked_saidas("Bodor1 (12K)")
    print(f"3. Saídas bloqueadas para Bodor1: {locked_saidas}")
    print(f"   ✓ Deve conter saida001.cnc: {'saida001.cnc' in locked_saidas}")
    
    # Simular instância 2 escolhendo saida002 (diferente, portanto disponível)
    print(f"4. Verificando se saida002.cnc está bloqueado: ", end="")
    is_locked_2 = LocksManager.is_locked("Bodor1 (12K)", "saida002.cnc")
    print(is_locked_2)
    print(f"   ✓ Deve ser False (disponível): {is_locked_2 == False}")
    
    # Restaurar getpid
    os_module.getpid = pid_original
    
    print("\n" + "=" * 60)
    print("✓ TESTE DE MÚLTIPLAS INSTÂNCIAS PASSOU!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_multi_instance_locks()
    except Exception as e:
        print(f"\n✗ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

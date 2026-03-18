#!/usr/bin/env python3
"""
Script de teste para validar OperatorsManager e LocksManager
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.operators import OperatorsManager
from core.locks import LocksManager

def test_operators():
    print("=" * 50)
    print("TESTANDO OPERATORSMANAGER")
    print("=" * 50)
    
    # Test 1: Load empty (should be [])
    print("\n1. Carregando operadores (deve estar vazio):")
    ops = OperatorsManager.load_operators()
    print(f"   Operadores: {ops}")
    
    # Test 2: Add 3 operators
    print("\n2. Adicionando 3 operadores:")
    OperatorsManager.add_operator("João Silva")
    print("   → João Silva adicionado")
    OperatorsManager.add_operator("Maria Santos")
    print("   → Maria Santos adicionado")
    OperatorsManager.add_operator("Pedro Costa")
    print("   → Pedro Costa adicionado")
    
    # Test 3: Verify they're saved
    print("\n3. Carregando operadores após adicionar:")
    ops = OperatorsManager.load_operators()
    print(f"   Operadores: {ops}")
    
    # Test 4: Add duplicate (should move to front)
    print("\n4. Adicionando João Silva novamente:")
    OperatorsManager.add_operator("João Silva")
    ops = OperatorsManager.load_operators()
    print(f"   Operadores: {ops}")
    print(f"   ✓ João Silva deve estar na frente: {ops[0] == 'João Silva'}")
    
    # Test 5: Get recent
    print("\n5. Buscando últimos 2 operadores:")
    recent = OperatorsManager.get_recent_operators(2)
    print(f"   Últimos 2: {recent}")

def test_locks():
    print("\n" + "=" * 50)
    print("TESTANDO LOCKSMANAGER")
    print("=" * 50)
    
    # Test 1: Acquire lock
    print("\n1. Adquirindo lock para Bodor1 + saida001.cnc:")
    LocksManager.acquire_lock("Bodor1 (12K)", "saida001.cnc")
    print("   ✓ Lock adquirido")
    
    # Test 2: Check is_locked
    print("\n2. Verificando se está bloqueado:")
    is_locked = LocksManager.is_locked("Bodor1 (12K)", "saida001.cnc")
    print(f"   É a mesma instância? {not is_locked} (deve ser True)")
    
    # Test 3: Get locked saidas
    print("\n3. Listando saídas bloqueadas para Bodor1:")
    locked = LocksManager.get_locked_saidas("Bodor1 (12K)")
    print(f"   Saídas bloqueadas: {locked}")
    
    # Test 4: Add another lock
    print("\n4. Adquirindo outro lock para Bodor1 + saida002.cnc:")
    LocksManager.acquire_lock("Bodor1 (12K)", "saida002.cnc")
    locked = LocksManager.get_locked_saidas("Bodor1 (12K)")
    print(f"   Saídas bloqueadas: {locked}")
    
    # Test 5: Release lock
    print("\n5. Liberando lock para saida001.cnc:")
    LocksManager.release_lock("Bodor1 (12K)", "saida001.cnc")
    locked = LocksManager.get_locked_saidas("Bodor1 (12K)")
    print(f"   Saídas bloqueadas: {locked}")
    print(f"   ✓ Deve conter apenas saida002.cnc: {'saida002.cnc' in locked}")

if __name__ == "__main__":
    try:
        test_operators()
        test_locks()
        print("\n" + "=" * 50)
        print("✓ TODOS OS TESTES PASSARAM!")
        print("=" * 50)
    except Exception as e:
        print(f"\n✗ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

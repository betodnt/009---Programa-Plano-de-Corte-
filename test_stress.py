import multiprocessing
import threading
import time
import os
import sys

# Insere a pasta raiz para importar os core modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.locks import LocksManager
from core.database import DatabaseManager

# Precisamos simular chamadas de 6 máquinas usando processos separados
# para testar de fato o OS file locking.

def worker_machine(machine_id):
    maquina = f"Máquina {machine_id}"
    print(f"[{maquina}] Iniciou.")
    for i in range(10):  # tenta 10 salvamentos/locks
        saida = f"Saida {i}"
        operador = f"Operador {machine_id}"
        pedido = f"100{machine_id}{i}"
        
        # 1. Acquire Lock
        try:
            LocksManager.acquire_lock(maquina, saida, operador, pedido)
            # print(f"[{maquina}] Adquiriu lock para {saida}.")
        except Exception as e:
            print(f"[{maquina}] ERRO LOCK: {e}")
            
        time.sleep(0.1) # Simulando trabalho
        
        # 2. Database Write
        file_path = f"./public/dados/dados_stress.xml"
        try:
            DatabaseManager.save_entrada(file_path, pedido, operador, maquina, "N/A", saida, "Corte", "2026-03-24 10:00:00")
            # print(f"[{maquina}] Gravou XML para {saida}.")
        except Exception as e:
            print(f"[{maquina}] ERRO XML: {e}")

        time.sleep(0.05)
        
        # 3. Release Lock
        try:
            LocksManager.release_lock(maquina, saida)
        except Exception as e:
            print(f"[{maquina}] ERRO UNLOCK: {e}")
            
    print(f"[{maquina}] Finalizou.")

def monitor_simulator():
    from core.config import ConfigManager
    print("[Monitor] Iniciou Thread de leitura.")
    for _ in range(25): # Monitor run for 5 seconds total (0.2s * 25)
        try:
            import xml.etree.ElementTree as ET
            file_path = f"./public/dados/dados_stress.xml"
            if os.path.exists(file_path):
                tree = ET.parse(file_path)
                root = tree.getroot()
                c = len(root.findall("Entrada"))
                # print(f"[Monitor] Leu com sucesso {c} entradas no XML.")
        except ET.ParseError:
            print("[Monitor] XML ParseError: Normal se bateu com escrita!")
        except Exception as e:
            print(f"[Monitor] ERRO INSPERADO: {e}")
            
        try:
            locks = LocksManager._load_locks()
            # print(f"[Monitor] Leu {len(locks)} locks ativos.")
        except Exception as e:
            print(f"[Monitor] ERRO lendo JSON: {e}")
            
        time.sleep(0.2)
    print("[Monitor] Finalizou.")

if __name__ == "__main__":
    tests = []
    
    # Inicia a thread do monitor
    tm = threading.Thread(target=monitor_simulator)
    tm.start()
    
    start_time = time.time()
    # Inicia 6 Processos para emular 6 computadores físicos
    for i in range(1, 7):
        p = multiprocessing.Process(target=worker_machine, args=(i,))
        tests.append(p)
        p.start()
        
    for p in tests:
        p.join()
        
    tm.join()
    
    print(f"Stress test concluído em {time.time() - start_time:.2f} segundos.")
    # Verifica estado final do locks.json
    final_locks = LocksManager._load_locks()
    print(f"Locks residuais (esperado 0): {len(final_locks)}")

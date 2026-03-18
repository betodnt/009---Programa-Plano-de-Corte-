#!/usr/bin/env python3
"""
Monitor de locks em tempo real
"""

import time
import os
import json
from core.locks import LocksManager

def monitor_locks():
    print("=== MONITOR DE LOCKS ===")
    print("Monitorando active_locks.json em tempo real...")
    print("Pressione Ctrl+C para parar\n")

    last_locks = {}

    while True:
        try:
            current_locks = LocksManager._load_locks()
            LocksManager._clean_expired_locks(current_locks)

            # Verifica se houve mudanças
            if current_locks != last_locks:
                print(f"\n[{time.strftime('%H:%M:%S')}] Locks atualizados:")
                if not current_locks:
                    print("  Nenhum lock ativo")
                else:
                    for key, data in current_locks.items():
                        maquina = data.get('maquina', 'N/A')
                        saida = data.get('saida', 'N/A')
                        pid = data.get('pid', 'N/A')
                        timestamp = time.strftime('%H:%M:%S', time.localtime(data.get('timestamp', 0)))
                        print(f"  🔒 {maquina} | {saida} (PID: {pid}, desde: {timestamp})")

                # Mostra saídas bloqueadas por máquina
                maquinas = set(data.get('maquina') for data in current_locks.values())
                for maquina in maquinas:
                    locked = LocksManager.get_locked_saidas(maquina)
                    if locked:
                        print(f"  🚫 {maquina}: {locked} bloqueadas")

                last_locks = current_locks.copy()

            time.sleep(2)  # Atualiza a cada 2 segundos

        except KeyboardInterrupt:
            print("\n\nMonitor parado.")
            break
        except Exception as e:
            print(f"Erro: {e}")
            time.sleep(5)

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    monitor_locks()
import multiprocessing
import os
import sys
import tempfile
import threading
import time

# Insere a pasta raiz para importar os core modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import DatabaseManager
from core.locks import LocksManager

STRESS_DIR = os.path.join(tempfile.gettempdir(), "plano_corte_stress")
LOCKS_FILE = os.path.join(STRESS_DIR, "active_locks.json")
XML_FILE = os.path.join(STRESS_DIR, "dados_stress.xml")


def _prepare_environment():
    os.makedirs(STRESS_DIR, exist_ok=True)
    for path in (LOCKS_FILE, XML_FILE, LOCKS_FILE + ".lock", XML_FILE + ".lock"):
        try:
            os.remove(path)
        except OSError:
            pass


def _configure_test_paths():
    os.environ["PCP_LOCKS_FILE"] = LOCKS_FILE
    os.environ["PCP_DADOS_XML"] = XML_FILE


def worker_machine(machine_id):
    maquina = f"Maquina {machine_id}"
    print(f"[{maquina}] Iniciou.")
    for i in range(10):
        saida = f"Saida {i}"
        operador = f"Operador {machine_id}"
        pedido = f"100{machine_id}{i}"

        try:
            LocksManager.acquire_lock(maquina, saida, operador, pedido)
        except Exception as e:
            print(f"[{maquina}] ERRO LOCK: {e}")

        time.sleep(0.1)

        try:
            DatabaseManager.save_entrada(
                XML_FILE,
                pedido,
                operador,
                maquina,
                "N/A",
                saida,
                "Corte",
                "2026-03-24 10:00:00",
            )
        except Exception as e:
            print(f"[{maquina}] ERRO XML: {e}")

        time.sleep(0.05)

        try:
            LocksManager.release_lock(maquina, saida)
        except Exception as e:
            print(f"[{maquina}] ERRO UNLOCK: {e}")

    print(f"[{maquina}] Finalizou.")


def monitor_simulator():
    print("[Monitor] Iniciou Thread de leitura.")
    for _ in range(25):
        try:
            import xml.etree.ElementTree as ET

            if os.path.exists(XML_FILE):
                tree = ET.parse(XML_FILE)
                root = tree.getroot()
                len(root.findall("Entrada"))
        except ET.ParseError:
            print("[Monitor] XML ParseError: houve leitura de arquivo parcial.")
        except Exception as e:
            print(f"[Monitor] ERRO INESPERADO: {e}")

        try:
            LocksManager._load_locks()
        except Exception as e:
            print(f"[Monitor] ERRO lendo JSON: {e}")

        time.sleep(0.2)
    print("[Monitor] Finalizou.")


if __name__ == "__main__":
    _prepare_environment()
    _configure_test_paths()
    tests = []

    tm = threading.Thread(target=monitor_simulator)
    tm.start()

    start_time = time.time()
    for i in range(1, 7):
        p = multiprocessing.Process(target=worker_machine, args=(i,))
        tests.append(p)
        p.start()

    for p in tests:
        p.join()

    tm.join()

    print(f"Stress test concluido em {time.time() - start_time:.2f} segundos.")
    final_locks = LocksManager._load_locks()
    print(f"Locks residuais (esperado 0): {len(final_locks)}")

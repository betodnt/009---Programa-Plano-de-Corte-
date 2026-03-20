import json
import os
import time

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCK_TIMEOUT = 3600

def _get_locks_file():
    try:
        from core.config import ConfigManager
        return ConfigManager.get_locks_file_path()
    except Exception:
        return os.path.join(_PROJECT_ROOT, "active_locks.json")

class LocksManager:

    @staticmethod
    def _load_locks():
        locks_file = _get_locks_file()
        if not os.path.exists(locks_file):
            return {}
        try:
            with open(locks_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def _save_locks(locks):
        locks_file = _get_locks_file()
        with open(locks_file, 'w', encoding='utf-8') as f:
            json.dump(locks, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _clean_expired_locks(locks):
        current_time = time.time()
        expired = [k for k, v in locks.items()
                   if current_time - v.get('timestamp', 0) > LOCK_TIMEOUT]
        for k in expired:
            del locks[k]
        return locks

    @staticmethod
    def acquire_lock(maquina, saida, operador="", pedido=""):
        locks = LocksManager._load_locks()
        locks = LocksManager._clean_expired_locks(locks)
        lock_key = f"{maquina}|{saida}"
        locks[lock_key] = {
            'maquina': maquina,
            'saida': saida,
            'operador': operador,
            'pedido': pedido,
            'pid': os.getpid(),
            'timestamp': time.time()
        }
        LocksManager._save_locks(locks)

    @staticmethod
    def release_lock(maquina, saida):
        locks = LocksManager._load_locks()
        lock_key = f"{maquina}|{saida}"
        if lock_key in locks:
            del locks[lock_key]
            LocksManager._save_locks(locks)

    @staticmethod
    def release_all_locks_for_pid():
        locks = LocksManager._load_locks()
        current_pid = os.getpid()
        to_remove = [k for k, v in locks.items() if v.get('pid') == current_pid]
        for k in to_remove:
            del locks[k]
        if to_remove:
            LocksManager._save_locks(locks)

    @staticmethod
    def is_locked(maquina, saida):
        locks = LocksManager._load_locks()
        locks = LocksManager._clean_expired_locks(locks)
        lock_key = f"{maquina}|{saida}"
        if lock_key in locks:
            if locks[lock_key].get('pid') == os.getpid():
                return False
            return True
        return False

    @staticmethod
    def get_locked_saidas(maquina):
        locks = LocksManager._load_locks()
        locks = LocksManager._clean_expired_locks(locks)
        locked = []
        for lock_data in locks.values():
            if lock_data.get('maquina') == maquina:
                if lock_data.get('pid') != os.getpid():
                    saida = lock_data.get('saida')
                    if saida and saida not in locked:
                        locked.append(saida)
        return locked

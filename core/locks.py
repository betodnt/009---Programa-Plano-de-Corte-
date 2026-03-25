import json
import os
import time
from contextlib import contextmanager

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCK_TIMEOUT = 14400 # 4 horas (estendido para permitir alerta visual no Monitor antes de expirar)

@contextmanager
def _json_file_lock(file_path):
    """Bloqueio simples para evitar corrupção do JSON por concorrência"""
    lock_path = file_path + ".writelock"
    start_time = time.time()
    acquired = False
    try:
        while time.time() - start_time < 5:  # Timeout de 5s para adquirir lock
            try:
                # Tenta criar arquivo de lock de forma atômica
                fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                acquired = True
                break
            except FileExistsError:
                # Se o lock for muito velho (>10s), assume que travou e remove
                try:
                    if time.time() - os.stat(lock_path).st_mtime > 10:
                        os.remove(lock_path)
                except OSError:
                    pass
                time.sleep(0.1)
        yield acquired
    finally:
        if acquired:
            try:
                os.remove(lock_path)
            except OSError:
                pass

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
        # Usa o lock para garantir que ninguém mais está escrevendo
        with _json_file_lock(locks_file) as acquired:
            if not acquired:
                # Se não conseguiu lock, loga ou ignora, mas evita corrupção
                return
            with open(locks_file, 'w', encoding='utf-8') as f:
                json.dump(locks, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _modify_locks_safely(callback):
        locks_file = _get_locks_file()
        with _json_file_lock(locks_file) as acquired:
            if not acquired:
                return False
            locks = {}
            if os.path.exists(locks_file):
                try:
                    with open(locks_file, 'r', encoding='utf-8') as f:
                        locks = json.load(f)
                except Exception:
                    pass
            locks = LocksManager._clean_expired_locks(locks)
            locks = callback(locks)
            if locks is not None:
                try:
                    with open(locks_file, 'w', encoding='utf-8') as f:
                        json.dump(locks, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
            return True

    @staticmethod
    def _clean_expired_locks(locks):
        current_time = time.time()
        # Remove locks antigos (> 1 hora)
        expired = [k for k, v in locks.items()
                   if current_time - v.get('timestamp', 0) > LOCK_TIMEOUT]
        for k in expired:
            del locks[k]
        return locks

    @staticmethod
    def acquire_lock(maquina, saida, operador="", pedido=""):
        def _add_lock(locks):
            lock_key = f"{maquina}|{saida}"
            locks[lock_key] = {
                'maquina': maquina,
                'saida': saida,
                'operador': operador,
                'pedido': pedido,
                'pid': os.getpid(),
                'timestamp': time.time()
            }
            return locks
        LocksManager._modify_locks_safely(_add_lock)

    @staticmethod
    def release_lock(maquina, saida):
        def _del_lock(locks):
            lock_key = f"{maquina}|{saida}"
            if lock_key in locks:
                del locks[lock_key]
            return locks
        LocksManager._modify_locks_safely(_del_lock)

    @staticmethod
    def release_all_locks_for_pid():
        def _del_pid_locks(locks):
            current_pid = os.getpid()
            to_remove = [k for k, v in locks.items() if v.get('pid') == current_pid]
            for k in to_remove:
                del locks[k]
            return locks
        LocksManager._modify_locks_safely(_del_pid_locks)

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

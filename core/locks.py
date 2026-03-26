import json
import os
import socket
import tempfile
import time

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCK_TIMEOUT = 14400  # 4 horas


class SimpleFileLock:
    """Mecanismo simples de trava para evitar concorrencia em rede."""

    def __init__(self, lock_path):
        self.lock_path = lock_path

    def acquire(self, timeout=5.0):
        start = time.time()
        while time.time() - start < timeout:
            try:
                fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return True
            except FileExistsError:
                try:
                    if os.path.exists(self.lock_path) and time.time() - os.path.getmtime(self.lock_path) > 10:
                        try:
                            os.remove(self.lock_path)
                        except OSError:
                            pass
                except OSError:
                    pass
                time.sleep(0.1)
            except OSError:
                time.sleep(0.1)
        return False

    def release(self):
        try:
            os.remove(self.lock_path)
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
    def _get_owner_id():
        return f"{socket.gethostname()}-{os.getpid()}"

    @staticmethod
    def _now():
        return time.time()

    @staticmethod
    def _load_locks():
        locks_file = _get_locks_file()
        if not os.path.exists(locks_file):
            return {}
        try:
            with open(locks_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, OSError):
            return {}

    @staticmethod
    def _save_locks(locks):
        locks_file = _get_locks_file()
        os.makedirs(os.path.dirname(locks_file) or ".", exist_ok=True)

        for attempt in range(3):
            try:
                temp_fd, temp_path = tempfile.mkstemp(
                    dir=os.path.dirname(locks_file) or ".",
                    prefix=".locks_tmp_",
                    suffix=".json",
                )
                try:
                    with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                        json.dump(locks, f, ensure_ascii=False, indent=2)
                    os.replace(temp_path, locks_file)
                    return True
                except Exception:
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass
                    raise
            except Exception:
                if attempt < 2:
                    time.sleep(0.1 * (attempt + 1))
                else:
                    print(f"[LOCKS] Falha ao salvar locks apos 3 tentativas: {locks_file}")
                    return False
        return False

    @staticmethod
    def _modify_locks_safely(callback):
        locks_file = _get_locks_file()
        lock_manager = SimpleFileLock(locks_file + ".lock")

        if lock_manager.acquire(timeout=7.0):
            try:
                locks = LocksManager._load_locks()
                locks = LocksManager._clean_expired_locks(locks)
                locks = callback(locks)
                if locks is not None:
                    return LocksManager._save_locks(locks)
                return False
            except Exception as e:
                print(f"[LOCKS] Erro critico na modificacao: {e}")
                return False
            finally:
                lock_manager.release()
        print("[LOCKS] Erro: Timeout aguardando liberacao do arquivo de rede.")
        return False

    @staticmethod
    def get_active_locks():
        locks = LocksManager._load_locks()
        return LocksManager._clean_expired_locks(locks)

    @staticmethod
    def _clean_expired_locks(locks):
        current_time = LocksManager._now()
        expired = [
            k
            for k, v in locks.items()
            if current_time - v.get("heartbeat_at", v.get("timestamp", 0)) > LOCK_TIMEOUT
        ]
        for key in expired:
            del locks[key]
        return locks

    @staticmethod
    def acquire_lock(maquina, saida, operador="", pedido="", operation_id=""):
        outcome = {"ok": False}

        def _add_lock(locks):
            lock_key = f"{maquina}|{saida}"
            existing = locks.get(lock_key)
            if existing and existing.get("owner_id") != LocksManager._get_owner_id():
                return None

            now = LocksManager._now()
            locks[lock_key] = {
                "maquina": maquina,
                "saida": saida,
                "operador": operador,
                "pedido": pedido,
                "operation_id": operation_id,
                "owner_id": LocksManager._get_owner_id(),
                "timestamp": existing.get("timestamp", now) if existing else now,
                "heartbeat_at": now,
            }
            outcome["ok"] = True
            return locks

        result = LocksManager._modify_locks_safely(_add_lock)
        if result and outcome["ok"]:
            print(f"[LOCKS] Lock adquirido: {maquina}|{saida} (operador: {operador})")
        else:
            print(f"[LOCKS] FALHA ao adquirir lock: {maquina}|{saida}")
        return bool(result and outcome["ok"])

    @staticmethod
    def release_lock(maquina, saida, force=False):
        released = {"ok": False}

        def _del_lock(locks):
            lock_key = f"{maquina}|{saida}"
            existing = locks.get(lock_key)
            if existing and (force or existing.get("owner_id") == LocksManager._get_owner_id()):
                del locks[lock_key]
                released["ok"] = True
            return locks

        result = LocksManager._modify_locks_safely(_del_lock)
        if result and released["ok"]:
            print(f"[LOCKS] Lock liberado: {maquina}|{saida}")
        else:
            print(f"[LOCKS] FALHA ao liberar lock: {maquina}|{saida}")
        return bool(result and released["ok"])

    @staticmethod
    def touch_lock(maquina, saida):
        touched = {"ok": False}

        def _touch(locks):
            lock_key = f"{maquina}|{saida}"
            existing = locks.get(lock_key)
            if not existing or existing.get("owner_id") != LocksManager._get_owner_id():
                return None
            existing["heartbeat_at"] = LocksManager._now()
            touched["ok"] = True
            return locks

        result = LocksManager._modify_locks_safely(_touch)
        return bool(result and touched["ok"])

    @staticmethod
    def release_all_locks_for_pid():
        def _del_pid_locks(locks):
            owner_id = LocksManager._get_owner_id()
            to_remove = [k for k, v in locks.items() if v.get("owner_id") == owner_id]
            for key in to_remove:
                del locks[key]
            return locks

        LocksManager._modify_locks_safely(_del_pid_locks)

    @staticmethod
    def is_locked(maquina, saida):
        locks = LocksManager._load_locks()
        locks = LocksManager._clean_expired_locks(locks)
        lock_key = f"{maquina}|{saida}"
        if lock_key in locks:
            if locks[lock_key].get("owner_id") == LocksManager._get_owner_id():
                return False
            return True
        return False

    @staticmethod
    def get_locked_saidas(maquina):
        locks = LocksManager._load_locks()
        locks = LocksManager._clean_expired_locks(locks)
        locked = []
        for lock_data in locks.values():
            if lock_data.get("maquina") == maquina and lock_data.get("owner_id") != LocksManager._get_owner_id():
                saida = lock_data.get("saida")
                if saida and saida not in locked:
                    locked.append(saida)
        return locked

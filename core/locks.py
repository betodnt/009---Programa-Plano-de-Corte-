import json
import os
import time

LOCKS_FILE = "active_locks.json"
LOCK_TIMEOUT = 3600  # 1 hora em segundos

class LocksManager:
    """Gerencia locks de máquinas e saídas CNC em uso por outras instâncias"""
    
    @staticmethod
    def _load_locks():
        """Carrega arquivo de locks"""
        if not os.path.exists(LOCKS_FILE):
            return {}
        try:
            with open(LOCKS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    @staticmethod
    def _save_locks(locks):
        """Salva arquivo de locks"""
        os.makedirs(os.path.dirname(LOCKS_FILE) or '.', exist_ok=True)
        with open(LOCKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(locks, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def _clean_expired_locks(locks):
        """Remove locks expirados"""
        current_time = time.time()
        locks_to_remove = []
        
        for key, lock_data in locks.items():
            if current_time - lock_data.get('timestamp', 0) > LOCK_TIMEOUT:
                locks_to_remove.append(key)
        
        for key in locks_to_remove:
            del locks[key]
        
        return locks
    
    @staticmethod
    def acquire_lock(maquina, saida):
        """Adquire lock para máquina + saída CNC"""
        import os as os_module
        locks = LocksManager._load_locks()
        locks = LocksManager._clean_expired_locks(locks)
        
        # Cria chave única para máquina + saída
        lock_key = f"{maquina}|{saida}"
        
        locks[lock_key] = {
            'maquina': maquina,
            'saida': saida,
            'pid': os_module.getpid(),
            'timestamp': time.time()
        }
        
        LocksManager._save_locks(locks)
    
    @staticmethod
    def release_lock(maquina, saida):
        """Libera lock para máquina + saída CNC"""
        locks = LocksManager._load_locks()
        lock_key = f"{maquina}|{saida}"
        
        if lock_key in locks:
            del locks[lock_key]
            LocksManager._save_locks(locks)
    
    @staticmethod
    def is_locked(maquina, saida):
        """Verifica se máquina + saída está bloqueada por outra instância"""
        import os as os_module
        locks = LocksManager._load_locks()
        locks = LocksManager._clean_expired_locks(locks)
        
        lock_key = f"{maquina}|{saida}"
        
        if lock_key in locks:
            # Se for da mesma instância (PID), não está bloqueada
            if locks[lock_key].get('pid') == os_module.getpid():
                return False
            return True
        
        return False
    
    @staticmethod
    def get_locked_saidas(maquina):
        """Retorna lista de saídas bloqueadas para uma máquina específica"""
        import os as os_module
        locks = LocksManager._load_locks()
        locks = LocksManager._clean_expired_locks(locks)
        
        locked = []
        for key, lock_data in locks.items():
            if lock_data.get('maquina') == maquina:
                # Se não for da mesma instância
                if lock_data.get('pid') != os_module.getpid():
                    saida = lock_data.get('saida')
                    if saida and saida not in locked:
                        locked.append(saida)
        
        return locked

import json
import os
import time

from core.config import ConfigManager


class LoggingService:
    @staticmethod
    def _logs_dir():
        logs_dir = ConfigManager.get_logs_dir()
        os.makedirs(logs_dir, exist_ok=True)
        return logs_dir

    @staticmethod
    def _machine_slug():
        machine = ConfigManager.get_current_machine() or "maquina"
        return "".join(ch if ch.isalnum() else "_" for ch in machine).strip("_") or "maquina"

    @staticmethod
    def _log_path():
        date_str = time.strftime("%Y-%m-%d")
        filename = f"{LoggingService._machine_slug()}_{date_str}.log"
        return os.path.join(LoggingService._logs_dir(), filename)

    @staticmethod
    def write(event_type, **fields):
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": event_type,
            "machine": ConfigManager.get_current_machine(),
        }
        entry.update(fields)
        try:
            with open(LoggingService._log_path(), "a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

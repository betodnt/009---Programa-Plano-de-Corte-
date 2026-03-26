import os

from core.config import ConfigManager
from core.logging_service import LoggingService
from core.sync import SyncManager


class ApplicationService:
    @staticmethod
    def flush_pending_sync():
        try:
            result = SyncManager.flush_pending()
            LoggingService.write("sync_flush", result=result)
            return result
        except Exception as exc:
            result = {"synced": 0, "errors": 1, "remaining": 0}
            LoggingService.write("sync_flush_error", error=str(exc), result=result)
            return result

    @staticmethod
    def get_runtime_status():
        queue_status = SyncManager.get_queue_status()
        server_path = ConfigManager.get_server_path()
        locks_path = ConfigManager.get_locks_file_path()
        xml_path = ConfigManager.get_k8_data_path()
        logs_dir = ConfigManager.get_logs_dir()

        server_ok = os.path.exists(server_path)
        locks_dir_ok = os.path.exists(os.path.dirname(locks_path) or ".")
        xml_dir_ok = os.path.exists(os.path.dirname(xml_path) or ".")
        logs_dir_ok = os.path.exists(logs_dir)

        if queue_status["pending"] > 0:
            summary = f"Contingencia ativa: {queue_status['pending']} pendencia(s)"
            level = "warning"
        elif server_ok and locks_dir_ok and xml_dir_ok:
            summary = "Rede e gravacao OK"
            level = "ok"
        else:
            summary = "Verificar caminhos de rede"
            level = "error"

        return {
            "summary": summary,
            "level": level,
            "server_ok": server_ok,
            "server_path": server_path,
            "locks_dir_ok": locks_dir_ok,
            "locks_path": locks_path,
            "xml_dir_ok": xml_dir_ok,
            "xml_path": xml_path,
            "logs_dir_ok": logs_dir_ok,
            "logs_dir": logs_dir,
            "queue_status": queue_status,
        }

    @staticmethod
    def get_diagnostics_report():
        status = ApplicationService.get_runtime_status()
        queue = status["queue_status"]
        lines = [
            f"Resumo: {status['summary']}",
            "",
            f"Acervo CNC: {'OK' if status['server_ok'] else 'FALHA'}",
            status["server_path"],
            "",
            f"Diretorio do locks: {'OK' if status['locks_dir_ok'] else 'FALHA'}",
            status["locks_path"],
            "",
            f"Diretorio do XML: {'OK' if status['xml_dir_ok'] else 'FALHA'}",
            status["xml_path"],
            "",
            f"Diretorio de logs: {'OK' if status['logs_dir_ok'] else 'FALHA'}",
            status["logs_dir"],
            "",
            f"Fila offline pendente: {queue['pending']}",
            f"Idade da pendencia mais antiga: {queue['oldest_age_seconds']}s",
            queue["queue_dir"],
        ]
        return "\n".join(lines)

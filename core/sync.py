import json
import os
import time
import uuid

from core.config import ConfigManager


class SyncManager:
    @staticmethod
    def _queue_dir():
        queue_dir = ConfigManager.get_offline_queue_dir()
        os.makedirs(queue_dir, exist_ok=True)
        return queue_dir

    @staticmethod
    def _event_path():
        filename = f"{int(time.time() * 1000)}_{uuid.uuid4().hex}.json"
        return os.path.join(SyncManager._queue_dir(), filename)

    @staticmethod
    def enqueue(event_type, payload):
        event = {
            "event_type": event_type,
            "payload": payload,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        path = SyncManager._event_path()
        with open(path, "w", encoding="utf-8") as event_file:
            json.dump(event, event_file, ensure_ascii=False, indent=2)
        return path

    @staticmethod
    def enqueue_entrada(file_path, pedido, operador, maquina, retalho, saida, tipo, dt_inicio, operation_id=""):
        return SyncManager.enqueue(
            "save_entrada",
            {
                "file_path": file_path,
                "pedido": pedido,
                "operador": operador,
                "maquina": maquina,
                "retalho": retalho,
                "saida": saida,
                "tipo": tipo,
                "dt_inicio": dt_inicio,
                "operation_id": operation_id,
            },
        )

    @staticmethod
    def enqueue_termino(file_path, pedido, operador, maquina, dt_termino, tempo_decorrido, operation_id="", saida=""):
        return SyncManager.enqueue(
            "save_termino",
            {
                "file_path": file_path,
                "pedido": pedido,
                "operador": operador,
                "maquina": maquina,
                "dt_termino": dt_termino,
                "tempo_decorrido": tempo_decorrido,
                "operation_id": operation_id,
                "saida": saida,
            },
        )

    @staticmethod
    def flush_pending(max_items=50):
        from core.database import DatabaseManager

        queue_dir = SyncManager._queue_dir()
        pending_files = sorted(
            os.path.join(queue_dir, name)
            for name in os.listdir(queue_dir)
            if name.lower().endswith(".json")
        )

        synced = 0
        errors = 0
        for path in pending_files[:max_items]:
            try:
                with open(path, "r", encoding="utf-8") as event_file:
                    event = json.load(event_file)
                payload = event.get("payload", {})
                event_type = event.get("event_type")

                if event_type == "save_entrada":
                    ok, _ = DatabaseManager.save_entrada(
                        payload.get("file_path", ""),
                        payload.get("pedido", ""),
                        payload.get("operador", ""),
                        payload.get("maquina", ""),
                        payload.get("retalho", ""),
                        payload.get("saida", ""),
                        payload.get("tipo", ""),
                        payload.get("dt_inicio", ""),
                        payload.get("operation_id", ""),
                    )
                elif event_type == "save_termino":
                    ok, _ = DatabaseManager.save_termino(
                        payload.get("file_path", ""),
                        payload.get("pedido", ""),
                        payload.get("operador", ""),
                        payload.get("maquina", ""),
                        payload.get("dt_termino", ""),
                        payload.get("tempo_decorrido", ""),
                        payload.get("operation_id", ""),
                        payload.get("saida", ""),
                    )
                else:
                    ok = False

                if ok:
                    os.remove(path)
                    synced += 1
                else:
                    errors += 1
            except Exception:
                errors += 1

        remaining = len(
            [name for name in os.listdir(queue_dir) if name.lower().endswith(".json")]
        )
        return {"synced": synced, "errors": errors, "remaining": remaining}

    @staticmethod
    def get_queue_status():
        queue_dir = SyncManager._queue_dir()
        pending_files = sorted(
            os.path.join(queue_dir, name)
            for name in os.listdir(queue_dir)
            if name.lower().endswith(".json")
        )
        oldest_age_seconds = 0
        if pending_files:
            try:
                oldest_age_seconds = max(0, int(time.time() - os.path.getmtime(pending_files[0])))
            except OSError:
                oldest_age_seconds = 0
        return {
            "queue_dir": queue_dir,
            "pending": len(pending_files),
            "oldest_age_seconds": oldest_age_seconds,
        }

import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime

from core.config import ConfigManager
from core.locks import LocksManager


WARNING_THRESHOLD = 3600


class MonitorService:
    @staticmethod
    def load_snapshot(view_date, last_xml_mtime=0, cached_history_items=None):
        cached_history_items = cached_history_items or []
        payload = {
            "active_items": [],
            "history_items": [],
            "history_total": 0,
            "count": 0,
            "status_text": time.strftime("atualizado %H:%M:%S"),
            "status_color": "#e0e0e0",
            "xml_mtime": last_xml_mtime,
            "cached_history_items": cached_history_items,
        }

        today_str = datetime.now().strftime("%d/%m/%Y")
        locks = LocksManager.get_active_locks() if view_date == today_str else {}
        now = time.time()

        for key, data in sorted(locks.items(), key=lambda item: item[1].get("timestamp", 0)):
            operador = data.get("operador") or "-"
            maquina = data.get("maquina") or "-"
            pedido = data.get("pedido") or "-"
            plano = data.get("saida") or "-"
            elapsed = int(now - data.get("timestamp", now))
            duracao = MonitorService.format_duration(elapsed)
            tags = ("delayed",) if elapsed > WARNING_THRESHOLD else ("active",)
            payload["active_items"].append(
                {
                    "iid": key,
                    "values": (operador, maquina, pedido, plano, duracao, ""),
                    "tags": tags,
                }
            )

        xml_path = ConfigManager.get_k8_data_path(view_date)
        history_items, xml_mtime, status_text, status_color = MonitorService._load_history(
            xml_path,
            last_xml_mtime,
            cached_history_items,
        )

        payload["history_items"] = history_items[:100]
        payload["history_total"] = len(history_items)
        payload["count"] = len(payload["active_items"])
        payload["xml_mtime"] = xml_mtime
        payload["cached_history_items"] = history_items
        payload["status_text"] = status_text
        payload["status_color"] = status_color
        return payload

    @staticmethod
    def _load_history(xml_path, last_xml_mtime, cached_history_items):
        if not os.path.exists(xml_path):
            return [], 0, time.strftime("atualizado %H:%M:%S"), "#e0e0e0"

        try:
            current_mtime = os.stat(xml_path).st_mtime
            if current_mtime == last_xml_mtime and cached_history_items:
                return cached_history_items, current_mtime, time.strftime("atualizado %H:%M:%S"), "#e0e0e0"

            tree = ET.parse(xml_path)
            root = tree.getroot()
            temp_items = []
            for entrada in root.findall("Entrada"):
                if entrada.find("DataHoraTermino") is None:
                    continue
                operador = entrada.findtext("Operador", "-")
                maquina = entrada.findtext("Maquina", "-")
                pedido = entrada.findtext("Pedido", "-")
                plano = entrada.findtext("Saida", "-")
                duracao = entrada.findtext("TempoDecorrido", "-")
                dt_term = entrada.findtext("DataHoraTermino", "")
                hora_conclusao = dt_term.split(" ")[1] if " " in dt_term else dt_term
                temp_items.append((operador, maquina, pedido, plano, duracao, hora_conclusao))
            history_items = temp_items[::-1]
            return history_items, current_mtime, time.strftime("atualizado %H:%M:%S"), "#e0e0e0"
        except Exception:
            return cached_history_items, last_xml_mtime, "falha ao ler historico XML", "#c0392b"

    @staticmethod
    def format_duration(seconds):
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

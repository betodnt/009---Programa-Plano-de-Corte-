import os
from datetime import datetime
from dataclasses import dataclass
import uuid

from core.config import ConfigManager
from core.database import DatabaseManager
from core.locks import LocksManager
from core.logging_service import LoggingService
from core.operators import OperatorsManager
from core.sync import SyncManager


@dataclass
class OperationStart:
    operation_id: str
    start_time: datetime
    src_path: str
    dst_path: str


@dataclass
class OperationFinish:
    operation_id: str
    end_time: datetime
    elapsed_time: str
    src_path: str
    dst_path: str


@dataclass
class CompletionFeedback:
    dialog_title: str
    dialog_message: str
    level: str = "info"
    nif_path: str = ""


class OperationService:
    @staticmethod
    def get_locked_saidas(maquina):
        return LocksManager.get_locked_saidas(maquina)

    @staticmethod
    def flush_pending_sync():
        return SyncManager.flush_pending()

    @staticmethod
    def validate_start(data):
        saida = data.get("saida", "")
        if not saida:
            return False, ""

        operador = data.get("operador", "").strip()
        if not operador:
            return False, "Informe o nome do operador antes de iniciar."

        if LocksManager.is_locked(data["maquina"], saida):
            return (
                False,
                f"A saida '{saida}' ja esta sendo usada por outro operador na maquina '{data['maquina']}'.\n\nEscolha outra saida ou aguarde a finalizacao.",
            )

        return True, ""

    @staticmethod
    def prepare_start(data):
        ok, message = OperationService.validate_start(data)
        if not ok:
            LoggingService.write("start_validation_failed", data=data, reason=message)
            return None, message

        start_time = datetime.now()
        operation_id = uuid.uuid4().hex

        OperatorsManager.add_operator(data["operador"])
        if not LocksManager.acquire_lock(
            data["maquina"],
            data["saida"],
            data["operador"],
            data["pedido"],
            operation_id,
        ):
            LoggingService.write(
                "lock_acquire_failed",
                operation_id=operation_id,
                pedido=data["pedido"],
                operador=data["operador"],
                saida=data["saida"],
            )
            return None, "Nao foi possivel acessar o arquivo de controle na rede. Verifique se outra maquina esta salvando dados."

        src_path = os.path.join(ConfigManager.get_server_path(), data["saida"])
        dst_path = os.path.join(ConfigManager.get_saidas_cnc_path(), data["saida"])
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)

        LoggingService.write(
            "start_prepared",
            operation_id=operation_id,
            pedido=data["pedido"],
            operador=data["operador"],
            maquina=data["maquina"],
            saida=data["saida"],
            src_path=src_path,
            dst_path=dst_path,
        )
        return OperationStart(operation_id, start_time, src_path, dst_path), ""

    @staticmethod
    def rollback_start(data):
        LoggingService.write(
            "start_rollback",
            pedido=data.get("pedido", ""),
            operador=data.get("operador", ""),
            maquina=data.get("maquina", ""),
            saida=data.get("saida", ""),
        )
        LocksManager.release_lock(data["maquina"], data["saida"])

    @staticmethod
    def complete_start(data, operation_start):
        dt_inicio = operation_start.start_time.strftime("%Y-%m-%d %H:%M:%S")
        file_path = ConfigManager.get_k8_data_path()
        ok, err = DatabaseManager.save_entrada(
            file_path,
            data["pedido"],
            data["operador"],
            data["maquina"],
            data["retalho"],
            data["saida"],
            data["tipo"],
            dt_inicio,
            operation_start.operation_id,
        )

        if not ok:
            queue_path = SyncManager.enqueue_entrada(
                file_path,
                data["pedido"],
                data["operador"],
                data["maquina"],
                data["retalho"],
                data["saida"],
                data["tipo"],
                dt_inicio,
                operation_start.operation_id,
            )
            feedback = CompletionFeedback(
                dialog_title="Registro em contingencia",
                dialog_message=f"{err}\n\nO inicio foi salvo localmente e sera sincronizado quando a rede voltar.\nFila local: {queue_path}",
                level="warning",
            )
            LoggingService.write(
                "start_saved_offline",
                operation_id=operation_start.operation_id,
                pedido=data["pedido"],
                operador=data["operador"],
                maquina=data["maquina"],
                saida=data["saida"],
                queue_path=queue_path,
                error=err,
            )
        else:
            feedback = CompletionFeedback(dialog_title="", dialog_message="", level="info")
            LoggingService.write(
                "start_saved",
                operation_id=operation_start.operation_id,
                pedido=data["pedido"],
                operador=data["operador"],
                maquina=data["maquina"],
                saida=data["saida"],
                file_path=file_path,
            )

        nif_path = os.path.join(ConfigManager.get_server_path(), data["saida"].replace(".cnc", ".nif"))
        if os.path.exists(nif_path):
            feedback.nif_path = nif_path
        return feedback

    @staticmethod
    def prepare_finish(data, operation_id, elapsed_time):
        if not data.get("saida", ""):
            LoggingService.write("finish_validation_failed", operation_id=operation_id, data=data)
            return None

        end_time = datetime.now()
        src_path = os.path.join(ConfigManager.get_saidas_cnc_path(), data["saida"])
        dst_path = os.path.join(ConfigManager.get_saidas_cortadas_path(), data["saida"])
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)

        LoggingService.write(
            "finish_prepared",
            operation_id=operation_id,
            pedido=data["pedido"],
            operador=data["operador"],
            maquina=data["maquina"],
            saida=data["saida"],
            elapsed_time=elapsed_time,
            src_path=src_path,
            dst_path=dst_path,
        )
        return OperationFinish(operation_id, end_time, elapsed_time, src_path, dst_path)

    @staticmethod
    def complete_finish(data, operation_finish, success_title):
        dt_termino = operation_finish.end_time.strftime("%Y-%m-%d %H:%M:%S")
        file_path = ConfigManager.get_k8_data_path()
        ok, err = DatabaseManager.save_termino(
            file_path,
            data["pedido"],
            data["operador"],
            data["maquina"],
            dt_termino,
            operation_finish.elapsed_time,
            operation_finish.operation_id,
            data["saida"],
        )
        LocksManager.release_lock(data["maquina"], data["saida"])

        if ok:
            LoggingService.write(
                "finish_saved",
                operation_id=operation_finish.operation_id,
                pedido=data["pedido"],
                operador=data["operador"],
                maquina=data["maquina"],
                saida=data["saida"],
                elapsed_time=operation_finish.elapsed_time,
                file_path=file_path,
            )
            return CompletionFeedback(dialog_title="Sucesso", dialog_message=success_title, level="info")

        queue_path = SyncManager.enqueue_termino(
            file_path,
            data["pedido"],
            data["operador"],
            data["maquina"],
            dt_termino,
            operation_finish.elapsed_time,
            operation_finish.operation_id,
            data["saida"],
        )
        LoggingService.write(
            "finish_saved_offline",
            operation_id=operation_finish.operation_id,
            pedido=data["pedido"],
            operador=data["operador"],
            maquina=data["maquina"],
            saida=data["saida"],
            elapsed_time=operation_finish.elapsed_time,
            queue_path=queue_path,
            error=err,
        )
        return CompletionFeedback(
            dialog_title="Finalizado com contingencia",
            dialog_message=f"{success_title}\n\nMas houve falha ao salvar o historico remoto:\n{err}\n\nO termino foi salvo localmente e sera sincronizado quando a rede voltar.\nFila local: {queue_path}",
            level="warning",
        )

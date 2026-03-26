import os
import shutil
import tempfile
import time
import xml.etree.ElementTree as ET
from contextlib import contextmanager


class SimpleLockFile:
    def __init__(self, lock_path):
        self.lock_path = lock_path

    def tryLock(self, timeout_ms=5000):
        start_time = time.time()
        timeout_sec = timeout_ms / 1000.0
        while True:
            try:
                fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, f"locked_by_{os.getpid()}".encode())
                os.close(fd)
                return True
            except FileExistsError:
                try:
                    stats = os.stat(self.lock_path)
                    if time.time() - stats.st_mtime > 10.0:
                        os.remove(self.lock_path)
                        continue
                except OSError:
                    pass
            except OSError:
                pass
            if time.time() - start_time > timeout_sec:
                return False
            time.sleep(0.2)

    def unlock(self):
        try:
            if os.path.exists(self.lock_path):
                os.remove(self.lock_path)
                return True
        except OSError:
            pass
        return False


@contextmanager
def xml_lock(file_path):
    lock_path = file_path + ".lock"
    lock = SimpleLockFile(lock_path)
    acquired = lock.tryLock(5000)
    try:
        yield acquired
    finally:
        if acquired:
            lock.unlock()


class DatabaseManager:
    @staticmethod
    def _write_xml_atomic(tree, file_path):
        dirpath = os.path.dirname(file_path) or "."
        os.makedirs(dirpath, exist_ok=True)
        temp_fd, temp_path = tempfile.mkstemp(dir=dirpath, prefix=".dados_tmp_", suffix=".xml")
        try:
            with os.fdopen(temp_fd, "wb") as temp_file:
                tree.write(temp_file, encoding="utf-8", xml_declaration=True)
            os.replace(temp_path, file_path)
        except Exception:
            try:
                os.remove(temp_path)
            except OSError:
                pass
            raise

    @staticmethod
    def _auto_backup(file_path):
        try:
            dirpath = os.path.dirname(file_path)
            base = os.path.basename(file_path)
            name, ext = os.path.splitext(base)
            backup_path = os.path.join(dirpath, f"{name}_backup{ext}")
            shutil.copy2(file_path, backup_path)
        except Exception:
            pass

    @staticmethod
    def initialize_xml_if_needed(file_path):
        if not os.path.exists(file_path):
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                root = ET.Element("Dados")
                DatabaseManager._write_xml_atomic(ET.ElementTree(root), file_path)
            except Exception:
                pass

    @staticmethod
    def save_entrada(file_path, pedido, operador, maquina, retalho, saida, tipo, dt_inicio, operation_id=""):
        DatabaseManager.initialize_xml_if_needed(file_path)
        with xml_lock(file_path) as acquired:
            if not acquired:
                return False, "O servidor esta ocupado salvando outro registro. Tente novamente em alguns segundos."
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                entrada = None
                if operation_id:
                    for existing in root.findall("Entrada"):
                        if existing.findtext("OperationId", "") == str(operation_id):
                            entrada = existing
                            break

                if entrada is None:
                    entrada = ET.SubElement(root, "Entrada")

                for tag, value in (
                    ("Pedido", pedido),
                    ("Operador", operador),
                    ("Maquina", maquina),
                    ("Chapa", retalho),
                    ("Saida", saida),
                    ("Tipo", tipo),
                    ("DataHoraInicio", dt_inicio),
                    ("OperationId", operation_id),
                    ("Instancia", os.getpid()),
                ):
                    node = entrada.find(tag)
                    if node is None:
                        node = ET.SubElement(entrada, tag)
                    if not node.text:
                        node.text = str(value)
                DatabaseManager._write_xml_atomic(tree, file_path)
                DatabaseManager._auto_backup(file_path)
                return True, ""
            except Exception as e:
                if not os.path.exists(file_path):
                    try:
                        root = ET.Element("Dados")
                        entrada = ET.SubElement(root, "Entrada")
                        ET.SubElement(entrada, "Pedido").text = str(pedido)
                        ET.SubElement(entrada, "Operador").text = str(operador)
                        ET.SubElement(entrada, "Maquina").text = str(maquina)
                        ET.SubElement(entrada, "Chapa").text = str(retalho)
                        ET.SubElement(entrada, "Saida").text = str(saida)
                        ET.SubElement(entrada, "Tipo").text = str(tipo)
                        ET.SubElement(entrada, "DataHoraInicio").text = str(dt_inicio)
                        ET.SubElement(entrada, "OperationId").text = str(operation_id)
                        ET.SubElement(entrada, "Instancia").text = str(os.getpid())
                        DatabaseManager._write_xml_atomic(ET.ElementTree(root), file_path)
                        DatabaseManager._auto_backup(file_path)
                        return True, ""
                    except Exception as inner_e:
                        return False, f"Erro ao criar novo XML: {inner_e}"
                return False, f"Erro ao ler XML (arquivo corrompido ou bloqueado): {e}"

    @staticmethod
    def save_termino(file_path, pedido, operador, maquina, dt_termino, tempo_decorrido, operation_id="", saida=""):
        DatabaseManager.initialize_xml_if_needed(file_path)
        with xml_lock(file_path) as acquired:
            if not acquired:
                return False, "Banco XML bloqueado no momento de finalizar. Finalize de novo."
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                found = False
                for entrada in reversed(root.findall("Entrada")):
                    op_tag = entrada.findtext("OperationId", "")
                    if operation_id and op_tag == str(operation_id):
                        if entrada.find("DataHoraTermino") is not None:
                            return True, ""
                        ET.SubElement(entrada, "DataHoraTermino").text = str(dt_termino)
                        ET.SubElement(entrada, "TempoDecorrido").text = str(tempo_decorrido)
                        found = True
                        break

                    if entrada.find("DataHoraTermino") is not None:
                        continue

                    p_tag = entrada.find("Pedido")
                    m_tag = entrada.findtext("Maquina", "")
                    s_tag = entrada.findtext("Saida", "")
                    if (
                        not operation_id
                        and p_tag is not None
                        and p_tag.text == str(pedido)
                        and m_tag == str(maquina)
                        and (not saida or s_tag == str(saida))
                    ):
                        ET.SubElement(entrada, "DataHoraTermino").text = str(dt_termino)
                        ET.SubElement(entrada, "TempoDecorrido").text = str(tempo_decorrido)
                        found = True
                        break
                if not found:
                    entrada = ET.SubElement(root, "Entrada")
                    ET.SubElement(entrada, "Pedido").text = str(pedido)
                    ET.SubElement(entrada, "Operador").text = str(operador)
                    ET.SubElement(entrada, "Maquina").text = str(maquina)
                    ET.SubElement(entrada, "Saida").text = str(saida) if saida else "Finalizacao Direta"
                    ET.SubElement(entrada, "OperationId").text = str(operation_id)
                    ET.SubElement(entrada, "DataHoraTermino").text = str(dt_termino)
                    ET.SubElement(entrada, "TempoDecorrido").text = str(tempo_decorrido)
                DatabaseManager._write_xml_atomic(tree, file_path)
                DatabaseManager._auto_backup(file_path)
                return True, ""
            except Exception as e:
                return False, f"Erro XML ao finalizar: {e}"

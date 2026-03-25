import os
import time
import shutil
from contextlib import contextmanager
import xml.etree.ElementTree as ET


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
            # Sleep um pouco maior para reduzir contenção de rede
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
                ET.ElementTree(root).write(file_path, encoding="utf-8", xml_declaration=True)
            except Exception:
                pass

    @staticmethod
    def save_entrada(file_path, pedido, operador, maquina, retalho, saida, tipo, dt_inicio):
        DatabaseManager.initialize_xml_if_needed(file_path)
        with xml_lock(file_path) as acquired:
            if not acquired:
                return False, "O servidor está ocupado salvando outro registro. Tente novamente em alguns segundos."
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                entrada = ET.SubElement(root, "Entrada")
                ET.SubElement(entrada, "Pedido").text = str(pedido)
                ET.SubElement(entrada, "Operador").text = str(operador)
                ET.SubElement(entrada, "Maquina").text = str(maquina)
                ET.SubElement(entrada, "Chapa").text = str(retalho)
                ET.SubElement(entrada, "Saida").text = str(saida)
                ET.SubElement(entrada, "Tipo").text = str(tipo)
                ET.SubElement(entrada, "DataHoraInicio").text = str(dt_inicio)
                ET.SubElement(entrada, "Instancia").text = str(os.getpid())
                tree.write(file_path, encoding="utf-8", xml_declaration=True)
                DatabaseManager._auto_backup(file_path)
                return True, ""
            except Exception as e:
                # CRÍTICO: Não criar novo XML se falhar o parse e o arquivo já existir
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
                        ET.SubElement(entrada, "Instancia").text = str(os.getpid())
                        ET.ElementTree(root).write(file_path, encoding="utf-8", xml_declaration=True)
                        DatabaseManager._auto_backup(file_path)
                        return True, ""
                    except Exception as inner_e:
                         return False, f"Erro ao criar novo XML: {inner_e}"
                return False, f"Erro ao ler XML (arquivo corrompido ou bloqueado): {e}"

    @staticmethod
    def save_termino(file_path, pedido, operador, maquina, dt_termino, tempo_decorrido):
        DatabaseManager.initialize_xml_if_needed(file_path)
        with xml_lock(file_path) as acquired:
            if not acquired:
                return False, "Banco XML bloqueado no momento de finalizar. Finalize de novo."
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                found = False
                for entrada in reversed(root.findall("Entrada")):
                    p_tag = entrada.find("Pedido")
                    if p_tag is not None and p_tag.text == str(pedido):
                        if entrada.find("DataHoraTermino") is None:
                            ET.SubElement(entrada, "DataHoraTermino").text = str(dt_termino)
                            ET.SubElement(entrada, "TempoDecorrido").text = str(tempo_decorrido)
                            found = True
                            break
                if not found:
                    entrada = ET.SubElement(root, "Entrada")
                    ET.SubElement(entrada, "Pedido").text = str(pedido)
                    ET.SubElement(entrada, "Operador").text = str(operador)
                    ET.SubElement(entrada, "Maquina").text = str(maquina)
                    ET.SubElement(entrada, "Saida").text = "Finalizacao Direta"
                    ET.SubElement(entrada, "DataHoraTermino").text = str(dt_termino)
                    ET.SubElement(entrada, "TempoDecorrido").text = str(tempo_decorrido)
                tree.write(file_path, encoding="utf-8", xml_declaration=True)
                DatabaseManager._auto_backup(file_path)
                return True, ""
            except Exception as e:
                return False, f"Erro XML ao finalizar: {e}"

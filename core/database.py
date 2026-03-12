import os
import time
from contextlib import contextmanager

class SimpleLockFile:
    def __init__(self, lock_path):
        self.lock_path = lock_path

    def tryLock(self, timeout_ms=2000):
        start_time = time.time()
        timeout_sec = timeout_ms / 1000.0
        
        while True:
            try:
                # 'x' mode fails if file already exists
                # This is an atomic operation on Windows and POSIX
                fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, b'locked')
                os.close(fd)
                return True
            except FileExistsError:
                # File exists, check if it's a stale lock (e.g. older than 5 seconds)
                try:
                    stats = os.stat(self.lock_path)
                    if time.time() - stats.st_mtime > 5.0:
                        # Stale lock, try to remove it
                        os.remove(self.lock_path)
                        continue
                except OSError:
                    pass
            except OSError:
                pass
            
            if time.time() - start_time > timeout_sec:
                return False
                
            time.time()
            time.sleep(0.1)

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
    acquired = lock.tryLock(2000)
    try:
        yield acquired
    finally:
        if acquired:
            lock.unlock()

import xml.etree.ElementTree as ET
from xml.dom import minidom

class DatabaseManager:
    @staticmethod
    def initialize_xml_if_needed(file_path):
        if not os.path.exists(file_path):
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                root = ET.Element("Dados")
                tree = ET.ElementTree(root)
                tree.write(file_path, encoding="utf-8", xml_declaration=True)
            except OSError:
                pass

    @staticmethod
    def _prettify(elem):
        """Retorna uma string XML formatada."""
        rough_string = ET.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    @staticmethod
    def save_entrada(file_path, pedido, operador, maquina, retalho, saida, tipo, dt_inicio):
        DatabaseManager.initialize_xml_if_needed(file_path)
        with xml_lock(file_path) as acquired:
            if not acquired:
                return False, "O banco de dados XML está ocupado no momento. Tente de novo."
                
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
                
                # Salva com formatação básica
                tree.write(file_path, encoding="utf-8", xml_declaration=True)
                return True, ""
            except Exception as e:
                # Se falhar ao parsear (arquivo corrompido ou formato errado), cria novo
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
                    tree = ET.ElementTree(root)
                    tree.write(file_path, encoding="utf-8", xml_declaration=True)
                    return True, ""
                except Exception as inner_e:
                    return False, f"Erro fatal ao salvar XML: {inner_e}"

    @staticmethod
    def save_termino(file_path, pedido, operador, maquina, dt_termino, tempo_decorrido):
        DatabaseManager.initialize_xml_if_needed(file_path)
        with xml_lock(file_path) as acquired:
            if not acquired:
                return False, "Banco XML bloqueado no momento de finalizar. Finalize de novo."
                
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                
                # Busca a última entrada aberta para este pedido
                found = False
                # Iterar em ordem reversa para pegar o mais recente
                entradas = root.findall("Entrada")
                for entrada in reversed(entradas):
                    p_tag = entrada.find("Pedido")
                    if p_tag is not None and p_tag.text == str(pedido):
                        if entrada.find("DataHoraTermino") is None:
                            # Achamos a entrada aberta!
                            ET.SubElement(entrada, "DataHoraTermino").text = str(dt_termino)
                            ET.SubElement(entrada, "TempoDecorrido").text = str(tempo_decorrido)
                            found = True
                            break
                
                if not found:
                    # Cria um registro avulso
                    entrada = ET.SubElement(root, "Entrada")
                    ET.SubElement(entrada, "Pedido").text = str(pedido)
                    ET.SubElement(entrada, "Operador").text = str(operador)
                    ET.SubElement(entrada, "Maquina").text = str(maquina)
                    ET.SubElement(entrada, "Saida").text = "Finalização Direta"
                    ET.SubElement(entrada, "DataHoraTermino").text = str(dt_termino)
                    ET.SubElement(entrada, "TempoDecorrido").text = str(tempo_decorrido)
                
                tree.write(file_path, encoding="utf-8", xml_declaration=True)
                return True, ""
            except Exception as e:
                return False, f"Erro XML ao finalizar: {e}"

if __name__ == "__main__":
    # Test block to verify database operations
    test_file = os.path.join(os.path.dirname(__file__), "..", "public", "dados", "dados_test.xml")
    
    print(f"--- Iniciando testes de Banco de Dados ---")
    print(f"Arquivo de teste: {os.path.abspath(test_file)}")
    
    # 1. Teste de Entrada
    success, msg = DatabaseManager.save_entrada(
        test_file, 
        pedido="TESTE-001", 
        operador="DebugBot", 
        maquina="Virtual-CNC", 
        retalho="Sim", 
        saida="TestOut.cnc", 
        tipo="Teste", 
        dt_inicio=time.strftime("%Y-%m-%d %H:%M:%S")
    )
    
    if success:
        print("OK: Entrada salva com sucesso.")
    else:
        print(f"ERRO: Falha ao salvar entrada: {msg}")
        
    # Espera um pouco para simular tempo decorrido
    time.sleep(1)
    
    # 2. Teste de Término
    success, msg = DatabaseManager.save_termino(
        test_file, 
        pedido="TESTE-001", 
        operador="DebugBot", 
        maquina="Virtual-CNC", 
        dt_termino=time.strftime("%Y-%m-%d %H:%M:%S"), 
        tempo_decorrido="00:00:01"
    )
    
    if success:
        print("OK: Término salvo com sucesso.")
    else:
        print(f"ERRO: Falha ao finalizar: {msg}")

    print(f"--- Testes Concluídos ---")

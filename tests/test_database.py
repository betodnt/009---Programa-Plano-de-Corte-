import pytest
import os
import xml.etree.ElementTree as ET
from core.database import DatabaseManager, xml_lock

def test_initialize_xml_if_needed(tmp_path):
    xml_file = tmp_path / "test.xml"
    DatabaseManager.initialize_xml_if_needed(str(xml_file))
    assert xml_file.exists()
    tree = ET.parse(str(xml_file))
    root = tree.getroot()
    assert root.tag == "Dados"

def test_save_entrada(tmp_path):
    xml_file = tmp_path / "test.xml"
    success, error = DatabaseManager.save_entrada(
        str(xml_file), "Pedido1", "Operador1", "Maquina1", "Retalho1", "Saida1", "Tipo1", "2023-01-01 12:00:00"
    )
    assert success
    assert error == ""
    tree = ET.parse(str(xml_file))
    root = tree.getroot()
    entradas = root.findall("Entrada")
    assert len(entradas) == 1
    entrada = entradas[0]
    assert entrada.find("Pedido").text == "Pedido1"
    assert entrada.find("Operador").text == "Operador1"
    assert entrada.find("Maquina").text == "Maquina1"
    assert entrada.find("Chapa").text == "Retalho1"
    assert entrada.find("Saida").text == "Saida1"
    assert entrada.find("Tipo").text == "Tipo1"
    assert entrada.find("DataHoraInicio").text == "2023-01-01 12:00:00"
    assert entrada.find("Instancia").text is not None

def test_save_termino(tmp_path):
    xml_file = tmp_path / "test.xml"
    DatabaseManager.save_entrada(
        str(xml_file), "Pedido1", "Operador1", "Maquina1", "Retalho1", "Saida1", "Tipo1", "2023-01-01 12:00:00"
    )
    success, error = DatabaseManager.save_termino(
        str(xml_file), "Pedido1", "Operador1", "Maquina1", "2023-01-01 13:00:00", "01:00:00"
    )
    assert success
    assert error == ""
    tree = ET.parse(str(xml_file))
    root = tree.getroot()
    entrada = root.find("Entrada")
    assert entrada.find("DataHoraTermino").text == "2023-01-01 13:00:00"
    assert entrada.find("TempoDecorrido").text == "01:00:00"

def test_save_termino_no_match(tmp_path):
    xml_file = tmp_path / "test.xml"
    success, error = DatabaseManager.save_termino(
        str(xml_file), "Pedido1", "Operador1", "Maquina1", "2023-01-01 13:00:00", "01:00:00"
    )
    assert success  # Should create a new entry
    assert error == ""
    tree = ET.parse(str(xml_file))
    root = tree.getroot()
    entradas = root.findall("Entrada")
    assert len(entradas) == 1
    entrada = entradas[0]
    assert entrada.find("Pedido").text == "Pedido1"
    assert entrada.find("DataHoraTermino").text == "2023-01-01 13:00:00"

def test_xml_lock(tmp_path):
    xml_file = tmp_path / "test.xml"
    lock_acquired = False
    with xml_lock(str(xml_file)) as acquired:
        lock_acquired = acquired
        assert acquired
        # Inside lock, file should be locked
    assert lock_acquired
    # After lock, should be unlocked
    assert not os.path.exists(str(xml_file) + ".lock")
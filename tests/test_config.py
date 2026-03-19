import pytest
import os
from core.config import ConfigManager

@pytest.fixture
def temp_config_file(tmp_path, monkeypatch):
    config_file = tmp_path / "config.ini"
    monkeypatch.setattr("core.config.CONFIG_FILE", str(config_file))
    return config_file

def test_resolve_path_relative(temp_config_file):
    # Test relative path resolution
    resolved = os.path.normpath(ConfigManager._resolve_path("./test/path"))
    expected = os.path.normpath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "test", "path"))
    assert resolved == expected

def test_resolve_path_absolute(temp_config_file):
    # Test absolute path (should remain unchanged)
    abs_path = "C:\\absolute\\path"
    assert ConfigManager._resolve_path(abs_path) == abs_path

def test_resolve_path_unc(temp_config_file):
    # Test UNC path
    unc_path = "\\\\server\\share\\path"
    assert ConfigManager._resolve_path(unc_path) == unc_path

def test_load_settings_creates_default(temp_config_file):
    ConfigManager.load_settings()
    assert temp_config_file.exists()
    with open(temp_config_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "[Paths]" in content
    assert "acervosaidascnc" in content

def test_get_server_path(temp_config_file):
    path = ConfigManager.get_server_path()
    assert path == r'V:\8. CONTROLE DE PRODUÇÃO\1. SAÍDAS A CORTAR'  # Default

def test_get_saidas_cnc_path(temp_config_file):
    path = ConfigManager.get_saidas_cnc_path()
    expected = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public", "saidas_cnc")
    assert os.path.normpath(path) == expected

def test_get_all_settings(temp_config_file):
    settings = ConfigManager.get_all_settings()
    assert isinstance(settings, dict)
    assert "acervosaidascnc" in settings

def test_save_settings(temp_config_file):
    new_settings = {"AcervoSaidasCNC": "new_path", "SaidasCnc": "./new_saidas"}
    ConfigManager.save_settings(new_settings)
    settings = ConfigManager.get_all_settings()
    assert settings["acervosaidascnc"] == "new_path"
    assert settings["saidascnc"] == "./new_saidas"
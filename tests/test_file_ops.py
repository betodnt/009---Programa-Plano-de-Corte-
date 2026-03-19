import pytest
import os
import shutil
from core.file_ops import FileOperationRunner

def test_copy_operation(tmp_path):
    src_file = tmp_path / "source.txt"
    dst_file = tmp_path / "dest.txt"
    src_file.write_text("test content")

    result = None
    def on_finished(error):
        nonlocal result
        result = error

    runner = FileOperationRunner("COPY", str(src_file), str(dst_file), on_finished)
    runner.start()
    runner.thread.join()  # Wait for completion

    assert result == ""
    assert dst_file.exists()
    assert dst_file.read_text() == "test content"

def test_move_operation(tmp_path):
    src_file = tmp_path / "source.txt"
    dst_file = tmp_path / "dest.txt"
    src_file.write_text("test content")

    result = None
    def on_finished(error):
        nonlocal result
        result = error

    runner = FileOperationRunner("MOVE", str(src_file), str(dst_file), on_finished)
    runner.start()
    runner.thread.join()

    assert result == ""
    assert not src_file.exists()
    assert dst_file.exists()
    assert dst_file.read_text() == "test content"

def test_operation_with_nonexistent_src(tmp_path):
    src_file = tmp_path / "nonexistent.txt"
    dst_file = tmp_path / "dest.txt"

    result = None
    def on_finished(error):
        nonlocal result
        result = error

    runner = FileOperationRunner("COPY", str(src_file), str(dst_file), on_finished)
    runner.start()
    runner.thread.join()

    assert "Falha na operação" in result
    assert not dst_file.exists()

def test_operation_creates_dst_dir(tmp_path):
    src_file = tmp_path / "source.txt"
    dst_dir = tmp_path / "subdir"
    dst_file = dst_dir / "dest.txt"
    src_file.write_text("test content")

    result = None
    def on_finished(error):
        nonlocal result
        result = error

    runner = FileOperationRunner("COPY", str(src_file), str(dst_file), on_finished)
    runner.start()
    runner.thread.join()

    assert result == ""
    assert dst_file.exists()
    assert dst_file.read_text() == "test content"
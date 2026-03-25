# Script para criar executável portátil com PyInstaller
# Execute: python build_exe.py

import os
import subprocess
import sys

def build_exe():
    # Instalar PyInstaller se não estiver instalado
    try:
        import PyInstaller
    except ImportError:
        print("Instalando PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Caminho do script principal
    main_script = "main.py"

    # Opções do PyInstaller
    options = [
        "--onedir",  # Pasta com executável (mais rápido que --onefile)
        "--windowed",  # Esconde o prompt de comando (console)
        "--clean",  # Limpa cache para build mais limpo
        "--strip",  # Remove símbolos de debug para reduzir tamanho
        "--name=ProgramaPlanoCorte",  # Nome do executável
        "--icon=icon.ico",  # Ícone do executável
        "--add-data=config.ini;.",  # Incluir config.ini
        "--add-data=Public;Public",  # Incluir pasta Public
        "--add-data=icon.png;.",  # Incluir ícone se existir
        "--add-data=icon.ico;.",  # Incluir ico
        "--hidden-import=xml.etree.ElementTree",  # Garantir import oculto
        "--hidden-import=webbrowser",
        "--hidden-import=threading",
        "--hidden-import=configparser",
        "--hidden-import=datetime",
        "--hidden-import=time",
        "--hidden-import=os",
        "--hidden-import=shutil",  # Para backup
        "--hidden-import=xml.dom.minidom",  # Para formatação de XML
        main_script
    ]

    print("Criando executável...")
    subprocess.check_call([sys.executable, "-m", "PyInstaller"] + options)

    print("Executável criado em: dist/ProgramaPlanoCorte/")
    print("Para executar: dist/ProgramaPlanoCorte/ProgramaPlanoCorte.exe")
    print("Para distribuir, compacte a pasta dist/ProgramaPlanoCorte/ em um ZIP.")

if __name__ == "__main__":
    build_exe()
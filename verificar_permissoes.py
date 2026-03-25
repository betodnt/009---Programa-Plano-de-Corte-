import os
import sys
import socket
from core.config import ConfigManager

def verificar_acesso_rede():
    print("="*60)
    print(f"DIAGNÓSTICO DE PERMISSÕES - MÁQUINA: {socket.gethostname()}")
    print("="*60)
    
    ConfigManager.load_settings()
    locks_path = ConfigManager.get_locks_file_path()
    locks_dir = os.path.dirname(locks_path)

    print(f"\n[1] Verificando caminho: {locks_dir}")
    
    if not os.path.exists(locks_dir):
        print(f"    [ERRO] O diretório não existe ou o caminho UNC está incorreto.")
        print(f"    Verifique se a unidade de rede está mapeada ou se o servidor está online.")
        return

    # Teste de Leitura
    try:
        arquivos = os.listdir(locks_dir)
        print(f"    [OK] Leitura permitida. ({len(arquivos)} arquivos encontrados)")
    except Exception as e:
        print(f"    [FALHA] Erro ao ler diretório: {e}")
        return

    # Teste de Escrita e Criação
    teste_nome = f"teste_permissao_{socket.gethostname()}.tmp"
    teste_path = os.path.join(locks_dir, teste_nome)
    
    try:
        with open(teste_path, 'w') as f:
            f.write("teste de escrita")
        print(f"    [OK] Escrita e criação de arquivo permitidas.")
        
        # Teste de Exclusão
        os.remove(teste_path)
        print(f"    [OK] Exclusão de arquivo permitida.")
        
        print("\n" + "!"*20)
        print("  MÁQUINA PRONTA!  ")
        print("!"*20)
        
    except PermissionError:
        print(f"    [CRÍTICO] Acesso negado! Esta máquina não tem permissão de ESCRITA nesta pasta.")
    except Exception as e:
        print(f"    [FALHA] Erro inesperado: {e}")

if __name__ == "__main__":
    verificar_acesso_rede()
    input("\nPressione Enter para sair...")
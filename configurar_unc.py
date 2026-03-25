#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para descobrir e configurar caminhos UNC para acesso em rede.
Permite rodar o monitor em qualquer máquina da rede.
"""

import os
import sys
import configparser
import subprocess

def discover_mapped_drive(drive_letter="V:"):
    """Tenta descobrir o caminho UNC da unidade mapeada"""
    try:
        # Usar wmic para descobrir compartilhamento
        result = subprocess.run(
            f'wmic logicaldisk where name="{drive_letter}" get Description',
            capture_output=True,
            text=True,
            shell=True
        )
        
        if result.stdout:
            print(f"[INFO] Unidade {drive_letter} encontrada")
            
        # Tentar usar net use para ver mapeamentos
        result = subprocess.run(
            'net use',
            capture_output=True,
            text=True,
            shell=True
        )
        
        print("\n=== Unidades de Rede Mapeadas ===")
        print(result.stdout)
        
        return None
    except Exception as e:
        print(f"[ERRO] Não foi possível descobrir UNC: {e}")
        return None

def test_network_path(path):
    """Testa se um caminho de rede está acessível"""
    try:
        if os.path.exists(path):
            print(f"[OK] Caminho acessível: {path}")
            return True
        else:
            print(f"[ERRO] Caminho não acessível: {path}")
            return False
    except Exception as e:
        print(f"[ERRO] Erro ao testar caminho: {e}")
        return False

def update_config_ini(unc_path):
    """Atualiza config.ini com caminhos UNC para rede"""
    config_file = os.path.join(os.path.dirname(__file__), 'config.ini')
    
    if not os.path.exists(config_file):
        print(f"[ERRO] Arquivo {config_file} não encontrado!")
        return False
    
    config = configparser.ConfigParser()
    config.read(config_file, encoding='utf-8')
    
    # Atualizar caminhos para UNC
    if not config.has_section('Paths'):
        config.add_section('Paths')
    
    # Converter para formato correto (sem espaços extras, barra consistente)
    unc_normalized = unc_path.replace('/', '\\').rstrip('\\')
    
    path_dados = f"{unc_normalized}\\dados_{{date}}.xml"
    path_locks = f"{unc_normalized}\\APP_data\\active_locks.json"
    
    print(f"\n[INFO] Atualizando config.ini com caminhos:")
    print(f"  DadosXml: {path_dados}")
    print(f"  LocksFile: {path_locks}")
    
    config.set('Paths', 'DadosXml', path_dados)
    config.set('Paths', 'LocksFile', path_locks)
    
    # Salvar backup
    backup_file = config_file + '.backup'
    if not os.path.exists(backup_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            with open(backup_file, 'w', encoding='utf-8') as bf:
                bf.write(f.read())
        print(f"[OK] Backup criado: {backup_file}")
    
    # Salvar arquivo atualizado
    with open(config_file, 'w', encoding='utf-8') as f:
        config.write(f)
    
    print(f"[OK] {config_file} atualizado com sucesso!")
    return True

def main():
    print("=" * 60)
    print("CONFIGURADOR DE CAMINHO UNC PARA MONITOR REMOTO")
    print("=" * 60)
    
    # Tentar descobrir automaticamente
    print("\n[1] Descobrindo caminho UNC da unidade V:...")
    discover_mapped_drive("V:")
    
    # Pedir input do usuário
    print("\n[2] Digite o caminho UNC encontrado:")
    print("    Exemplo: \\\\SERVIDOR\\compartilhado\\8. CONTROLE DE PRODUÇÃO\\3. DADOS")
    print("    Ou: \\\\192.168.1.100\\dados")
    
    unc_path = input("\nCaminho UNC (ou Enter para cancelar): ").strip()
    
    if not unc_path:
        print("[CANCELADO] Nenhum caminho fornecido")
        return False
    
    # Testar caminho
    print(f"\n[3] Testando caminho: {unc_path}")
    if not test_network_path(unc_path):
        print("\n[AVISO] O caminho pode não estar acessível dessa máquina")
        print("        Mas será salvo no config.ini mesmo assim")
    
    # Atualizar config.ini
    print(f"\n[4] Atualizando config.ini...")
    if update_config_ini(unc_path):
        print("\n" + "=" * 60)
        print("[SUCESSO] Configuração concluída!")
        print("=" * 60)
        print("\nAgora você pode:")
        print("  1. Copiar os arquivos para outra máquina")
        print("  2. Rodar: python monitor_app.py")
        print("\nTodos os monitores verão as operações em tempo real!")
        return True
    else:
        print("\n[ERRO] Falha ao atualizar config.ini")
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)

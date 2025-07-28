#!/usr/bin/env python3
"""
Script de Configuração Rápida do Bot de Trading Binance
"""

import os
import shutil
import sys
from pathlib import Path


def setup_bot():
    """Configuração inicial do bot"""
    print("🚀 Configurando Bot de Trading Binance...")
    
    # Criar diretórios necessários
    directories = ['logs', 'backups', 'data']
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✅ Diretório '{dir_name}' criado")
    
    # Copiar arquivos de configuração exemplo
    config_files = [
        ('config.yaml.example', 'config.yaml'),
        ('.env.example', '.env')
    ]
    
    for source, target in config_files:
        if not Path(target).exists():
            if Path(source).exists():
                shutil.copy(source, target)
                print(f"✅ Arquivo '{target}' criado a partir do exemplo")
            else:
                print(f"⚠️  Arquivo exemplo '{source}' não encontrado")
        else:
            print(f"ℹ️  Arquivo '{target}' já existe, pulando...")
    
    # Verificar dependências
    print("\n📦 Verificando dependências...")
    try:
        import pandas
        import numpy
        import binance
        import yaml
        print("✅ Todas as dependências principais encontradas")
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print("Execute: pip install -r requirements.txt")
        return False
    
    # Instruções finais
    print("\n🎯 Configuração concluída!")
    print("\n📝 Próximos passos:")
    print("1. Edite o arquivo 'config.yaml' com suas preferências")
    print("2. Adicione suas chaves de API no arquivo '.env'")
    print("3. Teste primeiro: python demo_bot.py")
    print("4. Execute o bot real: python main.py")
    
    print("\n⚠️  IMPORTANTE:")
    print("- Comece sempre com testnet: true no config.yaml")
    print("- Teste com pequenas quantias primeiro")
    print("- Monitore os logs regularmente")
    
    return True


if __name__ == "__main__":
    try:
        setup_bot()
    except KeyboardInterrupt:
        print("\n❌ Configuração cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro durante configuração: {e}")
        sys.exit(1)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desfragmentador de Arquivos - Fragmenta e Recombina arquivos grandes
Permite quebrar um arquivo grande em múltiplos fragmentos e recombinar depois
"""

import os
import json
from pathlib import Path
from typing import Optional

 
class FragmentadorArquivos:
    """Classe para fragmentar e desfragmentar arquivos"""
    
    METADATA_SUFFIX = ".metadata.json"
    
    def __init__(self, tamanho_fragmento_mb: int = 25):
        """
        Inicializa o fragmentador
        
        Args:
            tamanho_fragmento_mb: Tamanho de cada fragmento em MB (padrão: 25)
        """
        self.tamanho_fragmento = tamanho_fragmento_mb * 1024 * 1024  # Converter para bytes
        
    def fragmentar(self, caminho_arquivo: str, diretorio_saida: Optional[str] = None) -> bool:
        """
        Fragmenta um arquivo em múltiplos pedaços
        
        Args:
            caminho_arquivo: Caminho do arquivo a fragmentar
            diretorio_saida: Diretório onde salvar os fragmentos (padrão: mesmo diretório)
            
        Returns:
            True se sucesso, False se erro
        """
        try:
            arquivo = Path(caminho_arquivo)
            
            # Validar se arquivo existe
            if not arquivo.exists():
                print(f"❌ Erro: Arquivo '{caminho_arquivo}' não encontrado!")
                return False
            
            # Definir diretório de saída
            if diretorio_saida is None:
                diretorio_saida = str(arquivo.parent)
            
            diretorio_saida = Path(diretorio_saida)
            diretorio_saida.mkdir(parents=True, exist_ok=True)
            
            # Obter tamanho do arquivo
            tamanho_total = arquivo.stat().st_size
            nome_base = arquivo.stem
            extensao = arquivo.suffix
            
            print(f"\n📦 Iniciando fragmentação...")
            print(f"   Arquivo: {arquivo.name}")
            print(f"   Tamanho total: {self._formatar_bytes(tamanho_total)}")
            print(f"   Tamanho por fragmento: {self._formatar_bytes(self.tamanho_fragmento)}")
            
            # Calcular quantidade de fragmentos necessários
            num_fragmentos = (tamanho_total + self.tamanho_fragmento - 1) // self.tamanho_fragmento
            print(f"   Total de fragmentos: {num_fragmentos}")
            
            # Ler arquivo original e fragmentar
            fragmentos_info = []
            numero_fragmento = 1
            
            with open(arquivo, 'rb') as f_original:
                while True:
                    # Ler um pedaço do arquivo
                    dados = f_original.read(self.tamanho_fragmento)
                    
                    if not dados:
                        break
                    
                    # Criar nome do fragmento
                    nome_fragmento = f"{nome_base}{numero_fragmento}{extensao}"
                    caminho_fragmento = diretorio_saida / nome_fragmento
                    
                    # Salvar fragmento
                    with open(caminho_fragmento, 'wb') as f_fragmento:
                        f_fragmento.write(dados)
                    
                    tamanho_fragmento = len(dados)
                    fragmentos_info.append({
                        "numero": numero_fragmento,
                        "nome": nome_fragmento,
                        "tamanho": tamanho_fragmento,
                        "hash": self._calcular_hash_simples(dados)
                    })
                    
                    print(f"   ✓ Fragmento {numero_fragmento}/{num_fragmentos} criado: "
                          f"{nome_fragmento} ({self._formatar_bytes(tamanho_fragmento)})")
                    
                    numero_fragmento += 1
            
            # Salvar metadados
            metadata = {
                "arquivo_original": arquivo.name,
                "tamanho_original": tamanho_total,
                "tamanho_fragmento": self.tamanho_fragmento,
                "numero_fragmentos": num_fragmentos,
                "fragmentos": fragmentos_info,
                "hash_original": self._calcular_hash_arquivo(arquivo)
            }
            
            arquivo_metadata = diretorio_saida / f"{nome_base}{self.METADATA_SUFFIX}"
            with open(arquivo_metadata, 'w', encoding='utf-8') as f_meta:
                json.dump(metadata, f_meta, indent=2)
            
            print(f"   ✓ Arquivo de metadados criado: {arquivo_metadata.name}")
            print(f"\n✅ Fragmentação concluída com sucesso!\n")
            return True
            
        except Exception as e:
            print(f"❌ Erro durante fragmentação: {str(e)}")
            return False
    
    def desfragmentar(self, caminho_metadata: str, diretorio_saida: Optional[str] = None, 
                     nome_novo: Optional[str] = None) -> bool:
        """
        Recombina fragmentos em um arquivo original
        
        Args:
            caminho_metadata: Caminho do arquivo .metadata.json
            diretorio_saida: Diretório onde salvar o arquivo recombinado
            nome_novo: Novo nome para o arquivo (padrão: nome original)
            
        Returns:
            True se sucesso, False se erro
        """
        try:
            arquivo_metadata = Path(caminho_metadata)
            
            # Validar se arquivo de metadados existe
            if not arquivo_metadata.exists():
                print(f"❌ Erro: Arquivo de metadados '{caminho_metadata}' não encontrado!")
                return False
            
            # Carregar metadados
            with open(arquivo_metadata, 'r', encoding='utf-8') as f_meta:
                metadata = json.load(f_meta)
            
            # Definir diretório de saída
            if diretorio_saida is None:
                diretorio_saida = str(arquivo_metadata.parent)
            
            diretorio_saida = Path(diretorio_saida)
            diretorio_saida.mkdir(parents=True, exist_ok=True)
            
            # Definir nome do arquivo recombinado
            if nome_novo is None:
                nome_novo = metadata["arquivo_original"]
            
            caminho_saida = diretorio_saida / nome_novo
            diretorio_origem = arquivo_metadata.parent
            
            print(f"\n🔧 Iniciando desfragmentação...")
            print(f"   Arquivo original: {metadata['arquivo_original']}")
            print(f"   Tamanho esperado: {self._formatar_bytes(metadata['tamanho_original'])}")
            print(f"   Total de fragmentos: {metadata['numero_fragmentos']}")
            print(f"   Destino: {caminho_saida}")
            
            # Verificar se todos os fragmentos existem
            print(f"\n   Verificando fragmentos...")
            for frag_info in metadata['fragmentos']:
                caminho_fragmento = diretorio_origem / frag_info['nome']
                if not caminho_fragmento.exists():
                    print(f"   ❌ Fragmento não encontrado: {frag_info['nome']}")
                    return False
                print(f"   ✓ {frag_info['nome']} encontrado")
            
            # Combinar fragmentos
            print(f"\n   Combinando fragmentos...")
            tamanho_total_lido = 0
            
            with open(caminho_saida, 'wb') as f_saida:
                for i, frag_info in enumerate(metadata['fragmentos'], 1):
                    caminho_fragmento = diretorio_origem / frag_info['nome']
                    
                    with open(caminho_fragmento, 'rb') as f_fragmento:
                        dados = f_fragmento.read()
                        f_saida.write(dados)
                        tamanho_total_lido += len(dados)
                    
                    print(f"   ✓ Fragmento {i}/{metadata['numero_fragmentos']} combinado: "
                          f"{frag_info['nome']}")
            
            # Validar tamanho
            tamanho_final = caminho_saida.stat().st_size
            
            if tamanho_final != metadata['tamanho_original']:
                print(f"\n   ⚠️  Aviso: Tamanho final ({self._formatar_bytes(tamanho_final)}) "
                      f"diferente do esperado ({self._formatar_bytes(metadata['tamanho_original'])})")
            
            # Validar hash
            hash_final = self._calcular_hash_arquivo(caminho_saida)
            if hash_final == metadata.get('hash_original'):
                print(f"   ✓ Integridade do arquivo validada (hash coincide)")
            else:
                print(f"   ⚠️  Aviso: Hash do arquivo diferente")
            
            print(f"\n📁 Arquivo recombinado: {nome_novo}")
            print(f"   Tamanho final: {self._formatar_bytes(tamanho_final)}")
            print(f"\n✅ Desfragmentação concluída com sucesso!\n")
            return True
            
        except Exception as e:
            print(f"❌ Erro durante desfragmentação: {str(e)}")
            return False
    
    @staticmethod
    def _formatar_bytes(bytes_val: int) -> str:
        """Formata bytes para unidade legível"""
        for unidade in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.2f} {unidade}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f} PB"
    
    @staticmethod
    def _calcular_hash_simples(dados: bytes) -> str:
        """Calcula um hash simples dos dados"""
        import hashlib
        return hashlib.sha256(dados).hexdigest()[:16]
    
    @staticmethod
    def _calcular_hash_arquivo(caminho_arquivo: Path) -> str:
        """Calcula hash do arquivo completo"""
        import hashlib
        sha256_hash = hashlib.sha256()
        
        with open(caminho_arquivo, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()


def menu_principal():
    """Menu interativo principal"""
    fragmentador = None
    
    while True:
        print("\n" + "="*60)
        print("  🔧 DESFRAGMENTADOR DE ARQUIVOS")
        print("="*60)
        print("\n1. 📦 Fragmentar arquivo")
        print("2. 🔄 Desfragmentar (recombinar fragmentos)")
        print("3. ⚙️  Configurar tamanho do fragmento")
        print("4. ❌ Sair")
        print("\n" + "-"*60)
        
        opcao = input("Escolha uma opção (1-4): ").strip()
        
        if opcao == "1":
            caminho = input("\nDigite o caminho do arquivo a fragmentar: ").strip()
            caminho = caminho.strip('"').strip("'")  # Remover aspas
            
            tamanho_mb = 25
            if fragmentador:
                tamanho_mb = fragmentador.tamanho_fragmento // (1024 * 1024)
            
            if fragmentador is None:
                fragmentador = FragmentadorArquivos(tamanho_mb)
            
            diretorio = input("\nDigite o diretório para salvar fragmentos (ou Enter para automático): ").strip()
            diretorio = diretorio.strip('"').strip("'") if diretorio else None
            
            fragmentador.fragmentar(caminho, diretorio)
        
        elif opcao == "2":
            caminho_meta = input("\nDigite o caminho do arquivo .metadata.json: ").strip()
            caminho_meta = caminho_meta.strip('"').strip("'")
            
            diretorio = input("Digite o diretório para salvar o arquivo recombinado (ou Enter para automático): ").strip()
            diretorio = diretorio.strip('"').strip("'") if diretorio else None
            
            nome_novo = input("Digite um novo nome para o arquivo (ou Enter para manter original): ").strip()
            nome_novo = nome_novo if nome_novo else None
            
            if fragmentador is None:
                fragmentador = FragmentadorArquivos()
            
            fragmentador.desfragmentar(caminho_meta, diretorio, nome_novo)
        
        elif opcao == "3":
            if fragmentador is None:
                fragmentador = FragmentadorArquivos()
            
            try:
                tamanho = int(input("\nDigite o novo tamanho de fragmento em MB: ").strip())
                if tamanho > 0:
                    fragmentador = FragmentadorArquivos(tamanho)
                    print(f"✓ Tamanho do fragmento alterado para {tamanho}MB")
                else:
                    print("❌ Digite um valor maior que 0")
            except ValueError:
                print("❌ Valor inválido!")
        
        elif opcao == "4":
            print("\nAté logo! 👋\n")
            break
        
        else:
            print("❌ Opção inválida!")


def usar_como_modulo_exemplo():
    """Exemplo de como usar como módulo"""
    # Fragmentar
    frag = FragmentadorArquivos(tamanho_fragmento_mb=25)
    frag.fragmentar("meu_arquivo.rpa", "./fragmentos")
    
    # Desfragmentar
    frag.desfragmentar("./fragmentos/meu_arquivo.metadata.json", "./saida")


if __name__ == "__main__":
    import sys
    
    # Se passar argumentos de linha de comando
    if len(sys.argv) > 1:
        comando = sys.argv[1].lower()
        
        if comando == "fragmentar" and len(sys.argv) >= 3:
            arquivo = sys.argv[2]
            tamanho_mb = int(sys.argv[3]) if len(sys.argv) > 3 else 25
            diretorio = sys.argv[4] if len(sys.argv) > 4 else None
            
            frag = FragmentadorArquivos(tamanho_mb)
            frag.fragmentar(arquivo, diretorio)
        
        elif comando == "desfragmentar" and len(sys.argv) >= 3:
            metadata = sys.argv[2]
            diretorio = sys.argv[3] if len(sys.argv) > 3 else None
            nome = sys.argv[4] if len(sys.argv) > 4 else None
            
            frag = FragmentadorArquivos()
            frag.desfragmentar(metadata, diretorio, nome)
        
        else:
            print("Uso:")
            print("  python desfragmentador_de_arquivos.py fragmentar <arquivo> [tamanho_mb] [diretorio]")
            print("  python desfragmentador_de_arquivos.py desfragmentar <metadata.json> [diretorio] [novo_nome]")
            print("\nOu execute sem argumentos para menu interativo:")
            print("  python desfragmentador_de_arquivos.py")
    else:
        # Menu interativo
        menu_principal()

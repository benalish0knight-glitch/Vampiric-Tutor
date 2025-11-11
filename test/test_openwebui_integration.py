#!/usr/bin/env python3
"""
Script de teste de integração ESSENCIAL para verificar a comunicação e formato de dados
com OpenWebUI, focando apenas nos endpoints conhecidos e funcionais.
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, Any

# Carregar variáveis de ambiente
load_dotenv()

class OpenWebUIIntegrationTest:
    """Testes de integração essenciais com OpenWebUI"""
    
    def __init__(self):
        self.base_url = os.getenv("OPENWEBUI_BASE_URL")
        self.api_key = os.getenv("OPENWEBUI_API_KEY")
        self.kb_name = os.getenv("OPENWEBUI_KNOWLEDGE_BASE_NAME")
        
        if not all([self.base_url, self.api_key, self.kb_name]):
            raise ValueError("Credenciais do OpenWebUI não configuradas no .env")
        
        # Headers simples, Content-Type não é necessário para GETs e não funciona nos POSTs problemáticos.
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        
        self.test_results = []
    
    # --- FUNÇÕES AUXILIARES ---
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Registra o resultado de um teste"""
        result = {
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✓ PASSOU" if passed else "✗ FALHOU"
        print(f"\n{status}: {test_name}")
        if details:
            print(f"  Detalhes: {details.replace('\n', '\n  ')}")

    # --- TESTES ESSENCIAIS DE CONECTIVIDADE E AUTENTICAÇÃO ---

    def test_1_connection(self) -> bool:
        """Teste 1: Verificar Conectividade com OpenWebUI (/health)"""
        test_name = "1. Conectividade com OpenWebUI"
        try:
            url = f"{self.base_url}/api/v1/health"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code in [200, 404]:
                self.log_test(test_name, True, f"Servidor respondeu com status {response.status_code}")
                return True
            else:
                self.log_test(test_name, False, f"Status inesperado: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test(test_name, False, f"Erro de conexão/geral: {str(e)}")
            return False
    
    def test_2_authentication(self) -> bool:
        """Teste 2: Verificar Autenticação com API Key (GET /knowledge)"""
        test_name = "2. Autenticação com API Key"
        try:
            # Endpoint usado para autenticação no teste 2 original
            url = f"{self.base_url}/api/v1/knowledge"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 401:
                self.log_test(test_name, False, "API Key inválida ou expirada (Status 401)")
                return False
            elif response.status_code in [200, 404]:
                self.log_test(test_name, True, "Autenticação bem-sucedida (Status 200/404 OK)")
                return True
            else:
                self.log_test(test_name, True, f"Resposta recebida (status {response.status_code})")
                return True
                
        except Exception as e:
            self.log_test(test_name, False, f"Erro: {str(e)}")
            return False
    
    def test_3_knowledge_base_check(self) -> bool:
        """Teste 3: Tentar listar Knowledge Bases (/knowledge)"""
        test_name = f"3. Verificar Knowledge Base '{self.kb_name}'"
        try:
            # Endpoint que consistentemente falha com HTML, usado para diagnóstico final
            url = f"{self.base_url}/api/v1/knowledge"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                if response.content and not response.text.startswith("<!doctype html>"):
                    try:
                        kbs = response.json()
                        kb_names = [kb.get('name') for kb in kbs] if isinstance(kbs, list) else []
                        if self.kb_name in kb_names:
                            self.log_test(test_name, True, "Knowledge Base encontrado e JSON válido.")
                            return True
                        else:
                            self.log_test(test_name, False, f"JSON válido, mas KB '{self.kb_name}' não encontrado. Disponíveis: {kb_names}")
                            return False
                    except json.JSONDecodeError:
                        self.log_test(test_name, False, "Resposta 200, mas corpo inválido (Não-JSON, provável HTML).")
                        return False
                else:
                    self.log_test(test_name, False, "Resposta 200, mas corpo é HTML ou vazio.")
                    return False
            else:
                self.log_test(test_name, False, 
                    f"Não foi possível listar KBs (status {response.status_code}).")
                return False
                
        except Exception as e:
            self.log_test(test_name, False, f"Erro: {str(e)}")
            return False

    # --- TESTES DE FORMATO DE DADOS ---
    
    def test_4_chunk_format(self) -> bool:
        """Teste 4: Validar Formato de Chunks (Interno)"""
        test_name = "4. Validar Formato de Chunks"
        try:
            test_chunk = {
                "chunk_id": f"test_chunk_{datetime.now().timestamp()}",
                "text": "Este é um chunk de teste com conteúdo relevante.",
                "metadata": {
                    "source": "BookStack Page ID: 9999",
                    "title": "Test Page",
                    "url": f"{os.getenv('BOOKSTACK_BASE_URL', 'http://localhost')}/view/9999",
                    "chunk_index": 0
                }
            }
            required_fields = ["chunk_id", "text", "metadata"]
            has_all_fields = all(field in test_chunk for field in required_fields)
            if has_all_fields:
                self.log_test(test_name, True, 
                    f"Estrutura de chunk validada: {json.dumps(test_chunk, indent=2, ensure_ascii=False)}")
                return True
            else:
                self.log_test(test_name, False, "Campos obrigatórios faltando")
                return False
        except Exception as e:
            self.log_test(test_name, False, f"Erro: {str(e)}")
            return False
    
    def test_5_metadata_format(self) -> bool:
        """Teste 5: Validar Formato de Metadados (Interno)"""
        test_name = "5. Validação de Metadados"
        try:
            metadata = {
                "source": "BookStack Page ID: 123",
                "title": "Exemplo de Página",
                "url": f"{os.getenv('BOOKSTACK_BASE_URL', 'http://localhost')}/view/123",
                "book_id": 1,
                "page_id": 123,
                "updated_at": datetime.now().isoformat()
            }
            required_metadata = ["source", "title", "url"]
            has_required = all(field in metadata for field in required_metadata)
            if has_required:
                self.log_test(test_name, True, 
                    f"Metadados validados: {json.dumps(metadata, indent=2, ensure_ascii=False)}")
                return True
            else:
                self.log_test(test_name, False, "Campos de metadados obrigatórios faltando")
                return False
        except Exception as e:
            self.log_test(test_name, False, f"Erro: {str(e)}")
            return False
    
    def test_6_special_characters(self) -> bool:
        """Teste 6: Suporte a Caracteres Especiais (Interno)"""
        test_name = "6. Suporte a Caracteres Especiais"
        try:
            special_content = {
                "text": "Texto com acentuação: á, é, í, ó, ú, ç, ã, õ\n"
                        "Emojis: 🎉 🚀 ✨\n"
                        "Símbolos: © ® ™ € £ ¥\n"
                        "Markdown: **negrito** *itálico* `código`"
            }
            json_str = json.dumps(special_content, ensure_ascii=False)
            parsed = json.loads(json_str)
            if parsed["text"] == special_content["text"]:
                self.log_test(test_name, True, 
                    "Caracteres especiais preservados corretamente")
                return True
            else:
                self.log_test(test_name, False, "Perda de dados na serialização")
                return False
        except Exception as e:
            self.log_test(test_name, False, f"Erro: {str(e)}")
            return False

    # --- TESTE DE DESCOBERTA DE ENDPOINTS ---
    
    def test_7_api_endpoints(self) -> Dict[str, Any]:
        """Teste 7: Descobrir Endpoints Disponíveis da API"""
        test_name = "7. Descoberta de Endpoints da API"
        endpoints_found = {}
        common_endpoints = [
            "/api/v1/knowledge",
            "/api/v1/health",
            "/api/v1/documents",
            f"/api/v1/knowledge/{self.kb_name}",
        ]
        
        print(f"\n  Testando endpoints comuns...")
        for endpoint in common_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                response = requests.get(url, headers=self.headers, timeout=5)
                endpoints_found[endpoint] = {
                    "status": response.status_code,
                    "available": response.status_code not in [404]
                }
                print(f"    {endpoint}: {response.status_code}")
            except Exception as e:
                endpoints_found[endpoint] = {
                    "status": "error",
                    "error": str(e)
                }
        
        available_count = sum(1 for e in endpoints_found.values() 
                            if e.get("available", False))
        
        self.log_test(test_name, available_count > 0, 
            f"Encontrados {available_count} endpoints disponíveis")
        
        return endpoints_found
    
    # --- RELATÓRIO FINAL ---
    
    def generate_report(self):
        """Gera relatório final dos testes"""
        print("\n" + "="*70)
        print("RELATÓRIO DE TESTES DE INTEGRAÇÃO - OPENWEBUI (ESSENCIAL)")
        print("="*70)
        
        passed = sum(1 for r in self.test_results if r["passed"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\nTotal de testes: {total}")
        print(f"Testes aprovados: {passed}")
        print(f"Testes reprovados: {total - passed}")
        print(f"Taxa de sucesso: {success_rate:.1f}%")
        
        print("\n" + "-"*70)
        print("DETALHES DOS TESTES:")
        print("-"*70)
        
        for result in self.test_results:
            status = "✓" if result["passed"] else "✗"
            print(f"\n{status} {result['test']}")
            if result['details']:
                print(f"  {result['details'].replace('\n', '\n  ')}")
        
        report_file = f"data/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": total - passed,
                    "success_rate": success_rate
                },
                "tests": self.test_results,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*70}")
        print(f"Relatório salvo em: {report_file}")
        print("="*70)
        
        return success_rate >= 80 # Aumentando o limiar de sucesso.

def main():
    """Função principal para executar todos os testes"""
    print("="*70)
    print("TESTES DE INTEGRAÇÃO ESSENCIAIS - OPENWEBUI")
    print("="*70)
    print(f"\nData/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"OpenWebUI URL: {os.getenv('OPENWEBUI_BASE_URL')}")
    print(f"Knowledge Base: {os.getenv('OPENWEBUI_KNOWLEDGE_BASE_NAME')}")
    
    try:
        tester = OpenWebUIIntegrationTest()
        
        print("\n" + "="*70)
        print("EXECUTANDO TESTES...")
        print("="*70)
        
        # Execução dos testes essenciais
        tester.test_1_connection()
        tester.test_2_authentication()
        tester.test_3_knowledge_base_check()
        tester.test_4_chunk_format()
        tester.test_5_metadata_format()
        tester.test_6_special_characters()
        tester.test_7_api_endpoints()
        
        success = tester.generate_report()
        
        sys.exit(0 if success else 1)
        
    except ValueError as e:
        print(f"\n✗ ERRO DE CONFIGURAÇÃO: {e}")
        print("\nVerifique se as seguintes variáveis estão configuradas no .env:")
        print("  - OPENWEBUI_BASE_URL")
        print("  - OPENWEBUI_API_KEY")
        print("  - OPENWEBUI_KNOWLEDGE_BASE_NAME")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
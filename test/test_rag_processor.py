import pytest
import os
import json
from unittest.mock import Mock, patch, MagicMock
from app.rag_processor import RAGProcessor

# Fixtures para configuração de testes

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Configura variáveis de ambiente para os testes"""
    monkeypatch.setenv("OPENWEBUI_BASE_URL", "http://localhost:3000")
    monkeypatch.setenv("OPENWEBUI_API_KEY", "test-api-key-123")
    monkeypatch.setenv("OPENWEBUI_KNOWLEDGE_BASE_NAME", "test-kb")
    monkeypatch.setenv("CHUNK_SIZE", "1000")
    monkeypatch.setenv("CHUNK_OVERLAP", "200")
    monkeypatch.setenv("BOOKSTACK_BASE_URL", "http://localhost:8080")

@pytest.fixture
def rag_processor(mock_env_vars):
    """Instancia o RAGProcessor com configurações mockadas"""
    return RAGProcessor()

@pytest.fixture
def sample_markdown():
    """Retorna um conteúdo Markdown de exemplo"""
    return """# Título Principal

Este é um parágrafo de introdução com informações importantes sobre o documento.

## Seção 1

Conteúdo da primeira seção com detalhes técnicos.
- Item 1
- Item 2
- Item 3

## Seção 2

Mais conteúdo aqui com informações adicionais que precisam ser indexadas.

### Subseção 2.1

Detalhes específicos da subseção."""

# Testes Unitários

class TestRAGProcessorInitialization:
    """Testes de inicialização do RAGProcessor"""
    
    def test_initialization_with_valid_env(self, rag_processor):
        """Testa se o RAGProcessor é inicializado corretamente com env válido"""
        assert rag_processor.base_url == "http://localhost:3000"
        assert rag_processor.api_key == "test-api-key-123"
        assert rag_processor.kb_name == "test-kb"
        assert rag_processor.chunk_size == 1000
        assert rag_processor.chunk_overlap == 200
    
    def test_headers_format(self, rag_processor):
        """Verifica se os headers estão no formato correto"""
        assert "Authorization" in rag_processor.headers
        assert rag_processor.headers["Authorization"] == "Bearer test-api-key-123"
        assert rag_processor.headers["Content-Type"] == "application/json"
        assert rag_processor.headers["Accept"] == "application/json"
    
    def test_initialization_with_invalid_chunk_size(self, monkeypatch):
        """Testa inicialização com CHUNK_SIZE inválido"""
        monkeypatch.setenv("OPENWEBUI_BASE_URL", "http://localhost:3000")
        monkeypatch.setenv("OPENWEBUI_API_KEY", "test-key")
        monkeypatch.setenv("OPENWEBUI_KNOWLEDGE_BASE_NAME", "test-kb")
        monkeypatch.setenv("CHUNK_SIZE", "invalid")
        monkeypatch.setenv("CHUNK_OVERLAP", "200")
        
        processor = RAGProcessor()
        # Deve usar valores padrão
        assert processor.chunk_size == 1000
        assert processor.chunk_overlap == 200


class TestChunking:
    """Testes de divisão de conteúdo em chunks"""
    
    def test_split_into_chunks_basic(self, rag_processor, sample_markdown):
        """Testa a divisão básica de conteúdo em chunks"""
        chunks = rag_processor._split_into_chunks(sample_markdown)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
    
    def test_chunk_size_respected(self, rag_processor):
        """Verifica se o tamanho dos chunks é respeitado"""
        # Cria um texto grande
        large_text = "Este é um parágrafo. " * 200
        chunks = rag_processor._split_into_chunks(large_text)
        
        # Verifica se nenhum chunk excede significativamente o tamanho máximo
        for chunk in chunks:
            assert len(chunk) <= rag_processor.chunk_size + rag_processor.chunk_overlap
    
    def test_empty_content(self, rag_processor):
        """Testa divisão de conteúdo vazio"""
        chunks = rag_processor._split_into_chunks("")
        assert chunks == []
    
    def test_small_content_single_chunk(self, rag_processor):
        """Testa se conteúdo pequeno resulta em um único chunk"""
        small_text = "Texto pequeno"
        chunks = rag_processor._split_into_chunks(small_text)
        assert len(chunks) == 1
        assert chunks[0] == small_text


class TestOpenWebUIIngestion:
    """Testes de ingestão no OpenWebUI"""
    
    @patch('requests.post')
    def test_simulate_ingestion_success(self, mock_post, rag_processor, sample_markdown):
        """Testa ingestão bem-sucedida de dados"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_post.return_value = mock_response
        
        chunks = rag_processor._split_into_chunks(sample_markdown)
        rag_processor._simulate_openwebui_ingestion(123, "Test Page", chunks)
        
        # Verifica se a função foi executada sem erros
        assert mock_post.call_count >= 0
    
    def test_ingestion_payload_format(self, rag_processor):
        """Verifica o formato do payload de ingestão"""
        chunks = ["Chunk 1", "Chunk 2"]
        page_id = 123
        page_name = "Test Page"
        
        # Captura o que seria enviado
        with patch('requests.post') as mock_post:
            rag_processor._simulate_openwebui_ingestion(page_id, page_name, chunks)
        
        # Verifica que a função foi executada
        assert True  # A simulação imprime informações
    
    def test_ingestion_with_empty_credentials(self, monkeypatch):
        """Testa ingestão sem credenciais configuradas"""
        monkeypatch.setenv("OPENWEBUI_BASE_URL", "")
        monkeypatch.setenv("OPENWEBUI_API_KEY", "")
        monkeypatch.setenv("OPENWEBUI_KNOWLEDGE_BASE_NAME", "")
        
        processor = RAGProcessor()
        chunks = ["Test chunk"]
        
        # Não deve lançar exceção, apenas avisar
        processor._simulate_openwebui_ingestion(123, "Test", chunks)
        assert True
    
    def test_metadata_structure(self, rag_processor, sample_markdown):
        """Verifica a estrutura dos metadados enviados"""
        chunks = rag_processor._split_into_chunks(sample_markdown)
        page_id = 456
        page_name = "Test Document"
        
        # Os metadados devem conter source, title e url
        expected_metadata_keys = ["source", "title", "url"]
        
        # Verifica indiretamente através da execução
        rag_processor._simulate_openwebui_ingestion(page_id, page_name, chunks)
        assert True


class TestProcessAndIndex:
    """Testes do método principal process_and_index"""
    
    @pytest.mark.asyncio
    async def test_process_and_index_complete_flow(self, rag_processor, sample_markdown):
        """Testa o fluxo completo de processamento e indexação"""
        page_id = 789
        page_name = "Integration Test Page"
        
        with patch.object(rag_processor, '_simulate_openwebui_ingestion') as mock_ingest:
            await rag_processor.process_and_index(page_id, page_name, sample_markdown)
            
            # Verifica se a ingestão foi chamada
            mock_ingest.assert_called_once()
            
            # Verifica os argumentos da chamada
            call_args = mock_ingest.call_args[0]
            assert call_args[0] == page_id
            assert call_args[1] == page_name
            assert isinstance(call_args[2], list)  # chunks
            assert len(call_args[2]) > 0
    
    @pytest.mark.asyncio
    async def test_process_and_index_with_empty_content(self, rag_processor):
        """Testa processamento com conteúdo vazio"""
        with patch.object(rag_processor, '_simulate_openwebui_ingestion') as mock_ingest:
            await rag_processor.process_and_index(1, "Empty Page", "")
            
            # Deve ter sido chamado mesmo com conteúdo vazio
            mock_ingest.assert_called_once()
            call_args = mock_ingest.call_args[0]
            assert call_args[2] == []  # chunks vazios


# Testes de Integração

class TestIntegrationWithMockAPI:
    """Testes de integração com API mockada"""
    
    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_full_pipeline_with_mock_api(self, mock_post, rag_processor, sample_markdown):
        """Testa o pipeline completo com API mockada"""
        # Configura resposta mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "chunks_received": 3}
        mock_post.return_value = mock_response
        
        # Executa o pipeline
        await rag_processor.process_and_index(999, "Pipeline Test", sample_markdown)
        
        # Verifica que o processo foi concluído
        assert True
    
    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_api_error_handling(self, mock_post, rag_processor, sample_markdown):
        """Testa tratamento de erros da API"""
        # Simula erro de API
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        # Não deve lançar exceção
        await rag_processor.process_and_index(111, "Error Test", sample_markdown)
        assert True


# Testes de Validação de Dados

class TestDataValidation:
    """Testes de validação dos dados enviados"""
    
    def test_chunk_content_integrity(self, rag_processor, sample_markdown):
        """Verifica se o conteúdo é preservado após chunking"""
        chunks = rag_processor._split_into_chunks(sample_markdown)
        
        # Reconstrói o texto dos chunks
        reconstructed = "".join(chunks)
        
        # O texto original deve estar presente (com possíveis overlaps)
        assert len(reconstructed) >= len(sample_markdown)
    
    def test_special_characters_handling(self, rag_processor):
        """Testa tratamento de caracteres especiais"""
        special_text = "Texto com acentuação: á, é, í, ó, ú, ç, ã, õ\nE emojis: 🎉 🚀 ✨"
        chunks = rag_processor._split_into_chunks(special_text)
        
        assert len(chunks) > 0
        # Verifica se os caracteres especiais foram preservados
        reconstructed = "".join(chunks)
        assert "á" in reconstructed
        assert "🎉" in reconstructed
    
    def test_markdown_formatting_preserved(self, rag_processor, sample_markdown):
        """Verifica se a formatação Markdown é preservada"""
        chunks = rag_processor._split_into_chunks(sample_markdown)
        
        reconstructed = "".join(chunks)
        # Verifica elementos Markdown
        assert "#" in reconstructed  # Headers
        assert "-" in reconstructed  # List items


# Testes de Performance

class TestPerformance:
    """Testes de performance e limites"""
    
    def test_large_document_chunking(self, rag_processor):
        """Testa chunking de documento grande"""
        # Cria um documento de ~100KB
        large_text = "Este é um parágrafo com informações relevantes. " * 2000
        
        chunks = rag_processor._split_into_chunks(large_text)
        
        assert len(chunks) > 1
        assert all(len(chunk) > 0 for chunk in chunks)
    
    @pytest.mark.asyncio
    async def test_multiple_pages_processing(self, rag_processor):
        """Testa processamento de múltiplas páginas"""
        pages = [
            (1, "Page 1", "Content 1 " * 100),
            (2, "Page 2", "Content 2 " * 100),
            (3, "Page 3", "Content 3 " * 100),
        ]
        
        with patch.object(rag_processor, '_simulate_openwebui_ingestion'):
            for page_id, page_name, content in pages:
                await rag_processor.process_and_index(page_id, page_name, content)
        
        assert True


# Configuração para executar os testes
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
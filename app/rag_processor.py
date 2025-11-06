import os
import requests
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Any

load_dotenv()

class RAGProcessor:
    """
    Processa o conteúdo Markdown, divide em chunks e simula a inserção
    no Knowledge Base do Open WebUI.
    """
    def __init__(self):
        self.base_url = os.getenv("OPENWEBUI_BASE_URL")
        self.api_key = os.getenv("OPENWEBUI_API_KEY")
        self.kb_name = os.getenv("OPENWEBUI_KNOWLEDGE_BASE_NAME")
        
        # Configurações de chunking
        try:
            self.chunk_size = int(os.getenv("CHUNK_SIZE", 1000))
            self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", 200))
        except ValueError:
            print("Aviso: CHUNK_SIZE ou CHUNK_OVERLAP inválido. Usando valores padrão (1000/200).")
            self.chunk_size = 1000
            self.chunk_overlap = 200

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def _split_into_chunks(self, content: str) -> List[str]:
        """
        Divide o conteúdo em chunks usando o LangChain RecursiveCharacterTextSplitter.
        """
        return self.text_splitter.split_text(content)

    def _simulate_openwebui_ingestion(self, page_id: int, page_name: str, chunks: List[str]):
        """
        Simula a chamada à API do Open WebUI para ingestão de documentos.
        
        NOTA: O Open WebUI não possui um endpoint de API público e direto para
        upload de documentos RAG. A ingestão é feita geralmente via interface
        ou por meio de um processo de sincronização de diretório.
        
        Para este projeto, vamos simular a chamada de API.
        """
        if not all([self.base_url, self.api_key, self.kb_name]):
            print("Aviso: Credenciais do Open WebUI incompletas. Simulação de ingestão ignorada.")
            return

        # Endpoint de ingestão simulado
        # Você precisará adaptar isso ao endpoint real do Open WebUI, se houver.
        ingestion_endpoint = f"{self.base_url}/api/v1/knowledge-base/{self.kb_name}/ingest"
        
        print(f"Simulando ingestão no Open WebUI Knowledge Base: {self.kb_name}")
        print(f"Endpoint: {ingestion_endpoint}")
        print(f"Total de chunks a serem enviados: {len(chunks)}")
        
        # Metadados para o documento
        metadata = {
            "source": f"BookStack Page ID: {page_id}",
            "title": page_name,
            "url": f"{os.getenv('BOOKSTACK_BASE_URL')}view/{page_id}"
        }
        
        # Simulação de envio de cada chunk
        for i, chunk in enumerate(chunks):
            payload = {
                "chunk_id": f"{page_id}-{i}",
                "text": chunk,
                "metadata": metadata
            }
            
            # Simulação de requisição POST
            # response = requests.post(ingestion_endpoint, headers=self.headers, json=payload)
            # if response.status_code == 200:
            # #     print(f"Chunk {i+1}/{len(chunks)} enviado com sucesso.")
            # # else:
            # #     print(f"Erro ao enviar chunk {i+1}/{len(chunks)}: {response.text}")
            
            print(f"Chunk {i+1}/{len(chunks)} simulado. Tamanho: {len(chunk)} caracteres.")
            
        print("Simulação de ingestão concluída.")


    async def process_and_index(self, page_id: int, page_name: str, markdown_content: str):
        """
        Processa o conteúdo e inicia a simulação de indexação.
        """
        # 1. Dividir em chunks
        chunks = self._split_into_chunks(markdown_content)
        
        # 2. Simular ingestão no Open WebUI
        self._simulate_openwebui_ingestion(page_id, page_name, chunks)

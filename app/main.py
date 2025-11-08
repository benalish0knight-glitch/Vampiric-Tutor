import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import Optional, List

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# --- Configurações ---
BOOKSTACK_BOOK_IDS = os.getenv("BOOKSTACK_BOOK_IDS")
if not BOOKSTACK_BOOK_IDS:
    raise ValueError("BOOKSTACK_BOOK_IDS não está configurado no .env")

try:
    # Converter string de IDs separados por vírgula em lista de inteiros
    MONITORED_BOOK_IDS = [int(book_id.strip()) for book_id in BOOKSTACK_BOOK_IDS.split(",")]
except ValueError:
    raise ValueError("BOOKSTACK_BOOK_IDS deve conter números inteiros separados por vírgula (ex: 1,2,3)")

from bookstack_api import BookStackAPI
from rag_processor import RAGProcessor

# Inicializar a aplicação FastAPI
app = FastAPI(title="BookStack RAG Sync Service")

# Inicializar clientes de API
bookstack_api = BookStackAPI()
rag_processor = RAGProcessor()

# --- Modelos Pydantic para o Webhook Payload ---

class WebhookRelatedItem(BaseModel):
    id: int
    name: str
    slug: str
    book_id: int
    chapter_id: Optional[int] = None
    url: str

class WebhookPayload(BaseModel):
    event: str
    text: str
    url: str
    related_item: WebhookRelatedItem

# --- Funções de Processamento em Background ---

async def process_bookstack_update(page_id: int, page_name: str):
    """
    Função principal para extrair, processar e indexar o conteúdo.
    """
    print(f"Iniciando processamento para a página ID: {page_id} ({page_name})")
    
    # 1. Extrair conteúdo da página
    markdown_content = await run_in_threadpool(
        bookstack_api.get_page_content, page_id
    )
    
    if not markdown_content:
        print(f"Aviso: Não foi possível obter o conteúdo da página {page_id}.")
        return

    # 2. Processar e indexar no RAG
    await rag_processor.process_and_index(page_id, page_name, markdown_content)
    
    print(f"Processamento concluído para a página ID: {page_id}")


# --- Endpoint do Webhook ---

@app.post("/webhook/bookstack")
async def bookstack_webhook(payload: WebhookPayload, background_tasks: BackgroundTasks):
    """
    Recebe o payload do webhook do BookStack e inicia o processo de sincronização.
    """
    # 1. Verificar o tipo de evento
    if payload.event not in ["page_update", "page_create"]:
        print(f"Evento ignorado: {payload.event}")
        return {"status": "ignored", "reason": f"Event type {payload.event} not supported"}

    page_id = payload.related_item.id
    book_id = payload.related_item.book_id
    page_name = payload.related_item.name

    # 2. Verificar se o livro está na lista de livros monitorados
    is_monitored = await run_in_threadpool(
        bookstack_api.is_book_monitored, book_id, MONITORED_BOOK_IDS
    )

    if not is_monitored:
        print(f"Atualização ignorada: Livro ID {book_id} não está na lista de livros monitorados.")
        print(f"Livros monitorados: {MONITORED_BOOK_IDS}")
        return {"status": "ignored", "reason": "Book not in monitored list"}

    # 3. Adicionar a tarefa de processamento em background
    background_tasks.add_task(process_bookstack_update, page_id, page_name)

    return {"status": "success", "message": f"Processamento da página {page_id} iniciado em background."}

@app.get("/")
def read_root():
    return {
        "message": "BookStack RAG Sync Service está rodando.",
        "monitored_books": MONITORED_BOOK_IDS
    }

@app.get("/health")
def health_check():
    """Endpoint de verificação de saúde do serviço"""
    return {
        "status": "healthy",
        "monitored_books_count": len(MONITORED_BOOK_IDS),
        "monitored_books": MONITORED_BOOK_IDS
    }
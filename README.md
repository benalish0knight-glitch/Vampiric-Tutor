# Vampiric Tutor


<div align="center">
<img src="https://cards.scryfall.io/large/front/7/9/796018f1-f1e0-41ab-be55-9cb61bb2e9fe.jpg?1562919357" alt="Vampiric Tutor" width="50%" height="50%">
</div>

Este projeto Python, orquestrado com Docker Compose, atua como um serviço de sincronização em tempo real entre o **BookStack** e o sistema **RAG (Retrieval-Augmented Generation)** do **Open WebUI**.

O serviço monitora atualizações em uma estante específica do BookStack via webhook, extrai o conteúdo da página atualizada e o processa (dividindo em *chunks*) para indexação no Knowledge Base do Open WebUI.

## Funcionalidades

1.  **Receptor Webhook (FastAPI)**: Recebe notificações de `page_update` e `page_create` do BookStack.
2.  **Filtro de Estante**: Verifica se a página atualizada pertence a uma estante (Shelf ID) pré-configurada.
3.  **Extração de Conteúdo**: Utiliza a API REST do BookStack para extrair o conteúdo da página em formato Markdown.
4.  **Processamento RAG (LangChain)**: Divide o conteúdo em *chunks* de tamanho configurável para otimizar a indexação e a recuperação de contexto.
5.  **Simulação de Ingestão Open WebUI**: Simula o envio dos *chunks* para o Knowledge Base do Open WebUI.

## Estrutura do Projeto

```
bookstack-rag-sync/
├── app/
│   ├── main.py             # Aplicação FastAPI (Webhook e orquestração)
│   ├── bookstack_api.py    # Cliente para a API do BookStack
│   └── rag_processor.py    # Lógica de chunking e simulação de ingestão RAG
├── .env                    # Variáveis de ambiente (credenciais e configurações)
├── Dockerfile              # Definição da imagem Docker da aplicação
├── docker-compose.yml      # Orquestração do serviço
└── requirements.txt        # Dependências Python
```

## Configuração

### 1. Variáveis de Ambiente (`.env`)

Crie e preencha o arquivo `.env` na raiz do projeto com suas credenciais e configurações.

| Variável | Descrição | Exemplo |
| :--- | :--- | :--- |
| `BOOKSTACK_BASE_URL` | URL base da sua instância do BookStack. | `https://bookstack.exemplo.com` |
| `BOOKSTACK_TOKEN_ID` | Token ID da API do BookStack. | `seu_token_id` |
| `BOOKSTACK_TOKEN_SECRET` | Token Secret da API do BookStack. | `seu_token_secret` |
| `BOOKSTACK_SHELF_ID` | **ID da estante a ser monitorada.** | `2` |
| `OPENWEBUI_BASE_URL` | URL base da sua instância do Open WebUI. | `http://openwebui:8080` |
| `OPENWEBUI_API_KEY` | Token de autenticação da API do Open WebUI (se necessário). | `seu_api_key` |
| `OPENWEBUI_KNOWLEDGE_BASE_NAME` | Nome do Knowledge Base no Open WebUI. | `bookstack-knowledge` |
| `CHUNK_SIZE` | Tamanho máximo de cada chunk de texto (padrão: 1000). | `1000` |
| `CHUNK_OVERLAP` | Sobreposição de texto entre chunks (padrão: 200). | `200` |

### 2. Configuração do Webhook no BookStack

1.  Acesse a área de administração do seu BookStack.
2.  Vá para **Settings** > **Webhooks**.
3.  Crie um novo Webhook com as seguintes configurações:
    *   **Webhook Endpoint**: A URL pública do seu serviço, apontando para o endpoint do webhook. Exemplo: `http://seu-ip-publico:8000/webhook/bookstack`
    *   **Events**: Selecione os eventos **Page Update** e **Page Create**.

## Execução do Projeto

1.  **Construir e Iniciar o Serviço:**
    ```bash
    docker-compose up --build -d
    ```
2.  **Verificar Logs:**
    ```bash
    docker-compose logs -f bookstack-rag-sync
    ```

## Observação sobre a Ingestão no Open WebUI

O módulo `rag_processor.py` contém uma **simulação** da chamada de API para o Open WebUI.

> **Atenção**: O Open WebUI não possui um endpoint de API público e direto para upload de documentos RAG. A ingestão é feita geralmente via interface ou por meio de um processo de sincronização de diretório.

Se o Open WebUI não expuser um endpoint de ingestão direta, você precisará adaptar a função `_simulate_openwebui_ingestion` para:

1.  Salvar o conteúdo processado em um arquivo Markdown (ex: `/data/page_123.md`).
2.  Montar o diretório `/data` no container do Open WebUI para que ele possa monitorar e indexar automaticamente os novos arquivos.

A lógica de chunking e processamento de metadados está pronta para ser integrada ao método de ingestão que você escolher.

---
*Documento gerado por **Manus AI**.*
# Vampiric Tutor


<div align="center">
<img src="./img/vampiric-tutor.jpg" alt="Vampiric Tutor" width="50%" height="50%">
</div>

## Iniciando o serviço

```bash
docker compose up -d

docker compose ps
```
## Teste inicial

```bash
curl http://localhost:8000/
```

```json
{"message":"BookStack RAG Sync Service está rodando.","monitored_books":[1,2,3]}
```


```bash
curl http://localhost:8000/health
```

```json
{"status":"healthy","monitored_books_count":3,"monitored_books":[1,2,3]}
```

### Teste com Bookstack (Webhook):

#### Teste 1:

Salve como webhook_payload.json

```json
{
    "event": "page_update",
    "text": "Página 'Minha Página de Teste' foi atualizada.",
    "url": "https://bookstack.exemplo.com/books/2/page/101",
    "related_item": {
        "id": 101,
        "name": "Minha Página de Teste",
        "slug": "minha-pagina-de-teste",
        "book_id": 2,
        "chapter_id": null,
        "url": "https://bookstack.exemplo.com/books/2/page/101"
    }
}
```

```bash
curl -X POST http://localhost:8000/webhook/bookstack \
     -H "Content-Type: application/json" \
     -d @webhook_payload.json

```

Resultado Esperado (Resposta Imediata do Servidor ):

```json
{"status":"success","message":"Processamento da página 101 iniciado em background."}
```

#### Teste 2

```bash
curl -X POST http://localhost:8000/webhook/bookstack \
  -H "Content-Type: application/json" \
  -d '{
    "event": "page_update",
    "text": "Benny updated page \"My wonderful updated page\"",
    "url": "https://bookstack.local/books/my-awesome-book/page/my-wonderful-updated-page",
    "related_item": {
      "id": 2432,
      "book_id": 13,
      "chapter_id": 554,
      "name": "My wonderful updated page",
      "slug": "my-wonderful-updated-page",
      "url": "https://bookstack.local/books/my-awesome-book/page/my-wonderful-updated-page"
    }
  }'
```

```json
{"status":"success","message":"Processamento da página 2432 iniciado em background."}
```

#### Teste 2

```bash
curl -X POST http://localhost:8000/webhook/bookstack \
  -H "Content-Type: application/json" \
  -d '{
    "event": "page_update",
    "text": "Test page update",
    "url": "https://bookstack.local/books/test/page/test",
    "related_item": {
      "id": 1,
      "book_id": 999,
      "name": "Test Page",
      "slug": "test-page",
      "url": "https://bookstack.local/books/test/page/test"
    }
  }'
```

```json
{"status":"ignored","reason":"Book not in monitored list"}
```
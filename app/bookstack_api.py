import os
import requests
from dotenv import load_dotenv

load_dotenv()

class BookStackAPI:
    """
    Cliente para interagir com a API REST do BookStack.
    """
    def __init__(self):
        self.base_url = os.getenv("BOOKSTACK_BASE_URL")
        self.token_id = os.getenv("BOOKSTACK_TOKEN_ID")
        self.token_secret = os.getenv("BOOKSTACK_TOKEN_SECRET")

        if not all([self.base_url, self.token_id, self.token_secret]):
            # Não levantar exceção aqui, pois o .env pode estar vazio.
            # A validação ocorrerá na execução se as credenciais forem necessárias.
            pass

        # Garantir que a URL base termine com barra
        if self.base_url and not self.base_url.endswith('/'):
            self.base_url += '/'

        self.headers = {
            "Authorization": f"Token {self.token_id}:{self.token_secret}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def _make_request(self, method: str, endpoint: str, **kwargs):
        """
        Função auxiliar para fazer requisições à API do BookStack.
        """
        if not all([self.base_url, self.token_id, self.token_secret]):
            print("Erro: Credenciais do BookStack API não configuradas.")
            return None
            
        url = f"{self.base_url}api/{endpoint}"
        try:
            # Usando requests síncrono, pois o FastAPI lida com a assincronicidade
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"Erro HTTP ao acessar {url}: {e}")
            print(f"Resposta: {e.response.text}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Erro de requisição ao acessar {url}: {e}")
            return None

    def get_book_details(self, book_id: int) -> dict:
        """
        Obtém os detalhes de um livro, incluindo suas páginas e capítulos.
        Endpoint: GET /api/books/{id}
        """
        endpoint = f"books/{book_id}"
        return self._make_request("GET", endpoint)

    def get_page_content(self, page_id: int) -> str:
        """
        Obtém o conteúdo de uma página em formato Markdown.
        Endpoint: GET /api/pages/{id}
        """
        endpoint = f"pages/{page_id}"
        data = self._make_request("GET", endpoint)
        
        if data and 'markdown' in data:
            # O campo 'markdown' contém o conteúdo da página
            return data['markdown']
        
        return ""

    def is_book_monitored(self, book_id: int, monitored_book_ids: list) -> bool:
        """
        Verifica se um livro específico está na lista de livros monitorados.
        """
        return book_id in monitored_book_ids
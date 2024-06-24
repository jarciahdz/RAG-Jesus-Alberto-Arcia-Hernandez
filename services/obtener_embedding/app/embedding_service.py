import openai
import requests

def get_embedding(text, api_key, model):
    if not text:
        raise ValueError("El texto no puede estar vacío")
    
    openai.api_key = api_key
    try:
        # Configurar la sesión de requests y deshabilitar la verificación SSL
        session = requests.Session()
        session.verify = False
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "input": text,
            "model": model
        }
 
        response = session.post("https://api.openai.com/v1/embeddings", headers=headers, json=data)
        response.raise_for_status()  # Levanta una excepción para códigos de estado HTTP 4xx/5xx
        embedding = response.json()['data'][0]['embedding']
        return embedding
    except requests.exceptions.SSLError as e:
        print(f"SSL error: {e}")
        raise
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        raise RuntimeError("OpenAI API error")

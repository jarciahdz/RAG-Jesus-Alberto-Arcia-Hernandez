import sys
import os
import time

# Añadir la ruta del proyecto al PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from flask import Flask, request, jsonify, make_response
import requests
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_cors import CORS
import openai
from app.generate_response import construir_contexto
from app.config import Config



# Configuración de la clave de API de OpenAI
openai.api_key = Config.OPENAI_API_KEY

# Inicialización de la aplicación Flask
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config.from_object(Config)
app.config[Config.TEXTSECRET_KEY] = Config.SECRET_KEY  # Necesario para CSRFProtect
csrf = CSRFProtect(app)

# # Lista de orígenes de confianza
# TRUSTED_ORIGINS = [Config.TRUSTDOMAIN_5]

# # Configuración segura de CORS
# CORS(app, resources={r"/*": {"origins": TRUSTED_ORIGINS}})

def check_access_key(request):
    """
    Verifica si la clave de acceso en la solicitud es válida.
    
    Args:
    request (Request): La solicitud HTTP.
    
    Returns:
    bool: True si la clave de acceso es válida, False de lo contrario.
    """
    access_key = request.headers.get('Access-Key')
    return access_key == Config.SECRET_KEY

@app.route('/', methods=['GET'])
def index():
    """
    Ruta principal de la aplicación.
    
    Returns:
    Response: Respuesta HTTP con un mensaje de bienvenida y el token CSRF.
    """
    token = generate_csrf()
    response = make_response(jsonify({"message": "Welcome to API!", "csrf_token": token}))
    response.set_cookie('csrf_token', token, secure=True, httponly=True)
    return response

def make_openai_request(question, context):
    """
    Realiza una solicitud a la API de OpenAI para generar una respuesta basada en el contexto proporcionado.

    Args:
    question (str): La pregunta del usuario.
    context (str): El contexto construido a partir de las películas relevantes.

    Returns:
    Response: La respuesta de la API de OpenAI.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai.api_key}"
    }
    json_data = {
        "model": "gpt-4",
        "messages": [
            {
                "role": "system",
                "content": ("You are a friendly and helpful assistant. Your task is to answer questions based solely "
                            "on the provided context. This context includes a link to an image from the movie, a "
                            "description, and a similarity metric that indicates how relevant the context is to the "
                            "question based on documents retrieved from the database. Avoid using any external "
                            "information or personal knowledge. If the context does not provide enough information "
                            "to answer the question, respond with 'No lo sé basándome en el contexto proporcionado.' "
                            "Ensure your answers are natural, concise, and directly related to the given context. "
                            "Include the link to the image, the movie description, and the similarity metric in your "
                            "response only if the question explicitly requests it. Maintain a polite and helpful tone "
                            "in all your responses. Always respond in Spanish.")
            },
            {
                "role": "user",
                "content": f"Pregunta: {question}\nContexto: {context}\nRespuesta:"
            }
        ]
    }
    retries = 5
    for i in range(retries):
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=json_data
            
        )
        if response.status_code == 429:
            wait_time = (2 ** i) * 10  # Tiempo de espera exponencial
            print(f"HTTP 429 Too Many Requests - waiting {wait_time} seconds before retrying...")
            time.sleep(wait_time)
        else:
            response.raise_for_status()
            return response
    response.raise_for_status()  # Levantar una excepción si todos los reintentos fallan

@app.route('/ask', methods=['POST'])
def ask():
    """
    Endpoint para recibir preguntas y devolver respuestas basadas en embeddings de películas relevantes.
    
    Returns:
    Response: Respuesta HTTP con la respuesta generada o un mensaje de error.
    """
    if not check_access_key(request):
        return jsonify({"error": "Unauthorized access"}), 403

    data = request.json
    question = data.get('question')
    relevant_movies = data.get('relevant_movies')

    if not question or not relevant_movies:
        return jsonify({"error": "Missing question or relevant_movies"}), 400

    context = construir_contexto(question, relevant_movies)
    response = make_openai_request(question, context)
    answer = response.json()["choices"][0]["message"]["content"].strip()
    return jsonify({"answer": answer})

# @app.after_request
# def after_request(response):
#     """
#     Configura los encabezados de CORS después de cada solicitud.

#     Args:
#     response (Response): La respuesta HTTP.

#     Returns:
#     Response: La respuesta HTTP con los encabezados de CORS configurados.
#     """
#     origin = request.headers.get('Origin')
#     if origin in TRUSTED_ORIGINS:
#         response.headers.add('Access-Control-Allow-Origin', origin)
#         response.headers.add('Access-Control-Allow-Credentials', 'true')
#     return response

def run_app():
    """
    Configura y ejecuta la aplicación Flask.
    """
    app.run(host='0.0.0.0', port=5005, debug=False)

if __name__ == '__main__' and 'test' not in sys.argv:
    run_app()
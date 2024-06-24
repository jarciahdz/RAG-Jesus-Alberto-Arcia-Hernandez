import sys
import os
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect, generate_csrf

# Asegurar que el directorio raíz del proyecto esté en el PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.retrieval_service import get_relevant_movies
from app.config import Config

# Inicialización de la aplicación Flask
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config.from_object(Config)
app.config[Config.TEXTSECRET_KEY] = Config.SECRET_KEY  # Necesario para CSRFProtect
csrf = CSRFProtect(app)

# # Lista de orígenes de confianza
# TRUSTED_ORIGINS = [Config.TRUSTDOMAIN_4]

# # Configuración segura de CORS
# CORS(app, resources={r"/*": {"origins": TRUSTED_ORIGINS}})

# Constantes de mensajes y errores
ERROR_UNAUTHORIZED = {"error": "Unauthorized access"}
ERROR_NO_QUESTION = {"error": "No question provided"}
ERROR_NO_EMBEDDING = {"error": "No embedding provided"}
SUCCESS_MESSAGE = {"message": "Welcome to the get_relevant_embeddings API!"}


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

@app.route('/get_relevant_embeddings', methods=['POST'])
def get_relevant_embeddings_route():
    """
    Endpoint para obtener embeddings relevantes de películas basados en la entrada del usuario.
    
    Returns:
    Response: Respuesta HTTP con los embeddings relevantes o un mensaje de error.
    """
    if not check_access_key(request):
        return jsonify(ERROR_UNAUTHORIZED), 403

    data = request.json
    question = data.get('question')
    query_embedding = data.get('embedding')
    
    if not question:
        return jsonify(ERROR_NO_QUESTION), 400
    
    if not query_embedding:
        return jsonify(ERROR_NO_EMBEDDING), 400
    
    relevant_movies = get_relevant_movies(query_embedding)

    return jsonify({"question": question, "relevant_movies": relevant_movies})


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
    app.run(host='0.0.0.0', port=5004, debug=False)


if __name__ == '__main__' and 'test' not in sys.argv:
    run_app()
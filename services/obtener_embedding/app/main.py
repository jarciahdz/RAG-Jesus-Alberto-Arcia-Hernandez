import sys
import os
from flask import Flask, request, jsonify, make_response
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_cors import CORS

# Asegurar que el directorio del microservicio esté en el sys.path para las importaciones correctas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.embedding_service import get_embedding
from app.config import Config

# Inicialización de la aplicación Flask
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config.from_object(Config)
app.config[Config.TEXTSECRET_KEY] = Config.SECRET_KEY  # Necesario para CSRFProtect
csrf = CSRFProtect(app)

# # Lista de orígenes de confianza
# TRUSTED_ORIGINS = [Config.TRUSTDOMAIN_2]

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


@app.route('/get_embedding', methods=['POST'])
def get_embedding_route():
    if not check_access_key(request):
        return jsonify({"error": "Unauthorized access"}), 403

    data = request.json
    question = data.get('question')

    if not question:
        return jsonify({"error": "No question provided"}), 400

    try:
        embedding = get_embedding(question, Config.OPENAI_API_KEY, Config.OPENAI_MODEL)
        return jsonify({"question": question, "embedding": embedding})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500


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
    app.run(host='0.0.0.0', port=5002, debug=False)

if __name__ == '__main__' and 'test' not in sys.argv:
    run_app()

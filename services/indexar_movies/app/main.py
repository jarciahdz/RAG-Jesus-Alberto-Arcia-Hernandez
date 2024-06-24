import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from flask import Flask, request, jsonify, make_response
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_cors import CORS
from app.index_embeddings import index_embeddings
from app.config import Config
from app.s3_file_manager import create_bucket, upload_to_s3



# Inicialización de la aplicación Flask
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config.from_object(Config)
app.config[Config.TEXTSECRET_KEY] = Config.SECRET_KEY  # Necesario para CSRFProtect
csrf = CSRFProtect(app)

# # Lista de orígenes de confianza
# TRUSTED_ORIGINS = [Config.TRUSTDOMAIN_6]

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

@app.route('/index', methods=['POST'])
def index_route():
    """
    Ruta para indexar embeddings de películas.
    
    Returns:
        Response: Respuesta HTTP con el resultado de la indexación.
    """
    if not check_access_key(request):
        return jsonify({"error": "Unauthorized access"}), 403

    bucket_name = request.json.get('bucket_name')
    s3_file_key = request.json.get('s3_file_key')

    try:
        index_embeddings(bucket_name, s3_file_key)
        return jsonify({"message": "Indexing completed"}), 200
    except Exception as e:
        print(f"Error during indexing: {e}")
        return jsonify({"error": "Indexing failed"}), 500

@app.route('/upload', methods=['POST'])
def upload_route():
    """
    Ruta para subir archivos a S3.
    
    Returns:
        Response: Respuesta HTTP con el resultado de la subida.
    """
    if not check_access_key(request):
        return jsonify({"error": "Unauthorized access"}), 403

    file_path = request.json.get('file_path')
    bucket_name = request.json.get('bucket_name')
    s3_file_key = request.json.get('s3_file_key')
    region = request.json.get('region', 'us-west-1')

    create_bucket(bucket_name, region)
    upload_to_s3(file_path, bucket_name, s3_file_key)
    
    return jsonify({
        "message": "File uploaded successfully",
        "bucket_name": bucket_name,
        "s3_file_key": s3_file_key
    }), 200

# @app.after_request
# def after_request(response):
#     """
#     Configura los encabezados de CORS después de cada solicitud.

#     Args:
#         response (Response): La respuesta HTTP.

#     Returns:
#         Response: La respuesta HTTP con los encabezados de CORS configurados.
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
    app.run(host='0.0.0.0', port=5006, debug=False)

if __name__ == '__main__' and 'test' not in sys.argv:
    run_app()
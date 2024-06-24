import sys
import os
import pytest
from unittest import mock
from flask import json, request
from flask import get_flashed_messages


# Asegurar que el directorio del microservicio esté en el sys.path para las importaciones correctas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from main import app, check_access_key, run_app
from config import Config
from app.improve_question import mejorar_pregunta



# Esta fixture configura la aplicación Flask para pruebas y proporciona un cliente de pruebas.
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = Config.WTF_CSRF_ENABLED  # Deshabilitar CSRF para las pruebas
    with app.test_client() as client:
        yield client

# Pruebas para verificar que la clave de acceso se valida correctamente.
def test_check_access_key_valid(client):
    with app.test_request_context(headers={'Access-Key': Config.SECRET_KEY}):
        assert check_access_key(request) is True

def test_check_access_key_invalid(client):
    with app.test_request_context(headers={'Access-Key': 'invalid_key'}):
        assert check_access_key(request) is False

# Prueba que simula una solicitud exitosa al endpoint /improve_question utilizando un monkeypatch para la API de OpenAI.
def test_mejorar_pregunta_route_success(client, monkeypatch):
    class MockResponse:
        def __init__(self):
            self.choices = [MockChoice()]

    class MockChoice:
        def __init__(self):
            self.message = {'content': 'Esta es una pregunta corregida.'}

    def mock_chat_completion_create(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr("openai.ChatCompletion.create", mock_chat_completion_create)

    response = client.post('/improve_question', json={
        'question': 'Esta es una prueba?'
    }, headers={'Access-Key': Config.SECRET_KEY, 'Origin': 'http://localhost:5001'})

    data = json.loads(response.data)
    assert response.status_code == 200
    assert data['question'] == 'Esta es una pregunta corregida.'
    assert response.headers['Access-Control-Allow-Origin'] == 'http://localhost:5001'
    assert response.headers['Access-Control-Allow-Credentials'] == 'true'

## Pruebas de Casos Negativos
# Sin Pregunta Proporcionada
def test_mejorar_pregunta_route_no_question(client):
    response = client.post('/improve_question', json={}, headers={'Access-Key': Config.SECRET_KEY, 'Origin': 'http://localhost:5001'})
    data = json.loads(response.data)
    assert response.status_code == 400
    assert data['error'] == 'No question provided'
    assert response.headers['Access-Control-Allow-Origin'] == 'http://localhost:5001'
    assert response.headers['Access-Control-Allow-Credentials'] == 'true'

# Acceso No Autorizado
def test_mejorar_pregunta_route_unauthorized(client):
    response = client.post('/improve_question', json={
        'question': 'Esta es una prueba?'
    }, headers={'Access-Key': 'invalid_key', 'Origin': 'http://localhost:5001'})
    data = json.loads(response.data)
    assert response.status_code == 403
    assert data['error'] == 'Unauthorized access'
    assert response.headers['Access-Control-Allow-Origin'] == 'http://localhost:5001'
    assert response.headers['Access-Control-Allow-Credentials'] == 'true'

# Error de la API de OpenAI
def test_mejorar_pregunta_route_openai_error(client, monkeypatch):
    def mock_chat_completion_create(*args, **kwargs):
        raise RuntimeError("OpenAI API error")

    monkeypatch.setattr("openai.ChatCompletion.create", mock_chat_completion_create)

    response = client.post('/improve_question', json={
        'question': 'Esta es una prueba?'
    }, headers={'Access-Key': Config.SECRET_KEY, 'Origin': 'http://localhost:5001'})

    data = json.loads(response.data)
    assert response.status_code == 500
    assert data['error'] == 'OpenAI API error'
    assert response.headers['Access-Control-Allow-Origin'] == 'http://localhost:5001'
    assert response.headers['Access-Control-Allow-Credentials'] == 'true'

# Prueba para mejorar_pregunta cuando la pregunta está vacía
def test_mejorar_pregunta_vacia():
    with pytest.raises(ValueError, match="La pregunta no puede estar vacía"):
        mejorar_pregunta("")

# Prueba para la ruta mejorar_pregunta con pregunta vacía para cubrir la línea `return jsonify({"error": str(e)}), 400`
def test_mejorar_pregunta_route_empty_question(client):
    response = client.post('/improve_question', json={
        'question': ''
    }, headers={'Access-Key': Config.SECRET_KEY, 'Origin': 'http://localhost:5001'})
    data = json.loads(response.data)
    assert response.status_code == 400
    assert data['error'] == 'No question provided'
    assert response.headers['Access-Control-Allow-Origin'] == 'http://localhost:5001'
    assert response.headers['Access-Control-Allow-Credentials'] == 'true'

# Prueba para mejorar_pregunta cuando la pregunta está vacía
def test_mejorar_pregunta_lanza_value_error():
    with pytest.raises(ValueError, match="La pregunta no puede estar vacía"):
        mejorar_pregunta("")  # Lanza el ValueError si la pregunta está vacía


# Prueba para verificar la configuración del servidor
def test_run_app(monkeypatch):
    def mock_run(*args, **kwargs):
        assert kwargs['host'] == '0.0.0.0'
        assert kwargs['port'] == 5001

    monkeypatch.setattr("main.app.run", mock_run)
    
    # Simular que el entorno es de desarrollo
    original_env = Config.FLASK_ENV
    Config.FLASK_ENV = 'development'
    try:
        run_app()
    finally:
        Config.FLASK_ENV = original_env

# Prueba para la ruta principal
def test_index_route(client):
    response = client.get('/')
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['message'] == "Welcome to the Improve Question API!"
    assert 'csrf_token' in response.headers.get('Set-Cookie')
    assert 'HttpOnly' in response.headers.get('Set-Cookie')
    assert 'Secure' in response.headers.get('Set-Cookie')
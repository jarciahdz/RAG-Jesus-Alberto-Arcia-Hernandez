import sys
import os
import pytest
from flask import json, request
import numpy as np

# Asegurar que el directorio del microservicio esté en el sys.path para las importaciones correctas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from main import app, check_access_key, run_app
from config import Config
from normalization_service import normalize_l2

@pytest.fixture
def client():
    """
    Configura la aplicación Flask para pruebas y proporciona un cliente de pruebas.
    """
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = Config.WTF_CSRF_ENABLED
    with app.test_client() as client:
        yield client

@pytest.mark.parametrize("headers,expected", [
    ({"Access-Key": Config.SECRET_KEY}, True),
    ({"Access-Key": "invalid_key"}, False),
])
def test_check_access_key(client, headers, expected):
    """
    Verifica la validación de la clave de acceso.
    """
    with app.test_request_context(headers=headers):
        assert check_access_key(request) is expected

def post_request(client, url, json_data, headers):
    """
    Helper function to perform a POST request and return the response and parsed data.
    """
    response = client.post(url, json=json_data, headers=headers)
    return response, json.loads(response.data)

def test_normalize_embedding_route_success(client, monkeypatch):
    """
    Simula una solicitud exitosa al endpoint /normalize_embedding.
    Verifica que la respuesta contiene el embedding normalizado correctamente.
    """
    def mock_normalize_l2(x):
        return [0, 0, 0]

    monkeypatch.setattr("app.normalization_service.normalize_l2", mock_normalize_l2)

    response, data = post_request(client, '/normalize_embedding', {
        'question': 'Test question?',
        'embedding': [0, 0, 0]
    }, {'Access-Key': Config.SECRET_KEY, 'Origin': 'http://localhost:5003'})

    assert response.status_code == 200
    assert data['embedding'] == [0, 0, 0]
    assert data['question'] == 'Test question?'
    assert response.headers['Access-Control-Allow-Origin'] == 'http://localhost:5003'
    assert response.headers['Access-Control-Allow-Credentials'] == 'true'

@pytest.mark.parametrize("json_data,error_message", [
    ({'embedding': [0, 0, 0]}, 'No question provided'),
    ({'question': 'Test question?'}, 'No embedding provided')
])
def test_normalize_embedding_route_errors(client, json_data, error_message):
    """
    Verifica que se devuelven errores adecuados cuando faltan datos en la solicitud.
    """
    response, data = post_request(client, '/normalize_embedding', json_data, {
        'Access-Key': Config.SECRET_KEY, 'Origin': 'http://localhost:5003'
    })

    assert response.status_code == 400
    assert data['error'] == error_message
    assert response.headers['Access-Control-Allow-Origin'] == 'http://localhost:5003'
    assert response.headers['Access-Control-Allow-Credentials'] == 'true'

def test_normalize_embedding_vacia():
    """
    Verifica que se maneje correctamente un vector vacío.
    """
    result = normalize_l2(np.array([]))
    assert result.tolist() == []

def test_index_route(client):
    """
    Verifica la ruta principal y las configuraciones de cookies.
    """
    response = client.get('/')
    data = json.loads(response.data)

    assert response.status_code == 200
    assert data['message'] == "Welcome to the normalize_embedding API!"
    assert 'csrf_token' in response.headers.get('Set-Cookie')
    assert 'HttpOnly' in response.headers.get('Set-Cookie')
    assert 'Secure' in response.headers.get('Set-Cookie')

def test_normalize_l2():
    """
    Verifica que un vector se normaliza correctamente utilizando la norma L2.
    """
    vector = np.array([3.0, 4.0])
    expected_result = np.array([0.6, 0.8])  # Vector normalizado
    
    result = normalize_l2(vector)
    
    # Utilizar np.allclose para comparar arrays de punto flotante
    assert np.allclose(result, expected_result), f"Expected {expected_result}, but got {result}"

def test_normalize_embedding_route_unauthorized(client):
    """
    Verifica que se devuelve un error 403 cuando la clave de acceso es inválida.
    """
    response, data = post_request(client, '/normalize_embedding', {
        'question': 'Test question?',
        'embedding': [0, 0, 0]
    }, {'Access-Key': 'invalid_key', 'Origin': 'http://localhost:5003'})

    assert response.status_code == 403
    assert data['error'] == 'Unauthorized access'
    assert response.headers['Access-Control-Allow-Origin'] == 'http://localhost:5003'
    assert response.headers['Access-Control-Allow-Credentials'] == 'true'

def test_run_app(monkeypatch):
    """
    Verifica la configuración del servidor para asegurar que se utiliza la configuración correcta.
    """
    def mock_run(*args, **kwargs):
        assert kwargs['host'] == '0.0.0.0'
        assert kwargs['port'] == 5003

    monkeypatch.setattr("main.app.run", mock_run)

    run_app()

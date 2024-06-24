import sys
import os
import pytest
import requests
from unittest.mock import patch, MagicMock
from flask import json, request

# Asegurar que el directorio del microservicio esté en el sys.path para las importaciones correctas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from main import app, check_access_key, run_app, get_embedding_route, after_request
from config import Config
from app.embedding_service import get_embedding


app.route('/get_embedding', methods=['POST'])(get_embedding_route)

@pytest.fixture
def client():
    """
    Configura la aplicación Flask para pruebas y proporciona un cliente de pruebas.
    """
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = Config.WTF_CSRF_ENABLED
    with app.test_client() as client:
        yield client

def test_check_access_key_valid(client):
    """
    Verifica que la clave de acceso se valida correctamente cuando es válida.
    """
    with app.test_request_context(headers={'Access-Key': Config.SECRET_KEY}):
        assert check_access_key(request) is True

def test_check_access_key_invalid(client):
    """
    Verifica que la clave de acceso no se valida cuando es inválida.
    """
    with app.test_request_context(headers={'Access-Key': 'invalid_key'}):
        assert check_access_key(request) is False


def test_get_embedding_route_no_question(client):
    headers = {'Access-Key': 'correct_key'}
    
    with patch('main.check_access_key') as mock_check_access_key:
        mock_check_access_key.return_value = True

        response = client.post('/get_embedding', json={}, headers=headers)
        json_data = response.get_json()
        
        assert response.status_code == 400
        assert json_data['error'] == 'No question provided'

def test_get_embedding_route_unauthorized(client):
    data = {'question': 'What is the capital of France?'}
    headers = {'Access-Key': 'wrong_key'}
    
    with patch('main.check_access_key') as mock_check_access_key:
        mock_check_access_key.return_value = False

        response = client.post('/get_embedding', json=data, headers=headers)
        json_data = response.get_json()
        
        assert response.status_code == 403
        assert json_data['error'] == 'Unauthorized access'


def test_get_embedding_vacia(monkeypatch):
    """
    Verifica que se lanza un ValueError cuando el texto está vacío.
    """
    def mock_get_embedding(*args, **kwargs):
        raise ValueError("El texto no puede estar vacío")
    
    monkeypatch.setattr("app.embedding_service.get_embedding", mock_get_embedding)
    
    with pytest.raises(ValueError, match="El texto no puede estar vacío"):
        get_embedding("", Config.OPENAI_API_KEY, Config.OPENAI_MODEL)

def test_run_app(monkeypatch):
    """
    Verifica la configuración del servidor para asegurar que se utiliza la configuración correcta.
    """
    def mock_run(*args, **kwargs):
        assert kwargs['host'] == '0.0.0.0'
        assert kwargs['port'] == 5002

    monkeypatch.setattr("main.app.run", mock_run)

    original_env = Config.FLASK_ENV
    Config.FLASK_ENV = 'development'
    try:
        run_app()
    finally:
        Config.FLASK_ENV = original_env

def test_index_route(client):
    """
    Verifica la ruta principal y las configuraciones de cookies.
    """
    response = client.get('/')
    data = json.loads(response.data)

    assert response.status_code == 200
    assert data['message'] == "Welcome to the get_embedding API!"
    assert 'csrf_token' in response.headers.get('Set-Cookie')
    assert 'HttpOnly' in response.headers.get('Set-Cookie')
    assert 'Secure' in response.headers.get('Set-Cookie')

def test_get_embedding_success():
    text = "test"
    api_key = "fake_api_key"
    model = "text-embedding-ada-002"

    # Mock response data
    mock_response_data = {
        "data": [
            {
                "embedding": [0.1, 0.2, 0.3]
            }
        ]
    }

    with patch('requests.Session.post') as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = get_embedding(text, api_key, model)
        assert result == [0.1, 0.2, 0.3]

def test_get_embedding_empty_text():
    text = ""
    api_key = "fake_api_key"
    model = "text-embedding-ada-002"
    with pytest.raises(ValueError, match="El texto no puede estar vacío"):
        get_embedding(text, api_key, model)

def test_get_embedding_ssl_error():
    text = "test"
    api_key = "fake_api_key"
    model = "text-embedding-ada-002"

    with patch('requests.Session.post') as mock_post:
        mock_post.side_effect = requests.exceptions.SSLError("SSL error")
        with pytest.raises(requests.exceptions.SSLError):
            get_embedding(text, api_key, model)

def test_get_embedding_request_exception():
    text = "test"
    api_key = "fake_api_key"
    model = "text-embedding-ada-002"

    with patch('requests.Session.post') as mock_post:
        mock_post.side_effect = requests.exceptions.RequestException("Request error")
        with pytest.raises(RuntimeError, match="OpenAI API error"):
            get_embedding(text, api_key, model)

def test_get_embedding_route_success(client):
    with patch('main.get_embedding') as mock_get_embedding:
        mock_get_embedding.return_value = [0.1, 0.2, 0.3]
        data = {'question': 'What is the capital of France?'}
        headers = {'Access-Key': 'correct_key'}
        
        with patch('main.check_access_key') as mock_check_access_key:
            mock_check_access_key.return_value = True

            response = client.post('/get_embedding', json=data, headers=headers)
            json_data = response.get_json()
            
            assert response.status_code == 200
            assert json_data['question'] == 'What is the capital of France?'
            assert json_data['embedding'] == [0.1, 0.2, 0.3]


def test_get_embedding_route_value_error(client):
    with patch('main.get_embedding') as mock_get_embedding:
        mock_get_embedding.side_effect = ValueError("El texto no puede estar vacío")
        data = {'question': 'Some question'}
        headers = {'Access-Key': 'correct_key'}
        
        with patch('main.check_access_key') as mock_check_access_key:
            mock_check_access_key.return_value = True

            response = client.post('/get_embedding', json=data, headers=headers)
            json_data = response.get_json()
            
            assert response.status_code == 400
            assert json_data['error'] == 'El texto no puede estar vacío'


def test_get_embedding_route_runtime_error(client):
    with patch('main.get_embedding') as mock_get_embedding:
        mock_get_embedding.side_effect = RuntimeError("OpenAI API error")
        data = {'question': 'What is the capital of France?'}
        headers = {'Access-Key': 'correct_key'}
        
        with patch('main.check_access_key') as mock_check_access_key:
            mock_check_access_key.return_value = True

            response = client.post('/get_embedding', json=data, headers=headers)
            json_data = response.get_json()
            
            assert response.status_code == 500
            assert json_data['error'] == 'OpenAI API error'





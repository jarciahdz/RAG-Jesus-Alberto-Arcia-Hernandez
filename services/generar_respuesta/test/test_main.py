import sys
import os
import pytest
from unittest import mock
from flask import json, request, make_response
import requests
import time

# Asegurar que el directorio del microservicio esté en el sys.path para las importaciones correctas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from main import app, check_access_key, run_app, make_openai_request
from config import Config
from app.generate_response import construir_contexto

# Fixture para configurar la aplicación Flask para pruebas y proporcionar un cliente de pruebas
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = Config.WTF_CSRF_ENABLED
    with app.test_client() as client:
        yield client

# Pruebas para verificar que la clave de acceso se valida correctamente
def test_check_access_key_valid(client):
    with app.test_request_context(headers={'Access-Key': Config.SECRET_KEY}):
        assert check_access_key(request) is True

def test_check_access_key_invalid(client):
    with app.test_request_context(headers={'Access-Key': 'invalid_key'}):
        assert check_access_key(request) is False

# Pruebas para la función construir_contexto en generate_response.py
def test_construir_contexto():
    question = "¿Cuál es la mejor película?"
    relevant_movies = [
        {"similarity": 0.9, "title": "Movie 1", "plot": "Plot 1", "image": "Image 1"},
        {"similarity": 0.8, "title": "Movie 2", "plot": "Plot 2", "image": "Image 2"}
    ]
    expected_context = (
        "Pregunta: ¿Cuál es la mejor película?\n\n"
        "Contexto:\n"
        "Similarity: 0.9\nTitle: Movie 1\nPlot: Plot 1\nImage: Image 1\n\n"
        "Similarity: 0.8\nTitle: Movie 2\nPlot: Plot 2\nImage: Image 2\n\n"
        "Respuesta:"
    )
    context = construir_contexto(question, relevant_movies)
    assert context == expected_context

def test_index_route(client):
    response = client.get('/')
    data = response.get_json()

    assert response.status_code == 200
    assert data['message'] == "Welcome to the ask API!"
    assert 'csrf_token' in response.headers.get('Set-Cookie')
    assert 'HttpOnly' in response.headers.get('Set-Cookie')
    assert 'Secure' in response.headers.get('Set-Cookie')

class MockResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {"choices": [{"message": {"content": "This is a response"}}]}

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.exceptions.HTTPError(f"Status code: {self.status_code}")

def mock_post_factory(status_code=200, json_data=None):
    def mock_post(*args, **kwargs):
        return MockResponse(status_code, json_data)
    return mock_post

def test_make_openai_request_success(monkeypatch):
    monkeypatch.setattr("requests.post", mock_post_factory())

    question = "What is the best movie?"
    context = "Here is the context"
    response = make_openai_request(question, context)
    assert response.status_code == 200
    assert response.json()["choices"][0]["message"]["content"] == "This is a response"

def test_make_openai_request_retry(monkeypatch):
    def mock_post(*args, **kwargs):
        if mock_post.call_count < 4:
            mock_post.call_count += 1
            return MockResponse(429)
        else:
            return MockResponse(200)
    mock_post.call_count = 0

    monkeypatch.setattr("requests.post", mock_post)
    monkeypatch.setattr("time.sleep", lambda x: None)  # Evitar esperar en las pruebas

    question = "What is the best movie?"
    context = "Here is the context"
    response = make_openai_request(question, context)
    assert response.status_code == 200

def test_make_openai_request_failure(monkeypatch):
    monkeypatch.setattr("requests.post", mock_post_factory(500))

    question = "What is the best movie?"
    context = "Here is the context"

    with pytest.raises(requests.exceptions.HTTPError):
        make_openai_request(question, context)

def test_run_app(monkeypatch):
    def mock_run(*args, **kwargs):
        assert kwargs['host'] == '0.0.0.0'
        assert kwargs['port'] == 5005

    monkeypatch.setattr("main.app.run", mock_run)

    # Simular que el entorno es de desarrollo
    original_env = Config.FLASK_ENV
    Config.FLASK_ENV = 'development'
    try:
        run_app()
    finally:
        Config.FLASK_ENV = original_env

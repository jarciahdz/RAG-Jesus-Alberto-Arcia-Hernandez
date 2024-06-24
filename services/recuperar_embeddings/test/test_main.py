import sys
import os
import pytest
import unittest
from unittest.mock import patch, MagicMock
from flask import json, request

# Asegurar que el directorio del microservicio esté en el sys.path para las importaciones correctas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from main import app, check_access_key, run_app, get_relevant_embeddings_route, after_request
from config import Config
from app.retrieval_service import get_relevant_movies


app.route('/get_relevant_embeddings', methods=['POST'])(get_relevant_embeddings_route)

@pytest.fixture
def client():
    """
    Configura la aplicación Flask para pruebas y proporciona un cliente de pruebas.
    """
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = Config.WTF_CSRF_ENABLED
    with app.test_client() as client:
        yield client

def test_check_access_key(client):
    """
    Verifica que la clave de acceso se valida correctamente cuando es válida e inválida.
    """
    with app.test_request_context(headers={'Access-Key': Config.SECRET_KEY}):
        assert check_access_key(request) is True
    with app.test_request_context(headers={'Access-Key': 'invalid_key'}):
        assert check_access_key(request) is False

def post_request(client, data, access_key=Config.SECRET_KEY):
    """
    Helper function to make a POST request to the get_relevant_embeddings endpoint.
    """
    headers = {'Access-Key': access_key}
    with patch('main.check_access_key') as mock_check_access_key:
        mock_check_access_key.return_value = (access_key == Config.SECRET_KEY)
        return client.post('/get_relevant_embeddings', json=data, headers=headers)

def test_get_relevant_embeddings_no_question(client):
    response = post_request(client, {'embedding': [0.1, 0.2, 0.3]})
    json_data = response.get_json()
    assert response.status_code == 400
    assert json_data['error'] == 'No question provided'

def test_get_relevant_embeddings_no_embedding(client):
    response = post_request(client, {'question': 'What are the best movies?'})
    json_data = response.get_json()
    assert response.status_code == 400
    assert json_data['error'] == 'No embedding provided'

def test_get_relevant_embeddings_unauthorized(client):
    response = post_request(client, {'question': 'What are the best movies?'}, access_key='wrong_key')
    json_data = response.get_json()
    assert response.status_code == 403
    assert json_data['error'] == 'Unauthorized access'

def test_get_relevant_embeddings_success(client):
    with patch('main.get_relevant_movies') as mock_get_relevant_movies:
        mock_get_relevant_movies.return_value = [{'title': 'Movie 1', 'plot': 'Plot 1', 'image': 'Image 1', 'similarity': 0.9}]
        data = {'question': 'What are the best movies?', 'embedding': [0.1, 0.2, 0.3]}
        response = post_request(client, data)
        json_data = response.get_json()
        assert response.status_code == 200
        assert json_data['question'] == 'What are the best movies?'
        assert json_data['relevant_movies'] == [{'title': 'Movie 1', 'plot': 'Plot 1', 'image': 'Image 1', 'similarity': 0.9}]

def test_index_route(client):
    """
    Verifica la ruta principal y las configuraciones de cookies.
    """
    response = client.get('/')
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data['message'] == "Welcome to the get_relevant_embeddings API!"
    assert 'csrf_token' in response.headers.get('Set-Cookie')
    assert 'HttpOnly' in response.headers.get('Set-Cookie')
    assert 'Secure' in response.headers.get('Set-Cookie')

def test_run_app(monkeypatch):
    """
    Verifica la configuración del servidor para asegurar que se utiliza la configuración correcta.
    """
    def mock_run(*args, **kwargs):
        assert kwargs['host'] == '0.0.0.0'
        assert kwargs['port'] == 5004

    monkeypatch.setattr("main.app.run", mock_run)
    original_env = Config.FLASK_ENV
    Config.FLASK_ENV = 'development'
    try:
        run_app()
    finally:
        Config.FLASK_ENV = original_env


class RetrievalServiceTests(unittest.TestCase):

    @patch('app.retrieval_service.psycopg2.connect')
    def test_get_relevant_movies_success(self, mock_connect):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        mock_cur.fetchall.return_value = [
            ('Movie 1', 'Plot 1', 'Image 1', 0.9),
            ('Movie 2', 'Plot 2', 'Image 2', 0.8)
        ]

        query_embedding = [0.1, 0.2, 0.3]
        result = get_relevant_movies(query_embedding)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['title'], 'Movie 1')
        self.assertEqual(result[0]['similarity'], 0.9)

    @patch('app.retrieval_service.psycopg2.connect')
    def test_get_relevant_movies_exception(self, mock_connect):
        mock_connect.side_effect = Exception("Database connection failed")
        query_embedding = [0.1, 0.2, 0.3]
        result = get_relevant_movies(query_embedding)
        self.assertEqual(result, [])

if __name__ == "__main__":
    unittest.main()

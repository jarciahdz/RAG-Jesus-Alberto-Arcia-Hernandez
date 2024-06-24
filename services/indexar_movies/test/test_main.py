import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, json, request

# Ajustar el sys.path para incluir el directorio de servicios
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

from main import app, check_access_key
from index_embeddings import get_embeddings, index_embeddings, normalize_l2
from s3_file_manager import bucket_exists, create_bucket, calculate_md5, get_s3_md5, upload_to_s3, read_from_s3
import pandas as pd
from botocore.exceptions import ClientError
from app.config import Config

class MainAppTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.headers = {'Access-Key': 'correct_key'}  # Asegúrate de que esto coincida con Config.SECRET_KEY

    def test_index(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['message'], 'Welcome to the index and upload API!')

    def test_check_access_key_invalid(self):
        with app.test_request_context(headers={'Access-Key': 'wrong_key'}):
            self.assertFalse(check_access_key(request))

class IndexEmbeddingsTestCase(unittest.TestCase):

    @patch('index_embeddings.requests.post')
    def test_get_embeddings(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
        embeddings = get_embeddings(["test text"])
        self.assertEqual(len(embeddings), 1)
        self.assertEqual(embeddings[0], [0.1, 0.2, 0.3])

    def test_normalize_l2(self):
        vector = [1, 2, 2]
        normalized_vector = normalize_l2(vector)
        self.assertAlmostEqual(sum([x**2 for x in normalized_vector]), 1.0)

    @patch('index_embeddings.read_from_s3')
    @patch('index_embeddings.psycopg2.connect')
    @patch('index_embeddings.get_embeddings')
    def test_index_embeddings(self, mock_get_embeddings, mock_connect, mock_read_from_s3):
        mock_read_from_s3.return_value = pd.DataFrame({
            'title': ['Test title'],
            'plot': ['Test plot'],
            'image': ['Test image']
        })
        mock_get_embeddings.return_value = [[0.1, 0.2, 0.3]]
        mock_conn = mock_connect.return_value
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.mogrify.side_effect = lambda sql, args: b";".join([sql.encode()] * len(args))
        index_embeddings('test_bucket', 'test_key')
        mock_cursor.execute.assert_called()


class S3FileManagerTestCase(unittest.TestCase):

    @patch('s3_file_manager.boto3.client')
    def test_bucket_exists(self, mock_boto3_client):
        mock_s3 = mock_boto3_client.return_value
        mock_s3.head_bucket.return_value = {}
        self.assertTrue(bucket_exists('test_bucket'))

    @patch('s3_file_manager.boto3.client')
    def test_get_s3_md5(self, mock_boto3_client):
        mock_s3 = mock_boto3_client.return_value
        mock_s3.head_object.return_value = {'ETag': '"testetag"'}
        self.assertEqual(get_s3_md5('test_bucket', 'test_key'), 'testetag')

    @patch('s3_file_manager.boto3.client')
    def test_upload_to_s3(self, mock_boto3_client):
        mock_s3 = mock_boto3_client.return_value
        with patch('builtins.open', unittest.mock.mock_open(read_data=b'test data')):
            upload_to_s3('test_path', 'test_bucket', 'test_key')
            mock_s3.upload_file.assert_called()

    @patch('s3_file_manager.boto3.client')
    def test_read_from_s3(self, mock_boto3_client):
        mock_s3 = mock_boto3_client.return_value
        mock_s3.get_object.return_value = {'Body': MagicMock(read=lambda: b'title,plot,image\nTest title,Test plot,Test image')}
        df = read_from_s3('test_bucket', 'test_key')
        self.assertEqual(df['title'][0], 'Test title')

def process_batch(batch):
    try:
        combined_texts = [f"{row['title']}. {row['plot']}. {row['image']}" for _, row in batch.iterrows()]
        titles = [row['title'] for _, row in batch.iterrows()]
        plots = [row['plot'] for _, row in batch.iterrows()]
        images = [row['image'] for _, row in batch.iterrows()]
        
        embeddings = get_embeddings(combined_texts)
        normalized_embeddings = [normalize_l2(embedding) for embedding in embeddings]
        
        return [(title, plot, image, embedding.tolist()) for title, plot, image, embedding in zip(titles, plots, images, normalized_embeddings)]
    except ValueError as ve:
        print(f"ValueError processing batch: {ve}")
        raise ve  # Re-lanzar la excepción para que pueda ser cubierta por las pruebas
    except Exception as e:
        print(f"Error processing batch: {e}")
        return []



if __name__ == '__main__':
    unittest.main()

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
import psycopg2
import psycopg2.extras
import requests
import urllib3

from app.config import Config
from app.s3_file_manager import read_from_s3

# Deshabilitar advertencias de solicitudes inseguras (no recomendado para producción)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Inicializar cliente de OpenAI
api_key = Config.OPENAI_API_KEY
if not api_key:
    raise ValueError("API key not found. Please set the 'OPENAI_API_KEY' environment variable.")

def get_embeddings(texts, model=Config.OPENAI_MODEL, retries=5):
    """
    Obtiene las embeddings de los textos dados utilizando el modelo de OpenAI.

    Args:
        texts (list): Lista de textos para obtener las embeddings.
        model (str): Modelo de OpenAI a utilizar.
        retries (int): Número de intentos de reintento en caso de fallo.

    Returns:
        list: Lista de embeddings obtenidas.
    """
    url = "https://api.openai.com/v1/embeddings"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "input": texts,
        "model": model
    }

    for attempt in range(retries):
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            embeddings = response.json()["data"]
            return [embedding["embedding"] for embedding in embeddings]
        elif response.status_code == 429:
            wait_time = 10 ** attempt
            print(f"HTTP 429 Too Many Requests - waiting {wait_time} seconds before retrying...")
            time.sleep(wait_time)
        else:
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print(f"HTTP error: {e}")
                return []

    return []

def normalize_l2(x):
    """
    Normaliza un vector usando la norma L2.

    Args:
        x (numpy.ndarray): Vector a normalizar.

    Returns:
        numpy.ndarray: Vector normalizado.
    """
    x = np.array(x)
    norm = np.linalg.norm(x)
    return x if norm == 0 else x / norm

def index_embeddings(bucket_name, s3_file_key):
    """
    Función principal para indexar embeddings de películas.

    Args:
        bucket_name (str): Nombre del bucket en S3.
        s3_file_key (str): Clave del archivo en S3.
    """
    movies_df = read_from_s3(bucket_name, s3_file_key)
    movies_df = movies_df.dropna(subset=['title', 'plot', 'image'])

    conn = psycopg2.connect(
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        host=Config.DB_HOST,
        port=Config.DB_PORT
    )
    cur = conn.cursor()
    conn.autocommit = True
    
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS movie_embeddings (
        id SERIAL PRIMARY KEY,
        title TEXT,
        plot TEXT,
        image TEXT,
        embedding VECTOR(1536)
    )
    """)
    cur.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relname = 'idx_embedding' AND n.nspname = 'public'
        ) THEN
            CREATE INDEX idx_embedding ON movie_embeddings USING ivfflat (embedding);
        END IF;
    END
    $$;
    """)

    def process_batch(batch):
        try:
            combined_texts = [f"{row['title']}. {row['plot']}. {row['image']}" for _, row in batch.iterrows()]
            titles = [row['title'] for _, row in batch.iterrows()]
            plots = [row['plot'] for _, row in batch.iterrows()]
            images = [row['image'] for _, row in batch.iterrows()]
            
            embeddings = get_embeddings(combined_texts)
            normalized_embeddings = [normalize_l2(embedding) for embedding in embeddings]
            
            return [(title, plot, image, embedding.tolist()) for title, plot, image, embedding in zip(titles, plots, images, normalized_embeddings)]
        except Exception as e:
            print(f"Error processing batch: {e}")
            return []

    batch_size = 100
    batches = [movies_df[i:i + batch_size] for i in range(0, len(movies_df), batch_size)]

    data_a_insertar = []
    processed_batches = 0
    total_batches = len(batches)

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_batch = {executor.submit(process_batch, batch): batch for batch in batches}
        for future in as_completed(future_to_batch):
            try:
                result = future.result()
                if result:
                    data_a_insertar.extend(result)
                    processed_batches += 1
                    print(f"Processed batch {processed_batches}/{total_batches}")
            except Exception as exc:
                print(f"Batch processing generated an exception: {exc}")

    query = """
    INSERT INTO movie_embeddings (title, plot, image, embedding)
    VALUES (%s, %s, %s, %s)
    """
    psycopg2.extras.execute_batch(cur, query, data_a_insertar)

    cur.close()
    conn.close()

    print(f"Indexación completada. Total de registros procesados: {len(data_a_insertar)}")
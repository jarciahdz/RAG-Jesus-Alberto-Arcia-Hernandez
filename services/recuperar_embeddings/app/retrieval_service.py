import psycopg2
import numpy as np
from config import Config

# Constantes para la configuración de la base de datos
DB_CONFIG = {
    'dbname': Config.DB_NAME,
    'user': Config.DB_USER,
    'password': Config.DB_PASSWORD,
    'host': Config.DB_HOST,
    'port': Config.DB_PORT
}

# Consultas SQL
SQL_QUERY_RELEVANT_MOVIES = """
    SELECT title, plot, image, embedding <#> %s::vector AS similarity 
    FROM movie_embeddings 
    ORDER BY similarity ASC 
    LIMIT %s
"""

def get_relevant_movies(query_embedding, limit=5):
    """
    Obtiene las películas más relevantes basadas en el embedding de consulta utilizando PGVector.
    
    Args:
    query_embedding (list): Embedding de la consulta.
    limit (int): Número máximo de películas relevantes a retornar. Por defecto es 5.
    
    Returns:
    list: Lista de diccionarios con las películas relevantes.
    """
    query_embedding = np.array(query_embedding, dtype=np.float32).tolist()
    conn = None
    cur = None
    try:
        # Conexión a la base de datos
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        # Convertir el embedding en una cadena con el formato adecuado para PGVector
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        # Ejecutar consulta SQL utilizando PGVector para búsqueda de similitud
        cur.execute(SQL_QUERY_RELEVANT_MOVIES, (embedding_str, limit))
        results = cur.fetchall()
        # Construir la lista de películas relevantes
        relevant_movies = [
            {"title": title, "plot": plot, "image": image, "similarity": float(similarity)}
            for title, plot, image, similarity in results
        ]
        return relevant_movies
    except Exception as e:
        print(f"Error al obtener los embeddings: {e}")
        return []
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

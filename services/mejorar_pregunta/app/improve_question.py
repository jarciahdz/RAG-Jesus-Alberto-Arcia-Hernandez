import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import openai
from app.config import Config

def mejorar_pregunta(pregunta):
    """
    Utiliza la API de OpenAI para corregir errores ortográficos y completar palabras faltantes.

    Args:
    pregunta (str): La pregunta del usuario.

    Returns:
    str: La pregunta mejorada.

    Raises:
    ValueError: Si la pregunta está vacía.
    RuntimeError: Si hay un error al llamar a la API de OpenAI.
    """
    if not pregunta:
        raise ValueError("La pregunta no puede estar vacía")
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"Please review and improve the following question. Correct any spelling and grammatical errors, and complete any missing words or phrases to ensure it is clear and well-structured. Make sure the response is accurate and directly related to the question without adding any unnecessary information: {pregunta}"}
    ]
    
    response = openai.ChatCompletion.create(
        model=Config.MODEL,
        messages=messages,
        max_tokens=150
    )
    
    mejora = response.choices[0].message['content'].strip()
    return mejora
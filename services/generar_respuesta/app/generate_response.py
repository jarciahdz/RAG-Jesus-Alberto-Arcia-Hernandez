def construir_contexto(question, relevant_movies):
    """
    Construye el contexto necesario para la generación de la respuesta basada en la pregunta y las películas relevantes.

    Args:
    question (str): La pregunta proporcionada por el usuario.
    relevant_movies (list): Lista de películas relevantes con sus detalles.

    Returns:
    str: Contexto formateado listo para ser utilizado en la generación de la respuesta.
    """
    context = f"Pregunta: {question}\n\n"
    context += "Contexto:\n"
    for movie in relevant_movies:
        context += f"Similarity: {movie['similarity']}\n"
        context += f"Title: {movie['title']}\n"
        context += f"Plot: {movie['plot']}\n"
        context += f"Image: {movie['image']}\n\n"
    context += "Respuesta:"
    return context

# Microservicio de Recuperación de Embeddings

## Descripción

Este microservicio utiliza embeddings de texto para obtener películas relevantes basadas en la consulta proporcionada por el usuario. La aplicación está construida utilizando Flask y puede ser desplegada en Docker.

## Estructura del Proyecto

```
.
├── Dockerfile
├── README.md
├── app
│   ├── __init__.py
│   ├── __pycache__
│   ├── config.py
│   ├── main.py
│   └── retrieval_service.py
├── requirements.txt
└── test
    ├── __pycache__
    └── test_main.py
```

## Requisitos

- Python 3.12 o superior
- Docker (opcional, para despliegue en contenedores)
- Configuración de la base de datos PostgreSQL con PGVector

## Configuración

1. Clona el repositorio:
    ```bash
    git clone https://github.com/tu_usuario/recuperar_embeddings.git
    cd recuperar_embeddings
    ```

2. Crea un entorno virtual e instala las dependencias:
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows usa `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3. Crea un archivo `.env` en el directorio raíz del proyecto y añade las siguientes variables:
    ```
    DB_NAME=your_db_name
    DB_USER=your_db_user
    DB_PASSWORD=your_db_password
    DB_HOST=your_db_host
    DB_PORT=your_db_port
    SECRET_KEY=your_secret_key
    TRUSTDOMAIN_4=http://localhost:3000
    ```

## Uso

### Ejecución Local

1. Ejecuta la aplicación:
    ```bash
    python app/main.py
    ```

2. La API estará disponible en `http://localhost:5004`.

### Endpoints

- **`POST /get_relevant_embeddings`**
  - **Descripción:** Obtiene películas relevantes basadas en el embedding proporcionado.
  - **Headers:**
    - `Access-Key`: Clave de acceso para autenticación.
  - **Body (JSON):**
    ```json
    {
      "question": "Tu pregunta aquí",
      "embedding": [vector de embedding]
    }
    ```
  - **Respuesta Exitosa (200):**
    ```json
    {
      "question": "Tu pregunta aquí",
      "relevant_movies": [
        {"title": "Movie 1", "plot": "Plot 1", "image": "Image 1", "similarity": 0.9},
        ...
      ]
    }
    ```
  - **Errores:**
    - `403 Unauthorized access`: Si la clave de acceso no es válida.
    - `400 No question provided`: Si no se proporciona una pregunta.
    - `400 No embedding provided`: Si no se proporciona un embedding.

### Pruebas

1. Para ejecutar las pruebas, asegúrate de que el entorno virtual esté activado y luego ejecuta:
    ```bash
    pytest
    ```

## Despliegue con Docker

1. Construye la imagen de Docker:
    ```bash
    docker build -t recuperar_embeddings .
    # En mac usa: docker buildx build --platform linux/amd64 -t recuperar_embeddings
    ```

2. Ejecuta el contenedor:
    ```bash
    docker run -p 5004:5004 --env-file .env recuperar_embeddings
    ```

## Estructura de los Archivos

- **`app/config.py`**: Configuración de variables de entorno.
- **`app/retrieval_service.py`**: Lógica para obtener embeddings relevantes de la base de datos.
- **`app/main.py`**: Configuración y rutas del servidor Flask.
- **`test/test_main.py`**: Pruebas unitarias e integradas para el microservicio.

## Dockerfile

### Descripción del Dockerfile

El `Dockerfile` proporciona las instrucciones necesarias para construir una imagen de Docker para el microservicio. A continuación se describe el contenido del archivo:

- **Base Image**: Utiliza una imagen base ligera de Python (`python:3.10-slim`).
- **User Setup**: Crea un usuario no privilegiado para ejecutar la aplicación.
- **Working Directory**: Establece el directorio de trabajo en `/app`.
- **Requirements**: Copia el archivo `requirements.txt` y instala las dependencias.
- **Copy Application**: Copia el resto de la aplicación al contenedor.
- **Permissions**: Cambia la propiedad del directorio de trabajo al usuario no privilegiado.
- **User Switch**: Cambia al usuario no privilegiado.
- **Expose Port**: Expone el puerto `5004` para la aplicación.
- **Default Command**: Define el comando por defecto para ejecutar la aplicación.

```dockerfile
# Usar una imagen base de Python ligera y segura
FROM python:3.10-slim

# Crear un usuario no privilegiado
RUN useradd -m -s /bin/bash chucho111

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar el archivo de requerimientos al contenedor
COPY requirements.txt .

# Actualizar pip e instalar las dependencias, usando cacheo de capas de Docker
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el resto de la aplicación al contenedor
COPY app /app/app

# Cambiar la propiedad de /app al usuario no privilegiado
RUN chown -R chucho111:chucho111 /app

# Cambiar al usuario no privilegiado
USER chucho111

# Exponer el puerto 5004 para la aplicación
EXPOSE 5004

# Definir el comando por defecto para ejecutar la aplicación
CMD ["python", "app/main.py"]
```

## Pruebas Unitarias

Las pruebas unitarias se encuentran en el archivo `test/test_main.py` y cubren diversos aspectos del microservicio. A continuación, se describen las pruebas más importantes:

### Fixture para Configurar la Aplicación de Pruebas

- **`client`**: Configura la aplicación Flask para pruebas y proporciona un cliente de pruebas.

### Pruebas de Validación de Clave de Acceso

- **`test_check_access_key_valid`**: Verifica que la clave de acceso se valida correctamente cuando es válida.
- **`test_check_access_key_invalid`**: Verifica que la clave de acceso no se valida cuando es inválida.

### Pruebas del Endpoint `/get_relevant_embeddings`

- **`test_get_relevant_embeddings_no_question`**: Verifica que se devuelve un error `400` cuando no se proporciona una pregunta en la solicitud.
  - **Descripción**: Esta prueba asegura que la API maneja correctamente las solicitudes que no incluyen una pregunta, devolviendo el error apropiado.

- **`test_get_relevant_embeddings_no_embedding`**: Verifica que se devuelve un error `400` cuando no se proporciona un embedding en la solicitud.
  - **Descripción**: Esta prueba asegura que la API maneja correctamente las solicitudes que no incluyen un embedding, devolviendo el error apropiado.

- **`test_get_relevant_embeddings_unauthorized`**: Verifica que se devuelve un error `403` cuando la clave de acceso es inválida.
  - **Descripción**: Esta prueba asegura que la API maneja correctamente las solicitudes con claves de acceso inválidas, devolviendo el error apropiado.

- **`test_get_relevant_embeddings_success`**: Simula una solicitud exitosa al endpoint `/get_relevant_embeddings` utilizando un mock para la función `get_relevant_movies`.
  - **Descripción**: Esta prueba asegura que una solicitud válida es procesada correctamente por el endpoint y que se obtiene la respuesta esperada.

### Pruebas de la Función `get_relevant_movies`

- **`test_get_relevant_movies_success`**: Verifica que se obtienen las películas relevantes correctamente.
  - **Mock**: Se utiliza un mock para simular la conexión a la base de datos y los resultados de la consulta.

- **`test_get_relevant_movies_exception`**: Verifica el manejo de excepciones cuando hay un error en la conexión a la base de datos.
  - **Descripción**: Esta prueba asegura que la función `get_relevant_movies` maneja correctamente las excepciones y devuelve una lista vacía en caso de error.

### Prueba de la Ruta Principal

- **`test_index_route`**: Verifica la ruta principal y las configuraciones de cookies.
  - **Descripción**: Esta prueba asegura que la ruta principal `/` responde correctamente y configura las cookies adecuadamente, incluyendo el token CSRF.

### Prueba de Configuración del Servidor

- **`test_run_app`**: Verifica la configuración del servidor para asegurar que se utiliza la configuración correcta.
  - **Descripción**: Esta prueba asegura que el servidor Flask se configura correctamente para ejecutarse en el host `0.0.0.0` y en el puerto `5004`.

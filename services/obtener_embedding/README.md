# Microservicio de Obtención de Embeddings

## Descripción

Este microservicio utiliza la API de OpenAI para obtener embeddings de texto proporcionado por el usuario. La aplicación está construida utilizando Flask y puede ser desplegada en Docker.

## Estructura del Proyecto

```
.
├── Dockerfile
├── README.md
├── app
│   ├── __init__.py
│   ├── __pycache__
│   ├── config.py
│   ├── embedding_service.py
│   └── main.py
├── requirements.txt
└── test
    ├── __pycache__
    └── test_main.py
```

## Requisitos

- Python 3.12 o superior
- Docker (opcional, para despliegue en contenedores)
- OpenAI API Key

## Configuración

1. Clona el repositorio:
    ```bash
    git clone https://github.com/tu_usuario/obtener_embedding.git
    cd obtener_embedding
    ```

2. Crea un entorno virtual e instala las dependencias:
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows usa `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3. Crea un archivo `.env` en el directorio raíz del proyecto y añade las siguientes variables:
    ```
    OPENAI_API_KEY=your_openai_api_key
    MODEL=text-embedding-ada-002
    ACCESS_KEY=your_access_key
    ```

## Uso

### Ejecución Local

1. Ejecuta la aplicación:
    ```bash
    python app/main.py
    ```

2. La API estará disponible en `http://localhost:5002`.

### Endpoint

- **`POST /get_embedding`**
  - **Descripción:** Obtiene el embedding de un texto proporcionado.
  - **Headers:**
    - `Access-Key`: Clave de acceso para autenticación.
  - **Body (JSON):**
    ```json
    {
      "question": "Tu pregunta aquí"
    }
    ```
  - **Respuesta Exitosa (200):**
    ```json
    {
      "question": "Tu pregunta aquí",
      "embedding": [vector de embedding]
    }
    ```
  - **Errores:**
    - `403 Unauthorized access`: Si la clave de acceso no es válida.
    - `400 No question provided`: Si no se proporciona una pregunta.
    - `500 OpenAI API error`: Si ocurre un error con la API de OpenAI.

### Pruebas

1. Para ejecutar las pruebas, asegúrate de que el entorno virtual esté activado y luego ejecuta:
    ```bash
    pytest
    ```

## Despliegue con Docker

1. Construye la imagen de Docker:
    ```bash
    docker build -t obtener_embedding .
    # En mac usa: docker buildx build --platform linux/amd64 -t obtener_embedding
    ```

2. Ejecuta el contenedor:
    ```bash
    docker run -p 5002:5002 --env-file .env obtener_embedding
    ```

## Estructura de los Archivos

- **`app/config.py`**: Configuración de variables de entorno.
- **`app/embedding_service.py`**: Lógica para obtener embeddings utilizando la API de OpenAI.
- **`app/main.py`**: Configuración y rutas del servidor Flask.
- **`test/test_main.py`**: Pruebas unitarias e integradas para el microservicio.

## Pruebas Unitarias

Las pruebas unitarias se encuentran en el archivo `test/test_main.py` y cubren diversos aspectos del microservicio. A continuación, se describen las pruebas más importantes:

### Fixture para Configurar la Aplicación de Pruebas

- **`client`**: Configura la aplicación Flask para pruebas y proporciona un cliente de pruebas.

### Pruebas de Validación de Clave de Acceso

- **`test_check_access_key_valid`**: Verifica que la clave de acceso se valida correctamente cuando es válida.
- **`test_check_access_key_invalid`**: Verifica que la clave de acceso no se valida cuando es inválida.

### Pruebas del Endpoint `/get_embedding`

- **`test_get_embedding_route_no_question`**: Verifica que se devuelve un error `400` cuando no se proporciona una pregunta en la solicitud.
  - **Descripción**: Esta prueba asegura que la API maneja correctamente las solicitudes que no incluyen una pregunta, devolviendo el error apropiado.

- **`test_get_embedding_route_unauthorized`**: Verifica que se devuelve un error `403` cuando la clave de acceso es inválida.
  - **Descripción**: Esta prueba asegura que la API maneja correctamente las solicitudes con claves de acceso inválidas, devolviendo el error apropiado.

- **`test_get_embedding_route_success`**: Simula una solicitud exitosa al endpoint `/get_embedding` utilizando un monkeypatch para la API de OpenAI.
  - **Descripción**: Esta prueba asegura que un texto válido es procesado correctamente por el endpoint y que se obtiene la respuesta esperada.
  - **Mock**: Se utiliza `monkeypatch` para simular la respuesta de la API de OpenAI.

- **`test_get_embedding_route_value_error`**: Verifica que se devuelve un error `400` cuando la función `get_embedding` lanza un `ValueError`.
  - **Descripción**: Esta prueba asegura que la API maneja correctamente las excepciones lanzadas por `get_embedding`, devolviendo el error apropiado.

- **`test_get_embedding_route_runtime_error`**: Simula un error de la API de OpenAI y verifica que se devuelve un error `500`.
  - **Descripción**: Esta prueba asegura que la API maneja correctamente los errores de la API de OpenAI, devolviendo el error apropiado.
  - **Mock**: Se utiliza `monkeypatch` para simular un error de la API de OpenAI.

### Pruebas de Funciones Internas

- **`test_get_embedding_vacia`**: Verifica que se lanza un `ValueError` cuando el texto está vacío.
  - **Descripción**: Esta prueba asegura que la función `get_embedding` maneja correctamente las entradas vacías, lanzando una excepción apropiada.

- **`test_get_embedding_success`**: Verifica que se obtiene el embedding correctamente cuando el texto y la API key son válidos.
  - **Mock**: Se utiliza `patch` para simular una respuesta exitosa de la API de OpenAI.

- **`test_get_embedding_empty_text`**: Verifica que se lanza un `ValueError` cuando el texto está vacío.
  - **Descripción**: Esta prueba asegura que la función `get_embedding` maneja correctamente las entradas vacías, lanzando una excepción apropiada.

- **`test_get_embedding_ssl_error`**: Verifica que se lanza un `requests.exceptions.SSLError` cuando hay un error SSL en la solicitud a la API de OpenAI.
  - **Mock**: Se utiliza `patch` para simular un error SSL en la solicitud.

- **`test_get_embedding_request_exception`**: Verifica que se lanza un `RuntimeError` cuando hay un error de solicitud en la API de OpenAI.
  - **Mock**: Se utiliza `patch` para simular un error de solicitud en la API de OpenAI.

### Prueba de Configuración del Servidor

- **`test_run_app`**: Verifica la configuración del servidor para asegurar que se utiliza la configuración correcta.
  - **Descripción**: Esta prueba asegura que el servidor Flask se configura correctamente para ejecutarse en el host `0.0.0.0` y en el puerto `5002`.

### Prueba de la Ruta Principal

- **`test_index_route`**: Verifica la ruta principal y las configuraciones de cookies.
  - **Descripción**: Esta prueba asegura que la ruta principal `/` responde correctamente y configura las cookies adecuadamente, incluyendo el token CSRF.



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
- **Expose Port**: Expone el puerto `5002` para la aplicación.
- **Default Command**: Define el comando por defecto para ejecutar la aplicación.

```Dockerfile
# Usar una imagen base de Python ligera
FROM python:3.10-slim

# Crear un usuario no privilegiado
RUN useradd -m chucho111

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar el archivo de requerimientos al contenedor
COPY requirements.txt requirements.txt

# Actualizar pip y instalar las dependencias
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar el resto de la aplicación al contenedor
COPY app app

# Cambiar la propiedad de /app al usuario no privilegiado
RUN chown -R chucho111:chucho111 /app

# Cambiar al usuario no privilegiado
USER chucho111

# Exponer el puerto 5002 para la aplicación
EXPOSE 5002

# Definir el comando por defecto para ejecutar la aplicación
CMD ["python", "app/main.py"]

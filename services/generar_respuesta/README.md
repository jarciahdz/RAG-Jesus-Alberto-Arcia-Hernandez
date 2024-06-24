# Microservicio de Generación de Respuestas

## Descripción

Este microservicio utiliza la API de OpenAI para generar respuestas basadas en preguntas y un contexto proporcionado por el usuario. La aplicación está construida utilizando Flask y puede ser desplegada en Docker.

## Estructura del Proyecto

```
.
├── Dockerfile
├── README.md
├── app
│   ├── __init__.py
│   ├── __pycache__
│   ├── config.py
│   ├── generate_response.py
│   └── main.py
├── requirements.txt
└── test
    └── test_main.py
```

## Requisitos

- Python 3.12 o superior
- Docker (opcional, para despliegue en contenedores)
- OpenAI API Key

## Configuración

1. Clona el repositorio:
    ```bash
    git clone https://github.com/tu_usuario/generar_respuesta.git
    cd generar_respuesta
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
    SECRET_KEY=your_secret_key
    TRUSTDOMAIN_5=http://localhost:5005
    ```

## Uso

### Ejecución Local

1. Ejecuta la aplicación:
    ```bash
    python app/main.py
    ```

2. La API estará disponible en `http://localhost:5005`.

### Endpoint

- **`POST /ask`**
  - **Descripción:** Genera una respuesta basada en la pregunta y el contexto proporcionado.
  - **Headers:**
    - `Access-Key`: Clave de acceso para autenticación.
  - **Body (JSON):**
    ```json
    {
      "question": "Tu pregunta aquí",
      "relevant_movies": [
        {
          "similarity": 0.9,
          "title": "Movie 1",
          "plot": "Plot 1",
          "image": "Image 1"
        },
        ...
      ]
    }
    ```
  - **Respuesta Exitosa (200):**
    ```json
    {
      "answer": "La respuesta generada"
    }
    ```
  - **Errores:**
    - `403 Unauthorized access`: Si la clave de acceso no es válida.
    - `400 Missing question or relevant_movies`: Si no se proporciona una pregunta o las películas relevantes.

### Pruebas

1. Para ejecutar las pruebas, asegúrate de que el entorno virtual esté activado y luego ejecuta:
    ```bash
    pytest
    ```

## Despliegue con Docker

1. Construye la imagen de Docker:
    ```bash
    docker build -t generar_respuesta .
    # En mac usa: docker buildx build --platform linux/amd64 -t generar_respuesta
    ```

2. Ejecuta el contenedor:
    ```bash
    docker run -p 5005:5005 --env-file .env generar_respuesta
    ```

## Estructura de los Archivos

- **`app/config.py`**: Configuración de variables de entorno.
- **`app/generate_response.py`**: Lógica para construir el contexto necesario para la generación de respuestas.
- **`app/main.py`**: Configuración y rutas del servidor Flask.
- **`test/test_main.py`**: Pruebas unitarias e integradas para el microservicio.

## Pruebas Unitarias

Las pruebas unitarias se encuentran en el archivo `test/test_main.py` y cubren diversos aspectos del microservicio. A continuación, se describen las pruebas más importantes:

### Fixture para Configurar la Aplicación de Pruebas

La fixture `client` configura la aplicación Flask para pruebas y proporciona un cliente de pruebas.

### Pruebas de Validación de Clave de Acceso

Las pruebas `test_check_access_key_valid` y `test_check_access_key_invalid` verifican que la clave de acceso se valida correctamente cuando es válida e inválida, respectivamente.

### Pruebas para la Función `construir_contexto`

La prueba `test_construir_contexto` asegura que la función `construir_contexto` genera el contexto correcto basado en la pregunta y las películas relevantes proporcionadas.

### Pruebas del Endpoint `/ask`

- **`test_index_route`**: Verifica que la ruta principal responde correctamente con un mensaje de bienvenida y configura las cookies adecuadamente.
- **`test_make_openai_request_success`**: Simula una solicitud exitosa a la API de OpenAI.
- **`test_make_openai_request_retry`**: Verifica el comportamiento de reintento de solicitudes en caso de recibir un error 429 (Too Many Requests).
- **`test_make_openai_request_failure`**: Verifica que se manejen correctamente los errores de la API de OpenAI.

### Prueba de Configuración del Servidor

La prueba `test_run_app` verifica que el servidor Flask se configura correctamente para ejecutarse en el host `0.0.0.0` y en el puerto `5005`.

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
- **Expose Port**: Expone el puerto `5005` para la aplicación.
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

# Exponer el puerto 5005 para la aplicación
EXPOSE 5005

# Definir el comando por defecto para ejecutar la aplicación
CMD ["python", "app/main.py"]

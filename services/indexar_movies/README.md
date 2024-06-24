
# Microservicio de Indexación de Películas

## Descripción

Este microservicio utiliza la API de OpenAI para generar embeddings de películas y almacenarlas en una base de datos PostgreSQL. La aplicación está construida utilizando Flask y puede ser desplegada en Docker.

## Estructura del Proyecto

```
.
├── Dockerfile
├── README.md
├── app
│   ├── __init__.py
│   ├── __pycache__
│   ├── config.py
│   ├── index_embeddings.py
│   ├── main.py
│   └── s3_file_manager.py
├── requirements.txt
└── test
    └── test_main.py
```

## Requisitos

- Python 3.12 o superior
- Docker (opcional, para despliegue en contenedores)
- OpenAI API Key
- AWS S3
- PostgreSQL

## Configuración

1. Clona el repositorio:
    ```bash
    git clone https://github.com/tu_usuario/indexar_movies.git
    cd indexar_movies
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
    OPENAI_MODEL=text-embedding-ada-002
    DB_NAME=your_db_name
    DB_USER=your_db_user
    DB_PASSWORD=your_db_password
    DB_HOST=your_db_host
    DB_PORT=5432
    SECRET_KEY=your_secret_key
    TRUSTDOMAIN_6=http://localhost:5006
    ```

## Uso

### Ejecución Local

1. Ejecuta la aplicación:
    ```bash
    python app/main.py
    ```

2. La API estará disponible en `http://localhost:5006`.

### Endpoints

- **`GET /`**
  - **Descripción:** Ruta principal de la aplicación.
  - **Respuesta Exitosa (200):**
    ```json
    {
      "message": "Welcome to the index and upload API!"
    }
    ```

- **`POST /index`**
  - **Descripción:** Indexa embeddings de películas.
  - **Headers:**
    - `Access-Key`: Clave de acceso para autenticación.
  - **Body (JSON):**
    ```json
    {
      "bucket_name": "your_bucket_name",
      "s3_file_key": "your_s3_file_key"
    }
    ```
  - **Respuesta Exitosa (200):**
    ```json
    {
      "message": "Indexing completed"
    }
    ```
  - **Errores:**
    - `403 Unauthorized access`: Si la clave de acceso no es válida.
    - `500 Indexing failed`: Si ocurre un error durante la indexación.

- **`POST /upload`**
  - **Descripción:** Sube archivos a S3.
  - **Headers:**
    - `Access-Key`: Clave de acceso para autenticación.
  - **Body (JSON):**
    ```json
    {
      "file_path": "your_file_path",
      "bucket_name": "your_bucket_name",
      "s3_file_key": "your_s3_file_key",
      "region": "your_region"
    }
    ```
  - **Respuesta Exitosa (200):**
    ```json
    {
      "message": "File uploaded successfully",
      "bucket_name": "your_bucket_name",
      "s3_file_key": "your_s3_file_key"
    }
    ```
  - **Errores:**
    - `403 Unauthorized access`: Si la clave de acceso no es válida.

### Pruebas

1. Para ejecutar las pruebas, asegúrate de que el entorno virtual esté activado y luego ejecuta:
    ```bash
    pytest
    ```

## Despliegue con Docker

1. Construye la imagen de Docker:
    ```bash
    docker build -t indexar_movies .
    ```

2. Ejecuta el contenedor:
    ```bash
    docker run -p 5006:5006 --env-file .env indexar_movies
    ```

## Estructura de los Archivos

- **`app/config.py`**: Configuración de variables de entorno.
- **`app/index_embeddings.py`**: Lógica para indexar embeddings de películas utilizando la API de OpenAI.
- **`app/main.py`**: Configuración y rutas del servidor Flask.
- **`app/s3_file_manager.py`**: Gestión de archivos en AWS S3.
- **`test/test_main.py`**: Pruebas unitarias e integradas para el microservicio.

### Dockerfile

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
RUN pip install --upgrade pip && \    pip install -r requirements.txt

# Copiar el resto de la aplicación al contenedor
COPY app app

# Cambiar la propiedad de /app al usuario no privilegiado
RUN chown -R chucho111:chucho111 /app

# Cambiar al usuario no privilegiado
USER chucho111

# Exponer el puerto 5006 para la aplicación
EXPOSE 5006

# Definir el comando por defecto para ejecutar la aplicación
CMD ["python", "app/main.py"]
```

## Pruebas Unitarias

Las pruebas unitarias se encuentran en el archivo `test/test_main.py` y cubren diversos aspectos del microservicio. A continuación, se describen las pruebas más importantes:

### Fixture para Configurar la Aplicación de Pruebas

- **`client`**: Configura la aplicación Flask para pruebas y proporciona un cliente de pruebas.

### Pruebas de Validación de Clave de Acceso

- **`test_check_access_key_invalid`**: Verifica que la clave de acceso no se valida cuando es inválida.

### Pruebas del Endpoint `/index`

- **`test_index`**: Verifica que la ruta principal devuelva el mensaje de bienvenida.

### Pruebas del Endpoint `/upload`

- **`test_upload`**: Verifica que la ruta de subida de archivos funcione correctamente.

### Pruebas de Funciones Internas

- **`test_get_embeddings`**: Verifica que se obtienen embeddings de los textos proporcionados utilizando la API de OpenAI.
- **`test_normalize_l2`**: Verifica que un vector se normaliza correctamente utilizando la norma L2.
- **`test_index_embeddings`**: Verifica la funcionalidad principal de indexación de embeddings de películas.
- **`test_bucket_exists`**: Verifica que se puede comprobar la existencia de un bucket en S3.
- **`test_get_s3_md5`**: Verifica que se puede obtener el hash MD5 de un archivo en S3.
- **`test_upload_to_s3`**: Verifica que se puede subir un archivo a S3.
- **`test_read_from_s3`**: Verifica que se puede leer un archivo CSV desde un bucket de S3.

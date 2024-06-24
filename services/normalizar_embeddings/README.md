# Microservicio de Normalización de Embeddings

## Descripción

Este microservicio normaliza embeddings utilizando la norma L2. La aplicación está construida utilizando Flask y puede ser desplegada en Docker.

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
│   └── normalization_service.py
├── requirements.txt
└── test
    ├── __pycache__
    └── test_main.py
```

## Requisitos

- Python 3.12 o superior
- Docker (opcional, para despliegue en contenedores)

## Configuración

1. Clona el repositorio:
    ```bash
    git clone https://github.com/tu_usuario/normalizar_embeddings.git
    cd normalizar_embeddings
    ```

2. Crea un entorno virtual e instala las dependencias:
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows usa `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3. Crea un archivo `.env` en el directorio raíz del proyecto y añade las siguientes variables:
    ```
    SECRET_KEY=your_secret_key
    TRUSTDOMAIN_3=http://localhost:5003
    ```

## Uso

### Ejecución Local

1. Ejecuta la aplicación:
    ```bash
    python app/main.py
    ```

2. La API estará disponible en `http://localhost:5003`.

### Endpoint

- **`POST /normalize_embedding`**
  - **Descripción:** Normaliza un embedding proporcionado.
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
      "embedding": [vector normalizado]
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
    docker build -t normalizar_embeddings .
    ```

2. Ejecuta el contenedor:
    ```bash
    docker run -p 5003:5003 --env-file .env normalizar_embeddings
    ```

## Estructura de los Archivos

- **`app/config.py`**: Configuración de variables de entorno.
- **`app/normalization_service.py`**: Lógica para normalizar embeddings utilizando la norma L2.
- **`app/main.py`**: Configuración y rutas del servidor Flask.
- **`test/test_main.py`**: Pruebas unitarias e integradas para el microservicio.

## Pruebas Unitarias

Las pruebas unitarias se encuentran en el archivo `test/test_main.py` y cubren diversos aspectos del microservicio. A continuación, se describen las pruebas más importantes:

### Fixture para Configurar la Aplicación de Pruebas

- **`client`**: Configura la aplicación Flask para pruebas y proporciona un cliente de pruebas.

### Pruebas de Validación de Clave de Acceso

- **`test_check_access_key_valid`**: Verifica que la clave de acceso se valida correctamente cuando es válida.
- **`test_check_access_key_invalid`**: Verifica que la clave de acceso no se valida cuando es inválida.

### Pruebas del Endpoint `/normalize_embedding`

- **`test_normalize_embedding_route_success`**: Simula una solicitud exitosa al endpoint `/normalize_embedding`.
  - **Descripción**: Esta prueba asegura que un embedding válido es procesado correctamente por el endpoint y que se obtiene la respuesta esperada.
  - **Mock**: Se utiliza `monkeypatch` para simular la respuesta de la función de normalización.

- **`test_normalize_embedding_route_no_question`**: Verifica que se devuelve un error `400` cuando no se proporciona una pregunta en la solicitud.
  - **Descripción**: Esta prueba asegura que la API maneja correctamente las solicitudes que no incluyen una pregunta, devolviendo el error apropiado.

- **`test_normalize_embedding_route_no_embedding`**: Verifica que se devuelve un error `400` cuando no se proporciona un embedding en la solicitud.
  - **Descripción**: Esta prueba asegura que la API maneja correctamente las solicitudes que no incluyen un embedding, devolviendo el error apropiado.

- **`test_normalize_embedding_route_unauthorized`**: Verifica que se devuelve un error `403` cuando la clave de acceso es inválida.
  - **Descripción**: Esta prueba asegura que la API maneja correctamente las solicitudes con claves de acceso inválidas, devolviendo el error apropiado.

### Pruebas de Funciones Internas

- **`test_normalize_l2`**: Verifica que un vector se normaliza correctamente utilizando la norma L2.
  - **Descripción**: Esta prueba asegura que la función de normalización maneja correctamente los vectores de entrada.

### Prueba de la Ruta Principal

- **`test_index_route`**: Verifica la ruta principal y las configuraciones de cookies.
  - **Descripción**: Esta prueba asegura que la ruta principal `/` responde correctamente y configura las cookies adecuadamente, incluyendo el token CSRF.

### Prueba de Configuración del Servidor

- **`test_run_app`**: Verifica la configuración del servidor para asegurar que se utiliza la configuración correcta.
  - **Descripción**: Esta prueba asegura que el servidor Flask se configura correctamente para ejecutarse en el host `0.0.0.0` y en el puerto `5003`.

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
- **Expose Port**: Expone el puerto `5003` para la aplicación.
- **Default Command**: Define el comando por defecto para ejecutar la aplicación.

```Dockerfile
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

# Exponer el puerto 5003 para la aplicación
EXPOSE 5003

# Definir el comando por defecto para ejecutar la aplicación
CMD ["python", "app/main.py"]

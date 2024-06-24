import os
import boto3
import json
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env
load_dotenv()

def get_secret():
    secret_name = ".env"
    region_name = "us-east-1"

    # Crear un cliente de Secrets Manager
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except Exception as e:
        raise e

    # Desencripta el secreto usando la clave KMS asociada.
    secret = get_secret_value_response['SecretString']
    return json.loads(secret)

secrets = get_secret()

class Config:




import boto3
import pandas as pd
from io import StringIO
import hashlib
from botocore.exceptions import ClientError

def bucket_exists(bucket_name):
    """
    Verifica si un bucket existe en S3.

    Args:
        bucket_name (str): Nombre del bucket a verificar.

    Returns:
        bool: True si el bucket existe, False en caso contrario.
    """
    s3 = boto3.client('s3')
    try:
        s3.head_bucket(Bucket=bucket_name)
        return True
    except ClientError as e:
        print(f"Error checking if bucket exists: {e}")
        return False

def create_bucket(bucket_name, region=None):
    """
    Crea un bucket en S3 si no existe.

    Args:
        bucket_name (str): Nombre del bucket a crear.
        region (str, optional): Región donde crear el bucket. Por defecto es None.
    """
    if bucket_exists(bucket_name):
        print(f"El bucket {bucket_name} ya existe.")
        return
    
    try:
        s3_client = boto3.client('s3', region_name=region) if region else boto3.client('s3')
        create_bucket_configuration = {'LocationConstraint': region} if region else {}
        s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=create_bucket_configuration)
        print(f"Bucket {bucket_name} creado exitosamente")
    except ClientError as e:
        print(f"No se pudo crear el bucket: {e}")

def calculate_md5(file_path):
    """
    Calcula el hash MD5 de un archivo.

    Args:
        file_path (str): Ruta local del archivo.

    Returns:
        str: Hash MD5 del archivo.
    """
    hash_md5 = hashlib.sha512()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except IOError as e:
        print(f"Error calculating MD5 for file {file_path}: {e}")
        return None

def get_s3_md5(bucket_name, s3_file_key):
    """
    Obtiene el hash MD5 de un archivo en S3.

    Args:
        bucket_name (str): Nombre del bucket de S3.
        s3_file_key (str): Clave (ruta) en el bucket de S3.

    Returns:
        str: Hash MD5 del archivo en S3 o None si el archivo no existe.
    """
    s3_client = boto3.client('s3')
    try:
        response = s3_client.head_object(Bucket=bucket_name, Key=s3_file_key)
        return response['ETag'].strip('"')
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"El archivo {s3_file_key} no existe en el bucket {bucket_name}.")
            return None
        else:
            print(f"Error getting S3 MD5 for {s3_file_key} in bucket {bucket_name}: {e}")
            return None

def upload_to_s3(file_path, bucket_name, s3_file_key):
    """
    Sube un archivo a un bucket de S3 si es diferente al archivo existente.

    Args:
        file_path (str): Ruta local del archivo a subir.
        bucket_name (str): Nombre del bucket de S3.
        s3_file_key (str): Clave (ruta) en el bucket de S3.
    """
    local_md5 = calculate_md5(file_path)
    s3_md5 = get_s3_md5(bucket_name, s3_file_key)
    
    if s3_md5 == local_md5:
        print(f"El archivo {file_path} ya está actualizado en {bucket_name}/{s3_file_key}")
        return
    
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(file_path, bucket_name, s3_file_key)
        print(f"Archivo {file_path} subido a {bucket_name}/{s3_file_key}")
    except ClientError as e:
        print(f"No se pudo subir el archivo: {e}")

def read_from_s3(bucket_name, s3_file_key):
    """
    Lee un archivo CSV desde un bucket de S3.

    Args:
        bucket_name (str): Nombre del bucket de S3.
        s3_file_key (str): Clave (ruta) en el bucket de S3.

    Returns:
        pandas.DataFrame: DataFrame de pandas con el contenido del archivo CSV.
    """
    s3_client = boto3.client('s3')
    try:
        csv_obj = s3_client.get_object(Bucket=bucket_name, Key=s3_file_key)
        body = csv_obj['Body']
        csv_string = body.read().decode('utf-8')
        return pd.read_csv(StringIO(csv_string))
    except ClientError as e:
        print(f"No se pudo leer el archivo: {e}")
        return None

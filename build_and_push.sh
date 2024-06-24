#!/bin/bash

# Variables
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="471112756729"

# Servicios
services=("indexar_movies" "mejorar_pregunta" "obtener_embedding" "normalizar_embeddings" "recuperar_embeddings" "generar_respuesta")


# Crear un Builder y Configurar Buildx
if ! docker buildx inspect mybuilder > /dev/null 2>&1; then
  docker buildx create --use --name mybuilder
  docker buildx inspect mybuilder --bootstrap
else
  echo "Builder 'mybuilder' ya existe, usando el existente."
  docker buildx use mybuilder
fi

# Login en ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Crear Repositorios ECR y Construir, Etiquetar y Subir Imágenes
for service in "${services[@]}"
do
  # Crear el repositorio ECR si no existe
  if ! aws ecr describe-repositories --repository-names $service --region $AWS_REGION > /dev/null 2>&1; then
    aws ecr create-repository --repository-name $service --region $AWS_REGION
  else
    echo "El repositorio $service ya existe, omitiendo la creación."
  fi

  # Construir la imagen Docker
  if docker buildx build --platform linux/amd64 -t $service ./services/$service --load; then
    echo "Imagen $service construida exitosamente."
  else
    echo "Error al construir la imagen $service. Asegúrate de que el directorio y el Dockerfile existen."
    continue
  fi
  
  # Etiquetar la imagen Docker
  docker tag $service:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$service:latest
  
  # Subir la imagen a ECR
  if docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$service:latest; then
    echo "Imagen $service subida a ECR exitosamente."
  else
    echo "Error al subir la imagen $service a ECR."
  fi
done
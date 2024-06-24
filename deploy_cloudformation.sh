#!/bin/bash

# Variables
BUCKET_NAME="project-root-qs-cloudformation"
STACK_NAME="project-root"
TEMPLATE_DIR="deployment"
TEMPLATE_FILE="${TEMPLATE_DIR}/cloudformation.yaml"
TEMPLATE_URL="https://${BUCKET_NAME}.s3.amazonaws.com/cloudformation.yaml"

# Verificar si el archivo de plantilla existe
if [ ! -f "${TEMPLATE_FILE}" ]; then
  echo "Error: El archivo de plantilla ${TEMPLATE_FILE} no existe."
  exit 1
fi

# Crear el Bucket de S3 si no existe
if aws s3 ls "s3://${BUCKET_NAME}" 2>&1 | grep -q 'NoSuchBucket'; then
    echo "Creating S3 bucket: ${BUCKET_NAME}"
    aws s3 mb s3://${BUCKET_NAME}
else
    echo "S3 bucket ${BUCKET_NAME} already exists"
fi

# Subir la Plantilla a S3
echo "Uploading ${TEMPLATE_FILE} to S3 bucket: ${BUCKET_NAME}"
aws s3 cp ${TEMPLATE_FILE} s3://${BUCKET_NAME}/cloudformation.yaml
if [ $? -ne 0 ]; then
  echo "Error: No se pudo subir la plantilla a S3. Verifica los permisos y la conectividad."
  exit 1
fi

# Crear o actualizar el Stack de CloudFormation
if aws cloudformation describe-stacks --stack-name ${STACK_NAME} 2>&1 | grep -q 'does not exist'; then
    echo "Creating CloudFormation stack: ${STACK_NAME}"
    aws cloudformation create-stack --stack-name ${STACK_NAME} --template-url ${TEMPLATE_URL} --capabilities CAPABILITY_NAMED_IAM
else
    echo "Updating CloudFormation stack: ${STACK_NAME}"
    aws cloudformation update-stack --stack-name ${STACK_NAME} --template-url ${TEMPLATE_URL} --capabilities CAPABILITY_NAMED_IAM
fi

# Esperar hasta que el Stack esté completamente creado o actualizado
echo "Waiting for stack ${STACK_NAME} to be created/updated..."
aws cloudformation wait stack-create-complete --stack-name ${STACK_NAME} || aws cloudformation wait stack-update-complete --stack-name ${STACK_NAME}

echo "Stack ${STACK_NAME} created/updated successfully."
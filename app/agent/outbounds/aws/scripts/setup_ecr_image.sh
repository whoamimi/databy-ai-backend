#!/bin/bash
set -e  # Exit immediately on error

# ====== CONFIGURATION ======
ECR_REPO_NAME=${1:-"bedrock-agent-repo"}
AWS_REGION=${2:-"ap-southeast-2"}
IMAGE_TAG=${3:-"latest"}

echo "Creating ECR repository: ${ECR_REPO_NAME} in region: ${AWS_REGION}"

# ====== CREATE REPOSITORY ======
aws ecr create-repository \
  --repository-name "${ECR_REPO_NAME}" \
  --image-scanning-configuration scanOnPush=true \
  --encryption-configuration encryptionType=KMS \
  --region "${AWS_REGION}" \
  || echo "Repository may already exist"

# ====== LIST REPOSITORIES ======
echo "Listing repositories in ${AWS_REGION}:"
aws ecr describe-repositories --region "${AWS_REGION}"

# ====== RETRIEVE REPOSITORY URI ======
REPO_URI=$(aws ecr describe-repositories \
  --repository-names "${ECR_REPO_NAME}" \
  --query 'repositories[0].repositoryUri' \
  --output text \
  --region "${AWS_REGION}")

echo "Repository URI: ${REPO_URI}"

# ====== LOGIN TO ECR ======
echo "Logging into Amazon ECR..."
aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${REPO_URI}"

# ====== BUILD AND PUSH IMAGE ======
echo "Building Docker image: ${ECR_REPO_NAME}:${IMAGE_TAG}"
docker build -t "${ECR_REPO_NAME}:${IMAGE_TAG}" .

echo "Tagging Docker image for ECR..."
docker tag "${ECR_REPO_NAME}:${IMAGE_TAG}" "${REPO_URI}:${IMAGE_TAG}"

echo "Pushing image to ECR..."
docker push "${REPO_URI}:${IMAGE_TAG}"

# ====== DONE ======
echo "✅ Successfully pushed ${REPO_URI}:${IMAGE_TAG} to Amazon ECR"
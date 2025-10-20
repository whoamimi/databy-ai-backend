#!/bin/bash
# Setup script for AWS SageMaker Model Endpoint
# Deploys a HuggingFace model to a SageMaker endpoint
set -e  # Exit on any error

echo "=== SageMaker Model Endpoint Setup ==="

# Read configuration from environment or arguments
REGION=${1:-${AWS_REGION:-"us-east-1"}}
MODEL_NAME=${2:-"databy-hf-model"}
ENDPOINT_CONFIG_NAME=${3:-"databy-endpoint-config"}
ENDPOINT_NAME=${4:-"databy-endpoint"}
INSTANCE_TYPE=${5:-${AWS_INSTANCE_TYPE:-"ml.t3.medium"}}
INSTANCE_COUNT=${6:-${AWS_INSTANCE_COUNT:-1}}
EXECUTION_ROLE_ARN=${7:-${AWS_SAGEMAKER_SERVICE_ROLE:-""}}
HF_MODEL_ID=${8:-"distilbert-base-uncased"}
HF_TASK=${9:-"fill-mask"}

echo "Configuration:"
echo "  Region: $REGION"
echo "  Model Name: $MODEL_NAME"
echo "  Endpoint Config: $ENDPOINT_CONFIG_NAME"
echo "  Endpoint Name: $ENDPOINT_NAME"
echo "  Instance Type: $INSTANCE_TYPE"
echo "  Instance Count: $INSTANCE_COUNT"
echo "  HuggingFace Model: $HF_MODEL_ID"
echo "  HuggingFace Task: $HF_TASK"

# Validate required parameters
if [ -z "$EXECUTION_ROLE_ARN" ]; then
    echo "ERROR: Execution role ARN is required"
    echo "Usage: $0 [region] [model_name] [endpoint_config] [endpoint_name] [instance_type] [instance_count] [role_arn] [hf_model_id] [hf_task]"
    exit 1
fi

# Get HuggingFace DLC image URI
echo -e "\nGetting HuggingFace Deep Learning Container image..."
# Using HuggingFace Inference DLC for PyTorch
IMAGE_URI="763104351884.dkr.ecr.$REGION.amazonaws.com/huggingface-pytorch-inference:2.1.0-transformers4.37.0-cpu-py310-ubuntu22.04"

# Check if model already exists
echo -e "\nChecking for existing model..."
if aws sagemaker describe-model --region "$REGION" --model-name "$MODEL_NAME" &>/dev/null; then
    echo "Model '$MODEL_NAME' already exists, deleting..."
    aws sagemaker delete-model --region "$REGION" --model-name "$MODEL_NAME"
fi

# Create model
echo -e "\nCreating SageMaker model..."
aws sagemaker create-model \
    --region "$REGION" \
    --model-name "$MODEL_NAME" \
    --execution-role-arn "$EXECUTION_ROLE_ARN" \
    --primary-container "{
        \"Image\": \"$IMAGE_URI\",
        \"Environment\": {
            \"HF_MODEL_ID\": \"$HF_MODEL_ID\",
            \"HF_TASK\": \"$HF_TASK\"
        }
    }"

echo "Model created successfully!"

# Check if endpoint config exists
echo -e "\nChecking for existing endpoint configuration..."
if aws sagemaker describe-endpoint-config --region "$REGION" --endpoint-config-name "$ENDPOINT_CONFIG_NAME" &>/dev/null; then
    echo "Endpoint config '$ENDPOINT_CONFIG_NAME' already exists, deleting..."
    aws sagemaker delete-endpoint-config --region "$REGION" --endpoint-config-name "$ENDPOINT_CONFIG_NAME"
fi

# Create endpoint configuration
echo -e "\nCreating endpoint configuration..."
aws sagemaker create-endpoint-config \
    --region "$REGION" \
    --endpoint-config-name "$ENDPOINT_CONFIG_NAME" \
    --production-variants "[{
        \"VariantName\": \"AllTraffic\",
        \"ModelName\": \"$MODEL_NAME\",
        \"InitialInstanceCount\": $INSTANCE_COUNT,
        \"InstanceType\": \"$INSTANCE_TYPE\",
        \"InitialVariantWeight\": 1.0
    }]"

echo "Endpoint configuration created successfully!"

# Check if endpoint exists
echo -e "\nChecking for existing endpoint..."
if aws sagemaker describe-endpoint --region "$REGION" --endpoint-name "$ENDPOINT_NAME" &>/dev/null; then
    echo "Endpoint '$ENDPOINT_NAME' already exists, updating..."
    aws sagemaker update-endpoint \
        --region "$REGION" \
        --endpoint-name "$ENDPOINT_NAME" \
        --endpoint-config-name "$ENDPOINT_CONFIG_NAME"
else
    # Create endpoint
    echo -e "\nCreating endpoint..."
    aws sagemaker create-endpoint \
        --region "$REGION" \
        --endpoint-name "$ENDPOINT_NAME" \
        --endpoint-config-name "$ENDPOINT_CONFIG_NAME"
fi

echo "Endpoint creation initiated!"

# Wait for endpoint to be in service
echo -e "\nWaiting for endpoint to be InService (this may take several minutes)..."
aws sagemaker wait endpoint-in-service \
    --region "$REGION" \
    --endpoint-name "$ENDPOINT_NAME"

echo -e "\nEndpoint is now InService!"

# Display endpoint details
echo -e "\nEndpoint details:"
aws sagemaker describe-endpoint \
    --region "$REGION" \
    --endpoint-name "$ENDPOINT_NAME"

echo -e "\n=== SageMaker Model Endpoint Setup Complete ==="
echo "You can now invoke the endpoint using:"
echo "aws sagemaker-runtime invoke-endpoint --endpoint-name $ENDPOINT_NAME --body '{\"inputs\":\"your text\"}' output.json"

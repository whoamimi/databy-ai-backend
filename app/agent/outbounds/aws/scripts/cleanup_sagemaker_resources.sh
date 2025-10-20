#!/bin/bash
# Cleanup script for AWS SageMaker resources
# Deletes endpoints, endpoint configs, and models to avoid charges
set -e  # Exit on any error

echo "=== SageMaker Resources Cleanup ==="

# Read configuration from environment or arguments
REGION=${1:-${AWS_REGION:-"us-east-1"}}
RESOURCE_PREFIX=${2:-"databy"}

echo "Configuration:"
echo "  Region: $REGION"
echo "  Resource Prefix: $RESOURCE_PREFIX"

# List and delete endpoints
echo -e "\n=== Cleaning up Endpoints ==="
ENDPOINTS=$(aws sagemaker list-endpoints \
    --region "$REGION" \
    --query "Endpoints[?starts_with(EndpointName, '$RESOURCE_PREFIX')].EndpointName" \
    --output text)

if [ -n "$ENDPOINTS" ]; then
    echo "Found endpoints to delete:"
    for ENDPOINT in $ENDPOINTS; do
        echo "  - $ENDPOINT"
        aws sagemaker delete-endpoint \
            --region "$REGION" \
            --endpoint-name "$ENDPOINT"
        echo "    Deleted!"
    done
else
    echo "No endpoints found with prefix '$RESOURCE_PREFIX'"
fi

# List and delete endpoint configurations
echo -e "\n=== Cleaning up Endpoint Configurations ==="
ENDPOINT_CONFIGS=$(aws sagemaker list-endpoint-configs \
    --region "$REGION" \
    --query "EndpointConfigs[?starts_with(EndpointConfigName, '$RESOURCE_PREFIX')].EndpointConfigName" \
    --output text)

if [ -n "$ENDPOINT_CONFIGS" ]; then
    echo "Found endpoint configs to delete:"
    for CONFIG in $ENDPOINT_CONFIGS; do
        echo "  - $CONFIG"
        aws sagemaker delete-endpoint-config \
            --region "$REGION" \
            --endpoint-config-name "$CONFIG"
        echo "    Deleted!"
    done
else
    echo "No endpoint configs found with prefix '$RESOURCE_PREFIX'"
fi

# List and delete models
echo -e "\n=== Cleaning up Models ==="
MODELS=$(aws sagemaker list-models \
    --region "$REGION" \
    --query "Models[?starts_with(ModelName, '$RESOURCE_PREFIX')].ModelName" \
    --output text)

if [ -n "$MODELS" ]; then
    echo "Found models to delete:"
    for MODEL in $MODELS; do
        echo "  - $MODEL"
        aws sagemaker delete-model \
            --region "$REGION" \
            --model-name "$MODEL"
        echo "    Deleted!"
    done
else
    echo "No models found with prefix '$RESOURCE_PREFIX'"
fi

echo -e "\n=== Cleanup Complete ==="
echo "Summary of actions taken:"
echo "  - Deleted endpoints matching prefix '$RESOURCE_PREFIX'"
echo "  - Deleted endpoint configurations matching prefix '$RESOURCE_PREFIX'"
echo "  - Deleted models matching prefix '$RESOURCE_PREFIX'"
echo -e "\nNote: Domain and user profiles were not deleted for safety."
echo "To delete those, use the AWS Console or specific delete commands."

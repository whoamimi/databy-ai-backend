#!/bin/bash
# AWS Setup Script - Start SageMaker and Bedrock Services
# Sets up SageMaker AI Domain, Endpoint, and Bedrock AgentCore
set -e  # Exit on any error

echo "==================================="
echo "Starting AWS Services Setup"
echo "==================================="
echo ""

# Read configuration from environment or arguments
REGION=${1:-${AWS_REGION:-"us-east-1"}}
DOMAIN_NAME=${2:-"databy-ai-domain"}
ENDPOINT_NAME=${3:-"databy-endpoint"}
EXECUTION_ROLE_ARN=${4:-${AWS_SAGEMAKER_SERVICE_ROLE:-""}}

echo "Configuration:"
echo "  Region: $REGION"
echo "  Domain Name: $DOMAIN_NAME"
echo "  Endpoint Name: $ENDPOINT_NAME"
echo "  Execution Role: $EXECUTION_ROLE_ARN"
echo ""

# Validate required parameters
if [ -z "$EXECUTION_ROLE_ARN" ]; then
    echo "ERROR: Execution role ARN is required"
    echo "Set AWS_SAGEMAKER_SERVICE_ROLE environment variable or pass as argument"
    exit 1
fi

# ====================
# 1. SAGEMAKER DOMAIN
# ====================
echo "=== 1. Setting up SageMaker Domain ==="
EXISTING_DOMAIN=$(aws sagemaker list-domains \
    --region "$REGION" \
    --query "Domains[?DomainName=='$DOMAIN_NAME'].DomainId" \
    --output text 2>/dev/null || echo "")

if [ -n "$EXISTING_DOMAIN" ]; then
    echo "✓ Domain already exists: $EXISTING_DOMAIN"
    DOMAIN_ID="$EXISTING_DOMAIN"
else
    echo "Creating new SageMaker domain..."
    DOMAIN_ID=$(aws sagemaker create-domain \
        --region "$REGION" \
        --domain-name "$DOMAIN_NAME" \
        --auth-mode IAM \
        --default-user-settings "{
            \"ExecutionRole\": \"$EXECUTION_ROLE_ARN\"
        }" \
        --query 'DomainId' \
        --output text)

    echo "Waiting for domain to be InService..."
    aws sagemaker wait domain-in-service \
        --region "$REGION" \
        --domain-id "$DOMAIN_ID"

    echo "✓ Domain created: $DOMAIN_ID"
fi
echo ""

# ====================
# 2. SAGEMAKER ENDPOINT
# ====================
echo "=== 2. Setting up SageMaker Endpoint ==="
MODEL_NAME="databy-hf-model"
ENDPOINT_CONFIG_NAME="databy-endpoint-config"
INSTANCE_TYPE=${AWS_INSTANCE_TYPE:-"ml.t3.medium"}
INSTANCE_COUNT=${AWS_INSTANCE_COUNT:-1}
HF_MODEL_ID=${HF_MODEL_ID:-"distilbert-base-uncased"}
HF_TASK=${HF_TASK:-"fill-mask"}

echo "Model: $HF_MODEL_ID"
echo "Task: $HF_TASK"
echo "Instance: $INSTANCE_TYPE (count: $INSTANCE_COUNT)"

# Get HuggingFace DLC image
IMAGE_URI="763104351884.dkr.ecr.$REGION.amazonaws.com/huggingface-pytorch-inference:2.1.0-transformers4.37.0-cpu-py310-ubuntu22.04"

# Create or update model
if aws sagemaker describe-model --region "$REGION" --model-name "$MODEL_NAME" &>/dev/null; then
    echo "Deleting existing model..."
    aws sagemaker delete-model --region "$REGION" --model-name "$MODEL_NAME"
fi

echo "Creating model..."
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
    }" > /dev/null

# Create or update endpoint config
if aws sagemaker describe-endpoint-config --region "$REGION" --endpoint-config-name "$ENDPOINT_CONFIG_NAME" &>/dev/null; then
    echo "Deleting existing endpoint config..."
    aws sagemaker delete-endpoint-config --region "$REGION" --endpoint-config-name "$ENDPOINT_CONFIG_NAME"
fi

echo "Creating endpoint configuration..."
aws sagemaker create-endpoint-config \
    --region "$REGION" \
    --endpoint-config-name "$ENDPOINT_CONFIG_NAME" \
    --production-variants "[{
        \"VariantName\": \"AllTraffic\",
        \"ModelName\": \"$MODEL_NAME\",
        \"InitialInstanceCount\": $INSTANCE_COUNT,
        \"InstanceType\": \"$INSTANCE_TYPE\",
        \"InitialVariantWeight\": 1.0
    }]" > /dev/null

# Create or update endpoint
if aws sagemaker describe-endpoint --region "$REGION" --endpoint-name "$ENDPOINT_NAME" &>/dev/null; then
    echo "Updating existing endpoint..."
    aws sagemaker update-endpoint \
        --region "$REGION" \
        --endpoint-name "$ENDPOINT_NAME" \
        --endpoint-config-name "$ENDPOINT_CONFIG_NAME" > /dev/null
else
    echo "Creating endpoint..."
    aws sagemaker create-endpoint \
        --region "$REGION" \
        --endpoint-name "$ENDPOINT_NAME" \
        --endpoint-config-name "$ENDPOINT_CONFIG_NAME" > /dev/null
fi

echo "Waiting for endpoint to be InService (may take several minutes)..."
aws sagemaker wait endpoint-in-service \
    --region "$REGION" \
    --endpoint-name "$ENDPOINT_NAME"

echo "✓ Endpoint ready: $ENDPOINT_NAME"
echo ""

# ====================
# 3. BEDROCK AGENTCORE
# ====================
echo "=== 3. Setting up Bedrock AgentCore ==="
SESSION_ID="databy-agentcore-session-$(date +%s)"

# Validate session ID length
if [ ${#SESSION_ID} -lt 33 ]; then
    echo "ERROR: Session ID too short (${#SESSION_ID} chars, need 33+)"
    exit 1
fi

# Check Bedrock availability
if ! aws bedrock list-foundation-models --region "$REGION" &>/dev/null; then
    echo "WARNING: Bedrock not available in $REGION"
    echo "Available regions: us-east-1, us-west-2, ap-southeast-1, ap-northeast-1, eu-central-1"
else
    echo "✓ Bedrock service available"
    echo "Session ID: $SESSION_ID"

    # List available models
    echo ""
    echo "Available Claude models:"
    aws bedrock list-foundation-models \
        --region "$REGION" \
        --query 'modelSummaries[?contains(modelId, `claude`)].{ModelId:modelId}' \
        --output table 2>/dev/null || echo "  (none found)"
fi
echo ""

# ====================
# 4. SUMMARY
# ====================
echo "==================================="
echo "Setup Complete!"
echo "==================================="
echo ""
echo "Environment variables to set:"
echo "  export AWS_REGION=$REGION"
echo "  export AWS_SAGEMAKER_DOMAIN_ID=$DOMAIN_ID"
echo "  export AWS_SAGEMAKER_ENDPOINT_NAME=$ENDPOINT_NAME"
echo "  export AWS_BEDROCK_SESSION_ID=$SESSION_ID"
echo ""
echo "Services running:"
echo "  ✓ SageMaker Domain: $DOMAIN_ID"
echo "  ✓ SageMaker Endpoint: $ENDPOINT_NAME"
echo "  ✓ Bedrock AgentCore: Ready"
echo ""
echo "To stop services and avoid charges:"
echo "  bash on_stop.sh"
echo ""

exit 0
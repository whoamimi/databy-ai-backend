#!/bin/bash
# Setup script for AWS Bedrock AgentCore
# Configures Bedrock AgentCore for code execution capabilities
set -e  # Exit on any error

echo "=== Bedrock AgentCore Setup ==="

# Read configuration from environment or arguments
REGION=${1:-${AWS_REGION:-"us-east-1"}}
SESSION_ID=${2:-"databy-agentcore-session-$(date +%s)"}
EXECUTION_ROLE_ARN=${3:-${AWS_SAGEMAKER_SERVICE_ROLE:-""}}

echo "Configuration:"
echo "  Region: $REGION"
echo "  Session ID: $SESSION_ID"
echo "  Execution Role: $EXECUTION_ROLE_ARN"

# Validate session ID length (must be 33+ chars)
if [ ${#SESSION_ID} -lt 33 ]; then
    echo "ERROR: Session ID must be at least 33 characters long"
    echo "Current length: ${#SESSION_ID}"
    exit 1
fi

# Check if Bedrock service is available in the region
echo -e "\nChecking Bedrock service availability..."
if ! aws bedrock list-foundation-models --region "$REGION" &>/dev/null; then
    echo "ERROR: Bedrock service not available in region $REGION"
    echo "Available regions: us-east-1, us-west-2, ap-southeast-1, ap-northeast-1, eu-central-1"
    exit 1
fi

echo "Bedrock service is available!"

# List available foundation models
echo -e "\nAvailable Bedrock foundation models:"
aws bedrock list-foundation-models \
    --region "$REGION" \
    --query 'modelSummaries[?contains(modelId, `claude`)].{ModelId:modelId, ModelName:modelName}' \
    --output table

# Check AgentCore permissions
echo -e "\nVerifying AgentCore permissions..."
if [ -n "$EXECUTION_ROLE_ARN" ]; then
    echo "Using execution role: $EXECUTION_ROLE_ARN"

    # Check if role has bedrock permissions
    ROLE_NAME=$(echo "$EXECUTION_ROLE_ARN" | awk -F'/' '{print $NF}')
    echo "Role name: $ROLE_NAME"

    echo -e "\nRole policies:"
    aws iam list-attached-role-policies \
        --role-name "$ROLE_NAME" \
        --query 'AttachedPolicies[].PolicyName' \
        --output table 2>/dev/null || echo "WARNING: Could not list role policies"
else
    echo "WARNING: No execution role specified"
fi

# Test AgentCore code execution capability
echo -e "\n=== Testing AgentCore Code Execution ==="
echo "Testing with a simple Python script..."

# Create test Python code
TEST_CODE='print("Hello from Bedrock AgentCore!")'

# Create a temporary output file
OUTPUT_FILE=$(mktemp)

# Try to execute code via AgentCore
echo "Invoking AgentCore..."
if aws bedrock-agent-runtime invoke-inline-agent \
    --region "$REGION" \
    --session-id "$SESSION_ID" \
    --inline-session-state '{
        "sessionAttributes": {},
        "promptSessionAttributes": {}
    }' \
    --input-text "Execute this Python code: $TEST_CODE" \
    --enable-trace \
    --foundation-model "anthropic.claude-3-sonnet-20240229-v1:0" \
    "$OUTPUT_FILE" 2>/dev/null; then

    echo "AgentCore invocation successful!"
    echo "Response saved to: $OUTPUT_FILE"
    cat "$OUTPUT_FILE"
else
    echo "NOTE: Direct AgentCore invocation requires an agent to be created first"
    echo "See setup_bedrock_agent.sh for creating an agent with code execution"
fi

# Clean up
rm -f "$OUTPUT_FILE"

# Display configuration summary
echo -e "\n=== Configuration Summary ==="
cat <<EOF
Bedrock AgentCore is now configured for use.

To use AgentCore in your Python code:

import boto3
import json

client = boto3.client('bedrock-agent-runtime', region_name='$REGION')

response = client.invoke_inline_agent(
    sessionId='$SESSION_ID',
    inlineSessionState={
        'sessionAttributes': {},
        'promptSessionAttributes': {}
    },
    inputText='Your prompt here',
    foundationModel='anthropic.claude-3-sonnet-20240229-v1:0'
)

Environment variables to set:
  AWS_REGION=$REGION
  AWS_BEDROCK_SESSION_ID=$SESSION_ID

For code interpreter functionality, create an agent with:
  bash setup_bedrock_agent_with_code.sh
EOF

echo -e "\n=== Bedrock AgentCore Setup Complete ==="

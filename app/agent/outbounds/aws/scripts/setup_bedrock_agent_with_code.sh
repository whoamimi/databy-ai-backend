#!/bin/bash
# Setup script for AWS Bedrock Agent with Code Interpreter
# Creates a Bedrock agent with code execution capabilities
set -e  # Exit on any error

echo "=== Bedrock Agent with Code Interpreter Setup ==="

# Read configuration from environment or arguments
REGION=${1:-${AWS_REGION:-"us-east-1"}}
AGENT_NAME=${2:-"databy-code-agent"}
FOUNDATION_MODEL=${3:-"anthropic.claude-3-sonnet-20240229-v1:0"}
EXECUTION_ROLE_ARN=${4:-${AWS_SAGEMAKER_SERVICE_ROLE:-""}}

echo "Configuration:"
echo "  Region: $REGION"
echo "  Agent Name: $AGENT_NAME"
echo "  Foundation Model: $FOUNDATION_MODEL"
echo "  Execution Role: $EXECUTION_ROLE_ARN"

# Validate required parameters
if [ -z "$EXECUTION_ROLE_ARN" ]; then
    echo "ERROR: Execution role ARN is required"
    echo "The role needs permissions for Bedrock and S3"
    exit 1
fi

# Create agent instruction file
INSTRUCTION_FILE=$(mktemp)
cat > "$INSTRUCTION_FILE" <<'EOF'
You are DataBy AI, an autonomous data analysis agent with code execution capabilities.

Your responsibilities:
1. Analyze data using Python code
2. Generate insights and visualizations
3. Perform statistical analysis
4. Clean and transform data
5. Answer questions about datasets

When given a task:
- Break it down into steps
- Write clean, efficient Python code
- Use appropriate libraries (pandas, numpy, matplotlib, etc.)
- Provide clear explanations of your analysis
- Handle errors gracefully

You have access to a code interpreter to execute Python code.
Always validate your outputs and provide context for your results.
EOF

echo -e "\nAgent instruction file created"

# Check if agent already exists
echo -e "\nChecking for existing agent..."
EXISTING_AGENT=$(aws bedrock-agent list-agents \
    --region "$REGION" \
    --query "agentSummaries[?agentName=='$AGENT_NAME'].agentId" \
    --output text)

if [ -n "$EXISTING_AGENT" ]; then
    echo "Agent '$AGENT_NAME' already exists with ID: $EXISTING_AGENT"

    # Get agent details
    echo -e "\nAgent details:"
    aws bedrock-agent get-agent \
        --region "$REGION" \
        --agent-id "$EXISTING_AGENT"

    # Clean up temp file
    rm -f "$INSTRUCTION_FILE"
    exit 0
fi

# Create the agent
echo -e "\nCreating Bedrock agent..."
AGENT_ID=$(aws bedrock-agent create-agent \
    --region "$REGION" \
    --agent-name "$AGENT_NAME" \
    --foundation-model "$FOUNDATION_MODEL" \
    --instruction file://"$INSTRUCTION_FILE" \
    --agent-resource-role-arn "$EXECUTION_ROLE_ARN" \
    --query 'agent.agentId' \
    --output text)

echo "Agent created successfully!"
echo "Agent ID: $AGENT_ID"

# Enable code interpreter action group
echo -e "\nEnabling code interpreter..."
aws bedrock-agent create-agent-action-group \
    --region "$REGION" \
    --agent-id "$AGENT_ID" \
    --agent-version "DRAFT" \
    --action-group-name "code-interpreter" \
    --parent-action-group-signature "AMAZON.CodeInterpreter" \
    --action-group-state "ENABLED"

echo "Code interpreter enabled!"

# Prepare the agent
echo -e "\nPreparing agent..."
aws bedrock-agent prepare-agent \
    --region "$REGION" \
    --agent-id "$AGENT_ID"

echo "Agent preparation initiated!"

# Wait for agent to be prepared
echo -e "\nWaiting for agent to be prepared..."
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    STATUS=$(aws bedrock-agent get-agent \
        --region "$REGION" \
        --agent-id "$AGENT_ID" \
        --query 'agent.agentStatus' \
        --output text)

    echo "Status: $STATUS (Attempt $((ATTEMPT+1))/$MAX_ATTEMPTS)"

    if [ "$STATUS" = "PREPARED" ]; then
        echo "Agent is now prepared!"
        break
    elif [ "$STATUS" = "FAILED" ]; then
        echo "ERROR: Agent preparation failed"
        exit 1
    fi

    ATTEMPT=$((ATTEMPT+1))
    sleep 10
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "WARNING: Timeout waiting for agent to be prepared"
fi

# Create agent alias
echo -e "\nCreating agent alias..."
ALIAS_ID=$(aws bedrock-agent create-agent-alias \
    --region "$REGION" \
    --agent-id "$AGENT_ID" \
    --agent-alias-name "production" \
    --query 'agentAlias.agentAliasId' \
    --output text)

echo "Agent alias created: $ALIAS_ID"

# Display agent details
echo -e "\nAgent details:"
aws bedrock-agent get-agent \
    --region "$REGION" \
    --agent-id "$AGENT_ID"

# Clean up temp file
rm -f "$INSTRUCTION_FILE"

# Display usage instructions
echo -e "\n=== Configuration Summary ==="
cat <<EOF
Bedrock Agent with Code Interpreter is now ready!

Agent ID: $AGENT_ID
Alias ID: $ALIAS_ID

To invoke the agent in Python:

import boto3
import uuid

client = boto3.client('bedrock-agent-runtime', region_name='$REGION')

session_id = str(uuid.uuid4())

response = client.invoke_agent(
    agentId='$AGENT_ID',
    agentAliasId='$ALIAS_ID',
    sessionId=session_id,
    inputText='Analyze this data: [1, 2, 3, 4, 5]'
)

# Stream the response
for event in response['completion']:
    if 'chunk' in event:
        print(event['chunk']['bytes'].decode('utf-8'))

Environment variables to set:
  AWS_BEDROCK_AGENT_ID=$AGENT_ID
  AWS_BEDROCK_ALIAS_ID=$ALIAS_ID
  AWS_REGION=$REGION

Test the agent:
  aws bedrock-agent-runtime invoke-agent \\
    --agent-id $AGENT_ID \\
    --agent-alias-id $ALIAS_ID \\
    --session-id \$(uuidgen) \\
    --input-text "Calculate the sum of 1 to 10" \\
    --region $REGION
EOF

echo -e "\n=== Bedrock Agent Setup Complete ==="

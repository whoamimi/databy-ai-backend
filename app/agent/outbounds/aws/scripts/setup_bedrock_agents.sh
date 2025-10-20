#!/bin/bash
# Setup script sets up the required workflow for AWS Bedrock AgentCore outbound integration
# Sets up planner agent
set -e  # Exit immediately on error

AGENT_NAME=$1
MODEL=$2
INSTRUCTION_FILE=$3

aws bedrock-agent create-agent \
  --agent-name "$AGENT_NAME" \
  --foundation-model "$MODEL" \
  --instruction-file "file://$INSTRUCTION_FILE"

echo "Agent $AGENT_NAME created successfully."
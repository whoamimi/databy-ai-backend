#!/bin/bash
# Setup script for AWS SageMaker AI Domain
# Creates or verifies SageMaker domain for AI workspace
set -e  # Exit on any error

echo "=== SageMaker Domain Setup ==="

# Read configuration from environment or arguments
REGION=${1:-${AWS_REGION:-"us-east-1"}}
DOMAIN_NAME=${2:-"databy-ai-domain"}
VPC_ID=${3:-""}
SUBNET_IDS=${4:-""}
EXECUTION_ROLE_ARN=${5:-${AWS_SAGEMAKER_SERVICE_ROLE:-""}}

echo "Configuration:"
echo "  Region: $REGION"
echo "  Domain Name: $DOMAIN_NAME"
echo "  Execution Role: $EXECUTION_ROLE_ARN"

# Validate required parameters
if [ -z "$EXECUTION_ROLE_ARN" ]; then
    echo "ERROR: Execution role ARN is required"
    echo "Usage: $0 [region] [domain_name] [vpc_id] [subnet_ids] [execution_role_arn]"
    exit 1
fi

# Check if domain already exists
echo -e "\nChecking for existing domains..."
EXISTING_DOMAIN=$(aws sagemaker list-domains \
    --region "$REGION" \
    --query "Domains[?DomainName=='$DOMAIN_NAME'].DomainId" \
    --output text)

if [ -n "$EXISTING_DOMAIN" ]; then
    echo "Domain already exists with ID: $EXISTING_DOMAIN"
    echo "Domain details:"
    aws sagemaker describe-domain \
        --region "$REGION" \
        --domain-id "$EXISTING_DOMAIN"
    exit 0
fi

# Create domain
echo -e "\nCreating new SageMaker domain..."

# Build the create-domain command based on available parameters
if [ -n "$VPC_ID" ] && [ -n "$SUBNET_IDS" ]; then
    echo "Creating domain with VPC configuration..."
    DOMAIN_ID=$(aws sagemaker create-domain \
        --region "$REGION" \
        --domain-name "$DOMAIN_NAME" \
        --auth-mode IAM \
        --default-user-settings "{
            \"ExecutionRole\": \"$EXECUTION_ROLE_ARN\"
        }" \
        --vpc-id "$VPC_ID" \
        --subnet-ids $SUBNET_IDS \
        --query 'DomainId' \
        --output text)
else
    echo "Creating domain with public internet access..."
    DOMAIN_ID=$(aws sagemaker create-domain \
        --region "$REGION" \
        --domain-name "$DOMAIN_NAME" \
        --auth-mode IAM \
        --default-user-settings "{
            \"ExecutionRole\": \"$EXECUTION_ROLE_ARN\"
        }" \
        --query 'DomainId' \
        --output text)
fi

echo "Domain created successfully!"
echo "Domain ID: $DOMAIN_ID"

# Wait for domain to be in service
echo -e "\nWaiting for domain to be InService..."
aws sagemaker wait domain-in-service \
    --region "$REGION" \
    --domain-id "$DOMAIN_ID"

echo -e "\nDomain is now InService!"
echo "You can set AWS_SAGEMAKER_DOMAIN_ID=$DOMAIN_ID in your .env file"

# Display domain details
echo -e "\nDomain details:"
aws sagemaker describe-domain \
    --region "$REGION" \
    --domain-id "$DOMAIN_ID"

echo -e "\n=== SageMaker Domain Setup Complete ==="

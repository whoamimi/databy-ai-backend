#!/bin/bash
# Setup script for AWS SageMaker User Profile
# Creates a user profile within a SageMaker domain
set -e  # Exit on any error

echo "=== SageMaker User Profile Setup ==="

# Read configuration from environment or arguments
REGION=${1:-${AWS_REGION:-"us-east-1"}}
DOMAIN_ID=${2:-${AWS_SAGEMAKER_DOMAIN_ID:-""}}
USER_PROFILE_NAME=${3:-"ai-bot-workspace"}
EXECUTION_ROLE_ARN=${4:-${AWS_SAGEMAKER_SERVICE_ROLE:-""}}

echo "Configuration:"
echo "  Region: $REGION"
echo "  Domain ID: $DOMAIN_ID"
echo "  User Profile Name: $USER_PROFILE_NAME"
echo "  Execution Role: $EXECUTION_ROLE_ARN"

# Validate required parameters
if [ -z "$DOMAIN_ID" ]; then
    echo "ERROR: Domain ID is required"
    echo "Usage: $0 [region] [domain_id] [user_profile_name] [execution_role_arn]"
    exit 1
fi

if [ -z "$EXECUTION_ROLE_ARN" ]; then
    echo "ERROR: Execution role ARN is required"
    exit 1
fi

# Check if user profile already exists
echo -e "\nChecking for existing user profile..."
EXISTING_PROFILE=$(aws sagemaker list-user-profiles \
    --region "$REGION" \
    --domain-id-equals "$DOMAIN_ID" \
    --query "UserProfiles[?UserProfileName=='$USER_PROFILE_NAME'].UserProfileName" \
    --output text)

if [ -n "$EXISTING_PROFILE" ]; then
    echo "User profile '$USER_PROFILE_NAME' already exists"
    echo "User profile details:"
    aws sagemaker describe-user-profile \
        --region "$REGION" \
        --domain-id "$DOMAIN_ID" \
        --user-profile-name "$USER_PROFILE_NAME"
    exit 0
fi

# Create user profile
echo -e "\nCreating new user profile..."
aws sagemaker create-user-profile \
    --region "$REGION" \
    --domain-id "$DOMAIN_ID" \
    --user-profile-name "$USER_PROFILE_NAME" \
    --user-settings "{
        \"ExecutionRole\": \"$EXECUTION_ROLE_ARN\"
    }"

echo "User profile created successfully!"

# Wait for user profile to be in service
echo -e "\nWaiting for user profile to be InService..."
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    STATUS=$(aws sagemaker describe-user-profile \
        --region "$REGION" \
        --domain-id "$DOMAIN_ID" \
        --user-profile-name "$USER_PROFILE_NAME" \
        --query 'Status' \
        --output text)

    echo "Status: $STATUS (Attempt $((ATTEMPT+1))/$MAX_ATTEMPTS)"

    if [ "$STATUS" = "InService" ]; then
        echo "User profile is now InService!"
        break
    elif [ "$STATUS" = "Failed" ]; then
        echo "ERROR: User profile creation failed"
        exit 1
    fi

    ATTEMPT=$((ATTEMPT+1))
    sleep 10
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "WARNING: Timeout waiting for user profile to be InService"
fi

# Display user profile details
echo -e "\nUser profile details:"
aws sagemaker describe-user-profile \
    --region "$REGION" \
    --domain-id "$DOMAIN_ID" \
    --user-profile-name "$USER_PROFILE_NAME"

echo -e "\nYou can set AWS_SAGEMAKER_USER_ID=$USER_PROFILE_NAME in your .env file"

echo -e "\n=== SageMaker User Profile Setup Complete ==="

#!/bin/bash
# AWS CLI configuration inspection script
set -e  # Exit on any error

echo "=== AWS Configuration Check ==="

# View current configured profile/credentials
echo "Current configuration:"
aws configure list || { echo "ERROR: Failed to list AWS configuration"; exit 1; }

# Show all configuration values
echo -e "\nDefault profile configuration:"
aws configure list --profile default || echo "WARNING: Default profile not found"

# Get current region
echo -e "\nConfigured region:"
aws configure get region || { echo "ERROR: No region configured"; exit 1; }

# Get current access key
echo -e "\nConfigured access key:"
aws configure get aws_access_key_id || { echo "ERROR: No access key configured"; exit 1; }

# Check which IAM user/role you're authenticated as
echo -e "\nCaller identity:"
aws sts get-caller-identity || { echo "ERROR: Failed to authenticate with AWS. Check credentials."; exit 1; }

# View all configured profiles
echo -e "\nAvailable profiles:"
aws configure list-profiles || echo "WARNING: No profiles found"

# Show raw config file contents
echo -e "\nConfig file contents:"
if [ -f ~/.aws/config ]; then
    cat ~/.aws/config
else
    echo "WARNING: ~/.aws/config not found"
fi

echo -e "\n=== AWS Configuration Check Complete ==="
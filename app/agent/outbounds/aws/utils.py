"""
app.agent.outbounds.aws.utils

Utility functions for running AWS setup and management scripts.
"""
import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

from ....utils.settings import settings

# Get the scripts directory
SCRIPTS_DIR = Path(__file__).parent / "scripts"

def run_script(script_name: str, *args, cwd: Optional[str] = None) -> Dict[str, Any]:
    """
    Run a bash script with optional arguments.

    Args:
        script_name: Name of the script file (e.g., "setup_sagemaker_domain.sh")
        *args: Variable number of arguments to pass to the script
        cwd: Optional working directory (defaults to scripts directory)

    Returns:
        Dict with keys: 'success' (bool), 'stdout' (str), 'stderr' (str), 'returncode' (int)

    Raises:
        FileNotFoundError: If script doesn't exist
    """
    script_path = SCRIPTS_DIR / script_name

    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    # Build the command
    command = ["bash", str(script_path), *[str(arg) for arg in args]]

    # Set working directory
    working_dir = cwd or str(SCRIPTS_DIR)

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=working_dir,
            check=False  # Don't raise on non-zero exit
        )

        success = result.returncode == 0

        if success:
            print("✓ Script completed successfully")
        else:
            print(f"✗ Script failed with exit code {result.returncode}")

        if result.stdout:
            print("\nOutput:")
            print(result.stdout)

        if result.stderr:
            print("\nErrors/Warnings:")
            print(result.stderr)

        return {
            'success': success,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }

    except Exception as e:
        print(f"Error running script: {e}")
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1
        }


def setup_sagemaker_domain(
    region: Optional[str] = None,
    domain_name: str = "databy-ai-domain",
    vpc_id: Optional[str] = None,
    subnet_ids: Optional[str] = None,
    execution_role_arn: Optional[str] = None
) -> Dict[str, Any]:
    """
    Setup AWS SageMaker domain.

    Args:
        region: AWS region (defaults to settings.agent.cloud.aws.region)
        domain_name: Name for the SageMaker domain
        vpc_id: Optional VPC ID for domain
        subnet_ids: Optional subnet IDs (space-separated string)
        execution_role_arn: IAM role ARN (defaults to settings)

    Returns:
        Script execution result dictionary
    """
    aws_config = settings.agent.cloud.aws
    region = region or aws_config.region
    execution_role_arn = execution_role_arn or aws_config.sagemaker_service_role

    args = [region, domain_name]
    if vpc_id:
        args.append(vpc_id)
    if subnet_ids:
        args.append(subnet_ids)
    if execution_role_arn:
        args.append(execution_role_arn)

    return run_script("setup_sagemaker_domain.sh", *args)


def setup_sagemaker_user_profile(
    region: Optional[str] = None,
    domain_id: Optional[str] = None,
    user_profile_name: str = "ai-bot-workspace",
    execution_role_arn: Optional[str] = None
) -> Dict[str, Any]:
    """
    Setup SageMaker user profile.

    Args:
        region: AWS region (defaults to settings)
        domain_id: SageMaker domain ID (defaults to settings)
        user_profile_name: Name for user profile
        execution_role_arn: IAM role ARN (defaults to settings)

    Returns:
        Script execution result dictionary
    """
    aws_config = settings.agent.cloud.aws
    region = region or aws_config.region
    domain_id = domain_id or aws_config.sagemaker_domain_id
    execution_role_arn = execution_role_arn or aws_config.sagemaker_service_role

    return run_script(
        "setup_sagemaker_user_profile.sh",
        region,
        domain_id,
        user_profile_name,
        execution_role_arn
    )


def setup_sagemaker_endpoint(
    region: Optional[str] = None,
    model_name: str = "databy-hf-model",
    endpoint_config_name: str = "databy-endpoint-config",
    endpoint_name: str = "databy-endpoint",
    instance_type: Optional[str] = None,
    instance_count: Optional[int] = None,
    execution_role_arn: Optional[str] = None,
    hf_model_id: str = "distilbert-base-uncased",
    hf_task: str = "fill-mask"
) -> Dict[str, Any]:
    """
    Setup SageMaker model endpoint.

    Args:
        region: AWS region
        model_name: Name for the SageMaker model
        endpoint_config_name: Name for endpoint configuration
        endpoint_name: Name for the endpoint
        instance_type: EC2 instance type (defaults to settings)
        instance_count: Number of instances (defaults to settings)
        execution_role_arn: IAM role ARN (defaults to settings)
        hf_model_id: HuggingFace model ID
        hf_task: HuggingFace task type

    Returns:
        Script execution result dictionary
    """
    aws_config = settings.agent.cloud.aws
    region = region or aws_config.region
    instance_type = instance_type or aws_config.instance_type
    instance_count = instance_count or aws_config.instance_count
    execution_role_arn = execution_role_arn or aws_config.sagemaker_service_role

    return run_script(
        "setup_sagemaker_endpoint.sh",
        region,
        model_name,
        endpoint_config_name,
        endpoint_name,
        instance_type,
        instance_count,
        execution_role_arn,
        hf_model_id,
        hf_task
    )


def setup_bedrock_agentcore(
    region: Optional[str] = None,
    session_id: Optional[str] = None,
    execution_role_arn: Optional[str] = None
) -> Dict[str, Any]:
    """
    Setup AWS Bedrock AgentCore.

    Args:
        region: AWS region (defaults to settings)
        session_id: Session ID (must be 33+ chars)
        execution_role_arn: IAM role ARN (defaults to settings)

    Returns:
        Script execution result dictionary
    """
    aws_config = settings.agent.cloud.aws
    region = region or aws_config.region
    execution_role_arn = execution_role_arn or aws_config.sagemaker_service_role

    args = [region]
    if session_id:
        args.append(session_id)
    if execution_role_arn:
        args.append(execution_role_arn)

    return run_script("setup_bedrock_agentcore.sh", *args)


def setup_bedrock_agent_with_code(
    region: Optional[str] = None,
    agent_name: str = "databy-code-agent",
    foundation_model: str = "anthropic.claude-3-sonnet-20240229-v1:0",
    execution_role_arn: Optional[str] = None
) -> Dict[str, Any]:
    """
    Setup Bedrock agent with code interpreter.

    Args:
        region: AWS region (defaults to settings)
        agent_name: Name for the Bedrock agent
        foundation_model: Foundation model ID
        execution_role_arn: IAM role ARN (defaults to settings)

    Returns:
        Script execution result dictionary
    """
    aws_config = settings.agent.cloud.aws
    region = region or aws_config.region
    execution_role_arn = execution_role_arn or aws_config.sagemaker_service_role

    return run_script(
        "setup_bedrock_agent_with_code.sh",
        region,
        agent_name,
        foundation_model,
        execution_role_arn
    )


def cleanup_sagemaker_resources(
    region: Optional[str] = None,
    resource_prefix: str = "databy"
) -> Dict[str, Any]:
    """
    Cleanup SageMaker resources (endpoints, configs, models).

    Args:
        region: AWS region (defaults to settings)
        resource_prefix: Prefix to filter resources for deletion

    Returns:
        Script execution result dictionary
    """
    aws_config = settings.agent.cloud.aws
    region = region or aws_config.region

    return run_script("cleanup_sagemaker_resources.sh", region, resource_prefix)


def list_sagemaker_resources(region: Optional[str] = None) -> Dict[str, Any]:
    """
    List all SageMaker and Bedrock resources.

    Args:
        region: AWS region (defaults to settings)

    Returns:
        Script execution result dictionary
    """
    aws_config = settings.agent.cloud.aws
    region = region or aws_config.region

    return run_script("list_sagemaker_resources.sh", region)


def check_aws_configuration() -> Dict[str, Any]:
    """
    Check AWS CLI configuration and credentials.

    Returns:
        Script execution result dictionary
    """
    return run_script("on_start.sh")


def stop_all_services(
    region: Optional[str] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    🚨 EMERGENCY STOP: Stop/delete all AWS services that incur costs.

    This will stop/delete:
    - SageMaker endpoints (actively running)
    - SageMaker training jobs
    - SageMaker transform jobs
    - SageMaker notebook instances
    - SageMaker processing jobs
    - Bedrock provisioned throughput
    - Tagged EC2 instances
    - Lambda provisioned concurrency

    Args:
        region: AWS region (defaults to settings)
        dry_run: If True, only shows what would be stopped without actually stopping

    Returns:
        Script execution result dictionary

    Example:
        >>> # Preview what would be stopped
        >>> result = stop_all_services(dry_run=True)
        >>>
        >>> # Actually stop all services
        >>> result = stop_all_services()

    ⚠️  WARNING: This will immediately stop billable resources!
    """
    aws_config = settings.agent.cloud.aws
    region = region or aws_config.region

    print("=" * 60)
    print("🚨 EMERGENCY STOP: AWS Cost-Incurring Services")
    print("=" * 60)

    if dry_run:
        print("🔍 DRY RUN MODE - No resources will be modified")
    else:
        print("⚠️  WARNING: This will stop ALL billable AWS resources!")
        print("   Resources include: endpoints, training jobs, notebooks, etc.")

    print("=" * 60)

    return run_script("stop_all_services.sh", region, "true" if dry_run else "false")


if __name__ == "__main__":
    # Example usage
    print("=== Checking AWS Configuration ===")
    result = check_aws_configuration()

    if result['success']:
        print("\n=== Listing SageMaker Resources ===")
        list_sagemaker_resources()
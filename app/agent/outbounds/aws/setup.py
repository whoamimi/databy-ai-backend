"""
app.agent.outbounds.aws.setup_bot_playground
"""

import time
import boto3
from botocore.exceptions import ClientError

AWS_SAGEMAKER_SERVICE_ROLE ="sagemaker"
AWS_SAGEMAKER_DOMAIN_ID = 'd-8vejwitupz6k'
AWS_SAGEMAKER_SPACE_NAME = "ai-bot-workspace"
AWS_SAGEMAKER_USER_ROLE = 'arn:aws:iam::120569623166:role/service-role/AmazonSageMaker-ExecutionRole-20250313T010564'


AWS_SAGEMAKER_IMAGE_ARN = 'arn:aws:sagemaker:ap-southeast-2:452832661640:image/datascience-1.0'
AWS_DEFAULT_MODEL_ID = 'ml.t3.medium'

class SageMakerNotebookWorkspace:
    def __init__(self, domain_id: str = AWS_SAGEMAKER_DOMAIN_ID, space_name: str = AWS_SAGEMAKER_SPACE_NAME, sagemaker_arn: str = AWS_SAGEMAKER_USER_ROLE, sagemaker_role: str = AWS_SAGEMAKER_SERVICE_ROLE):

        self.domain_id = domain_id
        self.space_name = space_name
        self.execution_role = sagemaker_arn
        self.sagemaker_role = sagemaker_role

        self.client = boto3.client(self.sagemaker_role)

    @property
    def workspace_config(self):
        return {
            "DomainId": self.domain_id,
            "UserProfileName": self.space_name,
            "UserSettings": {
                'ExecutionRole': self.execution_role,
                'JupyterServerAppSettings': {
                    'DefaultResourceSpec': {
                        'InstanceType': 'system'
                    }
                },
                'KernelGatewayAppSettings': {
                    'DefaultResourceSpec': {
                        'InstanceType': AWS_DEFAULT_MODEL_ID,
                        'SageMakerImageArn': AWS_SAGEMAKER_IMAGE_ARN
                    }
                }
            }
        }

    def create_user_profile(self, max_tries: int = 5, max_wait_time: int = 3):
        """Create user profile for AI bot if it doesn't exist"""

        config = self.workspace_config

        try:
            # Check if profile exists
            response = self.client.describe_user_profile(
                DomainId=config.get("DomainId"),
                UserProfileName=config.get("UserProfileName")
            )
            print(f"✓ User profile '{self.space_name}' already exists")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFound':
                # Create the user profile
                print(f"Creating user profile '{self.space_name}'...")
                response = self.client.create_user_profile(
                    DomainId=config.get("DomainId"),
                    UserProfileName=config.get("UserProfileName"),
                    UserSettings=config.get("UserSettings")
                )

                print(f"✓ User profile created: {response['UserProfileArn']}")

        if response.get("Status", "") != "InService":
            if max_tries == 0:
                raise ValueError("Error Setting up workspace Sagemaker AI Studio.")
            time.sleep(max_wait_time)
            max_tries -= 1
            return self.create_user_profile(max_tries=max_tries)

    def create_space(self, space_name='ai-bot-notebook-space'):
        """Create a space (notebook workspace) for the AI bot"""
        try:
            # Check if space exists
            response = self.client.describe_space(
                DomainId=self.domain_id,
                SpaceName=space_name
            )
            print(f"✓ Space '{space_name}' already exists")
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFound':
                print(f"Creating space '{space_name}'...")
                response = self.client.create_space(
                    DomainId=self.domain_id,
                    SpaceName=space_name,
                    SpaceSettings={
                        'JupyterServerAppSettings': {
                            'DefaultResourceSpec': {
                                'InstanceType': 'system'
                            }
                        }
                    }
                )
                print(f"✓ Space created: {response['SpaceArn']}")
                return response
            else:
                raise

    def create_presigned_url(self, space_name='ai-bot-notebook-space'):
        """Generate presigned URL for the notebook"""

        response = self.client.create_presigned_domain_url(
            DomainId=self.domain_id,
            UserProfileName=self.space_name,
            SessionExpirationDurationInSeconds=43200  # 12 hours
        )
        return response['AuthorizedUrl']

    def execute_notebook(self, notebook_path, parameters=None):
        """Execute a notebook programmatically"""

        import papermill as pm

        output_path = notebook_path.replace('.ipynb', '_output.ipynb')

        pm.execute_notebook(
            notebook_path,
            output_path,
            parameters=parameters or {}
        )

        return output_path

    def start_notebook_instance(self):
        """Start JupyterServer app"""
        try:
            response = self.client.create_app(
                DomainId=self.domain_id,
                UserProfileName=self.space_name,
                AppType='JupyterServer',
                AppName='default'
            )
            print(f"✓ JupyterServer app started")
            return response
        except ClientError as e:
            if 'ResourceInUse' in str(e):
                print(f"✓ JupyterServer app already running")
                return None
            else:
                raise

    def setup_outbound(self):
        """Complete setup: create profile, space, and get URL"""
        print("\n=== Setting up AI Bot SageMaker Workspace ===\n")

        # Step 1: Create user profile
        self.create_user_profile()

        # Step 2: Create space
        self.create_space()

        # Step 3: Start Jupyter app
        self.start_notebook_instance()

        # Step 4: Get presigned URL
        try:
            url = self.create_presigned_url()
            print(f"\n✓ Workspace ready!")
            print(f"\nNotebook URL: {url}")
            return url
        except Exception as e:
            print(f"\n⚠ Could not generate URL yet. Try again in a few seconds.")
            print(f"Error: {e}")
            return None

if __name__ == "__main__":
    # Usage
    workspace = SageMakerNotebookWorkspace()
    workspace.setup_outbound()
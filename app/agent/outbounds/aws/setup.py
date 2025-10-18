"""
app.agent.outbounds.aws.setup

Setup Workspace Config for training models.

Usage:
- Initiate server directly from Hugging Face on SageMaker AI/ML. This is used to fine-tune models in cloud.

"""

import json
import boto3
import sagemaker
from sagemaker.huggingface import HuggingFaceModel
from typing import Literal

from ....utils.settings import settings
from ...core._skeleton import Outbound

aws = settings.agent.cloud.aws

BOTO_CLIENT = aws.boto_client
IAM_ROLE = aws.iam_role
INSTANCE_COUNT = aws.instance_count
INSTANCE_TYPE = aws.instance_type

class AWSageMaker(Outbound):

    def __init__(self):
        self.__role = self.setup_outbound()

    @staticmethod
    def setup_outbound(boto_client = BOTO_CLIENT, role_name=IAM_ROLE):
        try:
            role = sagemaker.get_execution_role()
        except ValueError:
            iam = boto3.client(boto_client)
            role = iam.get_role(RoleName=role_name)["Role"]["Arn"]
        except Exception as e:
            raise e
        return role

    def serve_model(self, hf_model_id: str, hf_task: Literal["text-generation"] = "text-generation", initial_instance_count=INSTANCE_COUNT, instance_type=INSTANCE_TYPE):

        hub = {
            "HF_MODEL_ID": hf_model_id,
            "HF_TASK": hf_task
        }

        hf_model = HuggingFaceModel(
            env=hub,
            role=self.__role,
            transformers_version="4.37",
            pytorch_version="2.1",
            py_version="py310"
        )

        pred = hf_model.deploy(initial_instance_count, instance_type)

        return pred

class AWSBedrockAgentCore(Outbound):
    def setup_outbound(self, **kwargs):
        """ validates handshakes before on fastapi lifespan etc."""
        return super().setup_outbound(**kwargs)

    def inference(self, session_id: str, python_script: str):

        client = boto3.client('bedrock-agentcore', region_name=aws.region)
        response = client.invoke_code_interpreter(
            codeInterpreterIdentifier='aws.codeinterpreter.v1',
            sessionId=session_id,  # Must be 33+ chars
            name='executeCode',
            arguments={
                'code': python_script,
                'language':'python'
            }
        )

        response_body = response['response'].read()
        response_data = json.loads(response_body)
        print("Agent Response:", response_data)

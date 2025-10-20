"""
app.agent.outbounds.aws.setup

AWS Sagemaker AI & Bedrock AgentCore Initiation stack for Gen AI / ML.

"""

import json
import boto3
from sagemaker.huggingface.model import HuggingFaceModel
from typing import Literal

from ....utils.settings import settings
from ...core._skeleton import Outbound

aws = settings.agent.cloud.aws

class AWSageMaker(Outbound):

    def __init__(self, config = aws):
        self.__role = self.get_account()
        self.config = config

    def get_account(self, boto_client = "iam", role_name=None):
        try:
            from sagemaker.session import get_execution_role
            role = get_execution_role()
        except (ValueError, ImportError):
            iam = boto3.client(boto_client)
            if role_name is None:
                role_name = self.config.sagemaker_service_role
            role = iam.get_role(RoleName=role_name)["Role"]["Arn"]
        except Exception as e:
            raise e
        return role

    def setup_outbound(self):
        """ Creates all required endpoints / workbooks on SageMaker AI for agent. """
        pass

    def inference(self, hf_model_id: str, hf_task: Literal["text-generation"] = "text-generation", initial_instance_count=None, instance_type=None):

        # Use config values as defaults
        if initial_instance_count is None:
            initial_instance_count = self.config.instance_count
        if instance_type is None:
            instance_type = self.config.instance_type

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
    """ Hosting AI via endpoint. """

    def __init__(self, region=aws.region):
        self.client = boto3.client('bedrock-agentcore', region_name=region)

    def inference(self, session_id: str, python_script: str):

        response = self.client.invoke_code_interpreter(
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

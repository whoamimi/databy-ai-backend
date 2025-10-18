"""
app.agent.outbounds.aws.inference

Inferencing Tasks with SageMaker AI Model.

Usage:
- Invoke AI Agents personalised to user.

"""

import boto3
from strands import Agent
from strands.models.sagemaker import SageMakerAIModel

from utils.settings import settings

aws_setup = settings.agent.cloud.aws

DEFAULT_OPTIONS = dict(
    max_tokens=100,
    temperature=0.7,
    stream=True
)

DEFAULT_ENDPOINT_CONFIG = {
"endpoint_name": aws_setup.sagemaker_domain_id,
"region_name": aws_setup.region,
}

class AWSagemaker:
    def __init__(self, endpoint_config = DEFAULT_ENDPOINT_CONFIG, payload_config = DEFAULT_OPTIONS):

        self.endpoint = endpoint_config
        self.payload_options = payload_config
        self.model = SageMakerAIModel(self.endpoint, self.payload_options)
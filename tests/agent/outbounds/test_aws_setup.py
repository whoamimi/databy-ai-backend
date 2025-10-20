import io
from unittest import mock

import pytest

from app.agent.outbounds.aws.main import AWSBedrockAgentCore, AWSageMaker
from app.utils.settings import settings


class _TestAWSageMaker(AWSageMaker):
    """Concrete subclass for testing abstract base requirements."""

    def __init__(self):
        # Initialize with config but mock get_account to avoid AWS calls
        self.config = settings.agent.cloud.aws
        self._AWSageMaker__role = "arn:aws:iam::123456789012:role/test-role"

    def get_account_pass(self, **kwargs):
        return kwargs

    def generate(self, **kwargs):
        return {}

    def end_session(self, **kwargs):
        pass

class _TestAWSBedrockAgentCore(AWSBedrockAgentCore):
    """Concrete subclass for testing abstract base requirements."""

    def get_account_pass(self, **kwargs):
        return kwargs

    def setup_outbound(self, **kwargs):
        return kwargs

    def generate(self, **kwargs):
        return {}

    def end_session(self, **kwargs):
        pass


@pytest.fixture()
def mock_huggingface_model(monkeypatch):
    model_mock = mock.MagicMock(name="HuggingFaceModel")
    instance_mock = model_mock.return_value
    instance_mock.deploy.return_value = "endpoint-name"
    monkeypatch.setattr("app.agent.outbounds.aws.main.HuggingFaceModel", model_mock)
    return model_mock, instance_mock


def test_awsagemaker_serve_model_deploys(monkeypatch, mock_huggingface_model):
    model_mock, instance_mock = mock_huggingface_model

    monkeypatch.setattr(
        "app.agent.outbounds.aws.main.sagemaker.get_execution_role",
        lambda: "arn:aws:iam::123456789012:role/test-role",
    )

    manager = _TestAWSageMaker()
    result = manager.inference(
        hf_model_id="distilbert",
        hf_task="text-generation",
        initial_instance_count=1,
        instance_type="ml.t3.medium",
    )

    model_mock.assert_called_once_with(
        env={"HF_MODEL_ID": "distilbert", "HF_TASK": "text-generation"},
        role="arn:aws:iam::123456789012:role/test-role",
        transformers_version="4.37",
        pytorch_version="2.1",
        py_version="py310",
    )
    instance_mock.deploy.assert_called_once_with(1, "ml.t3.medium")
    assert result == "endpoint-name"


def test_awsagemaker_fallbacks_to_iam_when_execution_role_missing(monkeypatch):
    monkeypatch.setattr(
        "app.agent.outbounds.aws.main.sagemaker.get_execution_role",
        mock.Mock(side_effect=ValueError("no execution role")),
    )

    iam_client = mock.MagicMock()
    iam_client.get_role.return_value = {"Role": {"Arn": "arn:aws:iam::000000000000:role/fallback"}}
    monkeypatch.setattr("app.agent.outbounds.aws.main.boto3.client", mock.Mock(return_value=iam_client))

    manager = _TestAWSageMaker()
    assert getattr(manager, "_AWSageMaker__role") == "arn:aws:iam::000000000000:role/fallback"


def test_bedrock_agentcore_invocation(monkeypatch, capsys):
    call_args = {}

    def fake_client(service_name, region_name=None):
        assert service_name == "bedrock-agentcore"

        class DummyClient:
            def invoke_code_interpreter(self, **kwargs):
                call_args.update(kwargs)
                return {"response": io.BytesIO(b"{\"result\": \"ok\"}")}

        return DummyClient()

    monkeypatch.setattr("app.agent.outbounds.aws.main.boto3.client", fake_client)

    agent = _TestAWSBedrockAgentCore()
    agent.inference(session_id="s" * 33, python_script="print('hello')")

    assert call_args["codeInterpreterIdentifier"] == "aws.codeinterpreter.v1"
    assert call_args["sessionId"] == "s" * 33
    assert call_args["arguments"]["code"] == "print('hello')"

    captured = capsys.readouterr()
    assert "Agent Response" in captured.out
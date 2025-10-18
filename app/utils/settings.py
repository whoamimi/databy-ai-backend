"""
app.utils.settings

Application settings and configuration.

"""

import os
import yaml
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Literal

from  ..utils.utils import setup_dev_workspace

if os.getenv("LOG_LEVEL", "DEBUG") == "DEBUG":
    from dotenv import load_dotenv
    load_dotenv('.env')

logger = logging.getLogger("uvicorn")

@dataclass
class ModelConfig:
    dev: str = field(default="", repr=False)
    prod: str = field(default="", repr=False)
    url: str = field(default="", repr=True)
    alt: list[str] = field(default_factory=list, repr=False)

    model_id: str = field(init=False, repr=True)
    source: Literal['dev', 'prod'] = field(default="dev", repr=False)

    def __post_init__(self):
        self.model_id = self.dev if self.source == 'dev' else self.prod

@dataclass
class AgentConfigBuild:
    config_path: Path
    prompt_paths: dict = field(init=False)
    model_paths: dict = field(init=False)
    model_catalogue: dict = field(init=False)
    prompts: dict = field(init=False)

    def __post_init__(self):
        self.prompt_paths = {
            "skeleton": self.config_path / "prompt_skeleton.yaml",
            "awsand": self.config_path / "prompt_awsand.yaml",
            "bigquery": self.config_path / "prompt_bigquery.yaml"
        }

        self.model_paths = {
            "model": self.config_path / "model.yaml",
            "genai": self.config_path / "genai.yaml"
        }

        self.model_catalogue = self.load_agent_stack(str(self.model_paths['genai'])) or {}
        self.prompts = self.load_prompts_from_path(self.prompt_paths['skeleton'])

    @staticmethod
    def load_agent_stack(file_path: str):
        """ Load from `genai.yaml` default models. """

        genai: dict = {}
        try:
            with open(file_path, "r") as f:
                for file in yaml.safe_load(f):
                    genai.update({
                        file.get('model_name'):
                            ModelConfig(
                                dev=file.get('model_id', ''),
                                prod=file.get('model_id', ''),
                                url=file.get('url', None),
                                alt=file.get('alt', None)
                            )
                    })
            return genai
        except Exception as e:
            logger.error(e)

    @staticmethod
    def load_prompts_from_path(file_path: str):

        with open(file_path, "r") as f:
            return yaml.safe_load(f)


@dataclass(frozen=True)
class Sandbox:
    # https://jupyterhub.readthedocs.io/en/stable/tutorial/index.html#working-with-the-jupyterhub-api
    # https://github.com/jupyterhub/jupyterhub?tab=readme-ov-file

    jupyter_url: str = os.getenv("JUPYTER_URL", "")
    jupyter_token: str = os.getenv("JUPYTER_TOKEN", "")
    document_id: str = os.getenv("DOCUMENT_ID", "")
    allow_img_output: bool = os.getenv("ALLOW_IMG_OUTPUT", "False").lower() in ("1", "true", "yes")
    backup_sandbox_server: str = os.getenv("AGENT_SANDBOX_URL", "")

@dataclass(frozen=True)
class AgentServerBuild(Sandbox):
    ollama: str = os.getenv("OLLAMA_HOST_URL", "")
    kaggle_kernel: str = os.getenv("KAGGLE_API_KEY", "")
    kaggle_kernel_server: str = os.getenv("KAGGLE_KERNEL_SERVER", "")

@dataclass(frozen=True)
class AWSConfig:
    # iam role
    region: str = field(default=os.getenv("AWS_DEFAULT_REGION", ""))
    access_key_id: str = field(default=os.getenv("AWS_ACCESS_KEY_ID", ""))
    secret_access_key: str = field(default=os.getenv("AWS_SECRET_ACCESS_KEY", ""))

    sagemaker_domain_id: str = field(default=os.getenv("AWS_SAGEMAKER_DOMAIN_ID", ""))
    s3_bucket: str = field(default=os.getenv("AWS_S3_BUCKET", ""))

    # client setup
    boto_client: str = field(default="iam")
    iam_role: str = field(default="SageMaker")
    # service roles
    sagemaker_service_role: str = field(default="sagemaker")
    bedrock_service_role: str = field(default=os.getenv("AWS_BEDROCK_SERVICE_ROLE", ""))
    bedrock_agencore_service_role: str = field(default="bedrock-agentcore")

    # ec2 instance default setup
    instance_count: int = field(default=1)
    instance_type: str = field(default="ml.t3.medium")

@dataclass(frozen=True)
class GCConfig:
    region: str = field(default=os.getenv("GCLOUD_REGION", ""))
    access_key_id: str = field(default=os.getenv("GCLOUD_ACCESS_KEY_ID", ""))
    secret_access_key: str = field(default=os.getenv("GCLOUD_SECRET_ACCESS_KEY", ""))
    bigquery_domain_id: str = field(default=os.getenv("GCLOUD_BIGQUERY_ENDPOINT", ""))

@dataclass(frozen=True)
class LightningConfig:
    api_key: str = field(default=os.getenv("LIGHTNING_API_KEY", ""))

@dataclass(frozen=True)
class AgentCloud:
    aws: AWSConfig = field(default_factory=AWSConfig)
    gcloud: GCConfig = field(default_factory=GCConfig)
    lightning: LightningConfig = field(default_factory=LightningConfig)

@dataclass(frozen=True)
class AgentDatabase:
    hf_user: str = field(default=os.getenv("HF_USER", ""))
    hf_token: str = field(default=os.getenv("HF_API_KEY", ""))

@dataclass(frozen=True)
class AgentBuild:
    server: AgentServerBuild
    stack: AgentConfigBuild
    cloud: AgentCloud
    database: AgentDatabase

@dataclass
class Settings:
    # FASTAPI CONFIG
    app_title: str = "DataBy API"
    app_description: str = "Autonomous AI agent for complete data lifecycle management"
    app_version: str = "0.1.0"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    docs_endpoint: str = "/api/docs"

    # DEV WORKSPACE
    debug: bool = field(default=os.getenv("DEBUG", "True").lower() in ("1", "true", "yes", "y"))
    log_level: str = field(default=os.getenv("LOG_LEVEL", "DEBUG"))

    # DIR PATHS
    root_dir: Path = field(init=False)
    docs_local_path: Path = field(init=False)
    static_path: Path = field(init=False)
    cli_path: Path = field(init=False)

    # AGENT
    agent: AgentBuild = field(init=False)
    prior_knowledge_dir: Path = field(init=False)

    def __post_init__(self):
        logger.info(f"Root directory initiated as: {Path()}")
        logger.info("Running checks on workspace setup ...")

        self.root_dir = setup_dev_workspace()
        self.docs_local_path = self.root_dir / "docs"
        self.static_path = self.root_dir / "app" / "static"
        self.cli_path = self.root_dir / "app" / "config" / "cli.yaml"

        logger.info(f"Default directory to: {self.root_dir}")

        config_path = self.root_dir / "app" / "agent" / "_config"

        if not config_path.exists() or not config_path.is_dir():
            logger.error("Error loading agent stack from path:", config_path)
            raise FileExistsError

        self.prior_knowledge_dir = self.root_dir / "app" / "agent" / "memory" / "prior_knowledge"

        stack= AgentConfigBuild(config_path=config_path)
        server = AgentServerBuild()
        cloud = AgentCloud()
        db = AgentDatabase()
        self.agent = AgentBuild(
            stack=stack,
            server=server,
            cloud=cloud,
            database=db
        )

    @property
    def root_path(self):
        return str(self.root_dir)

    @property
    def docs_path(self):
        return str(self.docs_local_path)

settings = Settings()
"""
app.utils.settings

Application settings and configuration.

[backlog]
TODO ADD CLI COMMANDS
- AWS Profiling / SETUP
- GCloud Profiling

"""

import os
import yaml
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Literal

from  ..utils.utils import setup_dev_workspace
#from .logger import setup_logging

if os.getenv("LOG_LEVEL", "DEBUG") == "DEBUG":
    from dotenv import load_dotenv

    load_dotenv('.env')

logger = logging.getLogger("uvicorn")

@dataclass
class GenAIConfig:
    model_name: str = field(default="", repr=True)
    model_id: str = field(default="", repr=True)
    url: str = field(default="", repr=True)
    alt: list[str] = field(default_factory=list, repr=False)

@dataclass
class AgentConfigBuild:
    config_path: Path = field(init=True, repr=False)
    prompt_paths: dict = field(init=False, repr=False, default_factory=dict)
    model_paths: dict = field(init=False, repr=False, default_factory=dict)
    model_catalogue: dict = field(init=False)
    prompts: dict = field(init=False)

    def __post_init__(self):
        self.prompt_paths["skeleton"] = self.config_path / "prompt_skeleton.yaml"
        self.prompt_paths["awsand"] = self.config_path / "prompt_awsand.yaml"
        self.prompt_paths["bigquery"] = self.config_path / "prompt_bigquery.yaml"
        self.model_paths["model"] = self.config_path / "model.yaml"

        if os.getenv("DEVELOPMENT", "DEV") != "PROD":
            self.model_paths["genai"] = self.config_path / "dev_genai.yaml"
        else:
            self.model_paths["genai"] = self.config_path / "prod_genai.yaml"

        self.model_catalogue = self.load_agent_stack(str(self.model_paths['genai'])) or {}
        self.prompts = self.load_prompts_from_path(str(self.prompt_paths['skeleton']))

    @staticmethod
    def load_agent_stack(file_path: str):
        """ Load from `genai.yaml` default models. """

        genai: dict = {}
        try:
            with open(file_path, "r") as f:
                for file in yaml.safe_load(f):

                    if model_name := file.get("model_name", None):
                        genai[model_name] = GenAIConfig(
                                model_id=file.get("model_id", ""),
                                model_name=model_name,
                                url=file.get('url', None),
                                alt=file.get('alt', None)
                            )
                    else:
                        raise ValueError(f"Error loading GENAI Configuration. Model Name must be configured for {file}")
            return genai
        except Exception as e:
            logger.error(e)

    @staticmethod
    def load_prompts_from_path(file_path: str):
        """ Loads yaml file type from path. """

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
    # workspace (iam) role setup
    region: str = field(default=os.getenv("AWS_REGION", ""))
    access_key_id: str = field(default=os.getenv("AWS_ACCESS_KEY_ID", ""))
    secret_access_key: str = field(default=os.getenv("AWS_SECRET_ACCESS_KEY", ""))

    # sagemaker setup
    sagemaker_user_id: str = field(default=os.getenv("AWS_SAGEMAKER_USER_ID", ""))
    sagemaker_domain_id: str = field(default=os.getenv("AWS_SAGEMAKER_DOMAIN_ID", ""))
    sagemaker_service_role: str = field(default=os.getenv("AWS_SAGEMAKER_SERVICE_ROLE", ""))

    # bedrock roles
    bedrock_service_role: str = field(default="bedrock")
    bedrock_agentcore_service_role: str = field(default="bedrock-agentcore")

    # DEFAULT INSTANCE SETUP (for model training). Maybe removed in future.
    instance_count: int = field(default=1)
    instance_type: str = field(default="ml.t3.medium")
    s3_bucket: str = field(default=os.getenv("AWS_S3_BUCKET", ""))

@dataclass(frozen=True)
class GCConfig:
    region: str = field(default=os.getenv("GCLOUD_REGION", ""))
    access_key_id: str = field(default=os.getenv("GCLOUD_ACCESS_KEY_ID", ""))
    secret_access_key: str = field(default=os.getenv("GCLOUD_SECRET_ACCESS_KEY", ""))
    bigquery_domain_id: str = field(default=os.getenv("GCLOUD_BIGQUERY_ENDPOINT", ""))

@dataclass(frozen=True)
class LightningConfig:
    user_name: str = field(default=os.getenv("LIGHTNING_USER_NAME", ""))
    api_key: str = field(default=os.getenv("LIGHTNING_API_KEY", ""))
    # STUDIO workspace setup
    studio_name: str = field(default="miplayground")

@dataclass(frozen=True)
class AgentDatabase:
    hf_user: str = field(default=os.getenv("HF_USERNAME", ""))
    hf_token: str = field(default=os.getenv("HF_API_KEY", ""))

@dataclass(frozen=True)
class AgentCloud:
    aws: AWSConfig = field(default_factory=AWSConfig)
    gcloud: GCConfig = field(default_factory=GCConfig)
    lightning: LightningConfig = field(default_factory=LightningConfig)

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

    # DEV WORKSPACE
    debug: bool = field(default=os.getenv("DEBUG", "True").lower() in ("1", "true", "yes", "y"))
    log_level: str = field(default=os.getenv("LOG_LEVEL", "DEBUG"))

    # DIR PATHS
    root_dir: Path = field(init=False)
    static_path: Path = field(init=False)
    template_path: Path = field(init=False)
    cli_path: Path = field(init=False)
    mock_data_path: Path = field(init=False)

    # AGENT
    agent: AgentBuild = field(init=False)
    prior_knowledge_dir: Path = field(init=False)

    def __post_init__(self):
        logger.info(f"Root directory initiated as: {Path()}")
        logger.info("Running checks on workspace setup ...")

        self.root_dir = setup_dev_workspace()
        self.static_path = self.root_dir / "app" / "static"
        self.template_path = self.root_dir / "app" / "templates"
        self.cli_path = self.root_dir / "app" / "config" / "cli.yaml"
        self.mock_data_path = self.root_dir / "data" / "input" / "dirty_cafe_sales.csv"

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

settings = Settings()
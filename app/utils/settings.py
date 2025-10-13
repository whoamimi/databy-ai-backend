"""
app.utils.settings
Application settings and configuration.
"""

import os
import yaml
import logging
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import Literal

load_dotenv('.env')

logger = logging.getLogger("uvicorn")

ROOT_DIR_NAME = 'backend'

def setup_dev_workspace(root_folder_name: str = ROOT_DIR_NAME):
    """ Call in files / notebooks if running workspace in sub-directory path. """

    if Path.cwd().stem == root_folder_name:
        logger.info(f'Path already set to default root directory: {Path.cwd()}')
        return Path.cwd()
    else:
        logger.info('Initialized workspace currently at directory: %s', Path.cwd())

    current = Path().resolve()
    for parent in [current, *current.parents]:
        if parent.name == root_folder_name:
            os.chdir(parent)  # change working directory
            logger.info(f"📂 Working directory set to: {parent}")
            return parent # Exit after changing directory

    raise FileNotFoundError(f"Root folder '{root_folder_name}' cannot be found from current dir: {Path.cwd()} ")

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

    @staticmethod
    def load_agent_generator(file_path: str):
        """ Load from `genai.yaml` default models. """

        genai: dict = {}
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

        logger.info('AgentConfig Stack build loaded!')

        receiver = yield
        while True:
            if receiver and isinstance(receiver, str):
                if model_config := genai.get(receiver, None):
                    yield model_config
            receiver = yield

@dataclass(frozen=True)
class AgentServerBuild:
    # SERVERS
    ollama: str = os.getenv("OLLAMA_HOST_URL", "")
    redis: str = os.getenv("REDIS_HOST_URL","redis://localhost:6379")
    agent_sandbox: str = os.getenv("AGENT_SANDBOX_URL", "")

@dataclass(frozen=True)
class AgentBuild:
    server: AgentServerBuild
    stack: AgentConfigBuild

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
    debug: bool = True
    log_level: str = "DEBUG"

    # DIR PATHS
    root_dir: Path = field(init=False)
    docs_local_path: Path = field(init=False)
    static_path: Path = field(init=False)

    # AGENT
    agent: AgentBuild = field(init=False)
    prior_knowledge_dir: Path = field(init=False)

    def __post_init__(self):
        logger.info(f"Root directory initiated as: {Path()}")
        logger.info("Running checks on workspace setup ...")

        self.root_dir = setup_dev_workspace()
        self.docs_local_path = self.root_dir / "docs"
        self.static_path = self.root_dir / "app" / "static"

        logger.info(f"Default directory to: {self.root_dir}")

        config_path = self.root_dir / "app" / "agent" / "_config"

        if not config_path.exists() or not config_path.is_dir():
            logger.error("Error loading agent stack from path:", config_path)
            raise FileExistsError

        self.prior_knowledge_dir = self.root_dir / "app" / "agent" / "memory" / "prior_knowledge"

        stack= AgentConfigBuild(config_path=config_path)
        server = AgentServerBuild()
        self.agent = AgentBuild(
            stack=stack,
            server=server
        )

    @property
    def root_path(self):
        return str(self.root_dir)

    @property
    def docs_path(self):
        return str(self.docs_local_path)

settings = Settings()
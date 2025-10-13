"""
app.agent.pipelines.data_cleaning

Contains the workflow construction
"""

import pandas as pd

from ...utils.settings import settings
from ..core._skeleton import Spine
from ..core._db import PromptBuilder
from ..core.pipeline import ChainStage

prompts = settings.agent.stack.prompts

try:
    dataSummarizerPrompt = PromptBuilder(**prompts['dataset_summarizer'])
except Exception as e:
    raise e

def main():
    pass

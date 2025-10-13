"""
app.agent.pipelines.records
"""

import pandas as pd
from dataclasses import dataclass, field
from typing import Literal

from ..actions.statistical_methods import *
from ..actions.missing_tools import *
from ..core._skeleton import Actuator

################################ PIPELINE CONFIG
DATA_SUMMARY_COLS = [
    'data_field_name',
    'data_type',
    'missing_count',
    'missing_ratio',
    'unique_count',
]
DATA_SUMMARY_NEW_COLS = ['description']
MIN_SAMPLE_SIZE = 25
MAX_SAMPLE_SIZE = 300

MISSING_TYPES: list = ['MAR', 'MNAR', 'MCAR']
MISSING_VAL_OPERATIONS = Actuator.action_space(workflow_name='statistical_methods')
MISSING_VAL_RESOLVERS = Actuator.action_space(workflow_name='missing_val_resolver')

@dataclass(frozen=True)
class PipelineConfig:
    data_summary_cols = DATA_SUMMARY_COLS + DATA_SUMMARY_NEW_COLS
    min_sample_size = MIN_SAMPLE_SIZE
    max_sample_size = MAX_SAMPLE_SIZE
    missing_val_operations = MISSING_VAL_OPERATIONS
    missing_val_resolvers = MISSING_VAL_RESOLVERS

################################ PIPELINE SCHEMAS / ROLLING WINDOW REPORTS
@dataclass
class Inputs:
    data: pd.DataFrame
    user_input_tags: list | None = field(default=None)
    model_objective: str | None = field(default=None)

@dataclass
class StageExploreReport:
    description: str | None = field(init=False, default=None)
    data_types: dict | None = field(init=False, default=None)
    data_summary: pd.DataFrame | None = field(init=False, default=None)

@dataclass
class MissingColumnReport:
    data_field_name: str
    missing_type: Literal['MAR', 'MNAR', 'MCAR']
    test_method: str
    results: str

@dataclass
class MissingReport:
    missing_report: list[MissingColumnReport] = field(default_factory=list)

@dataclass
class Session(StageExploreReport, MissingReport, Inputs):
    pass

################################ PIPELINE META - ignore - for interal use
@dataclass(frozen=True)
class PipelineStage:
    name: str
    order: int
    description: str

AGENT_CLEAN_PROGRESS = [
    PipelineStage(
        name="Exploring",
        order=1,
        description="Scanning dataset structure, types, and basic statistics to understand its composition."
    ),
    PipelineStage(
        name="Missing data",
        order=2,
        description="Detecting and quantifying missing values; determining if the missingness is random or systematic."
    ),
    PipelineStage(
        name="Outliers",
        order=3,
        description="Identifying abnormal or extreme values using statistical thresholds or model-based detection."
    ),
    PipelineStage(
        name="Dedupe values",
        order=4,
        description="Removing duplicate or nearly identical records to maintain dataset integrity."
    ),
    PipelineStage(
        name="Wrapping up",
        order=5,
        description="Finalizing cleaning process, validating outputs, and summarizing transformations applied."
    ),
]

if __name__ == '__main__':
    session = Session(data=pd.DataFrame())
    print(session)
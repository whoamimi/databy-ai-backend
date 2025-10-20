"""
app.agent.pipelines.records

"""

import pandas as pd
from uuid import UUID
from typing import Literal
from datetime import datetime
from dataclasses import dataclass, field

from ..actions.statistical_methods import *
from ..actions.missing_tools import *
from ..core._skeleton import ActionSpace

################################ PIPELINE CONFIG
DATA_SUMMARY_COLS = [
    'data_field_name',
    'data_type',
    'missing_count',
    'missing_ratio',
    'unique_count',
]

DATA_SUMMARY_NEW_COLS = ['description']
DATA_SUMMARY_TYPE_COLS = ["_data_types", "_data_num_types"]

MIN_SAMPLE_SIZE = 25
MAX_SAMPLE_SIZE = 300

MISSING_TYPES: list = ['MAR', 'MNAR', 'MCAR']
MISSING_VAL_OPERATIONS = ActionSpace.action_space(workflow_name='statistical_methods')
MISSING_VAL_RESOLVERS = ActionSpace.action_space(workflow_name='missing_val_resolver')

ANOMALIES_TYPE: list = ['conditional', 'collective', 'numeric', 'categorical', 'semantic']
ANOMALIES_CAUSES: list = ["instrument", "human", "systematic-bias", "natural-novelty", "adversarial-behavior"]

MISSING_STEPS_HEADER: list = [
    ("1. Classify each missing data value type category."),
    ("2. Return the method to evaluate the missing values that exist for each data field column.")
]
ANOMALIES_STEPS_HEADER: list = [
    ()
]
MAX_DEPTH_ANALYSIS: int = 3

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
    id: UUID
    data: pd.DataFrame
    created_timestamp: datetime
    user_input_tags: list | None = field(default=None)
    model_objective: str | None = field(default=None)

@dataclass
class DataExplorerReport:
    description: str | None = field(init=False, default=None)
    data_types: dict | None = field(init=False, default=None)
    data_summary: pd.DataFrame | None = field(init=False, default=None)

@dataclass
class BaseColumnAnalysis:
    data_field_name: str
    eval_action: str
    cause: str
    description: str

@dataclass
class BaseReport:
    todo: dict = field(default_factory=dict) # next task to be actioned relative to the task
    max_depth: int = field(default=MAX_DEPTH_ANALYSIS)

@dataclass
class MissingColumnReport(BaseColumnAnalysis):
    missing_type: Literal['MAR', 'MNAR', 'MCAR']

@dataclass
class AnomaliesColumnReport(BaseColumnAnalysis):
    anomlies_type: Literal['conditional', 'collective', 'numeric', 'categorical', 'semantic']

    def __post_init__(self):
        if self.cause not in ANOMALIES_CAUSES:
            raise ValueError

@dataclass
class MissingReport(BaseReport):
    report: list[MissingColumnReport] = field(default_factory=list)

    @property
    def to_dataframe(self):
        if len(self.todo) == 0:
            raise ValueError("Cannot proceed with empty dict.")
        else:
            df = pd.DataFrame(self.report)
            df["next_action"] = df["data_field_name"].map(self.todo)
            return df

@dataclass
class AnomaliesReport(BaseReport):
    report: list[AnomaliesColumnReport] = field(default_factory=list)

    @property
    def to_dataframe(self):
        if len(self.todo) == 0:
            raise ValueError("Cannot proceed with empty dict.")
        else:
            df = pd.DataFrame(self.report)
            df["next_action"] = df["data_field_name"].map(self.todo)
            return df

@dataclass
class SessionProfiler(DataExplorerReport, MissingReport, AnomaliesReport, Inputs):
    pass

if __name__ == '__main__':
    from uuid import uuid4

    session = SessionProfiler(id=uuid4(), data=pd.DataFrame(), created_timestamp=datetime.now())
    print(session)
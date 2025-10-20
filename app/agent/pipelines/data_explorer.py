"""
app/agent/pipelines/data_explorer.py

Instruct Callers & helper functions during the data_explorer stage - initiation of any data cleaning session.

TODO: if time allows - change report tracer to Markdown + add utility function to convert markdown to tabular formatting.

"""

from __future__ import annotations

import ollama
import pandas as pd
from dataclasses import dataclass, field

from ...utils.settings import settings
from ..core.pipeline import ChainStage
from ..core._db import PromptBuilder
from ..core._skeleton import Spine
from .records import SessionProfiler, DATA_SUMMARY_COLS, DATA_SUMMARY_NEW_COLS, MIN_SAMPLE_SIZE, DATA_SUMMARY_TYPE_COLS

prompts = settings.agent.stack.prompts

##################### 1. RETRIEVE THE PROMPTS

try:
    describePrompt = PromptBuilder(**prompts['describe_dataset'])
    metaPrompt = PromptBuilder(**prompts['dataset_meta_description'])
    numericTypePrompt = PromptBuilder(**prompts["datatype_numeric"])
    dataTypePrompt = PromptBuilder(**prompts["datatype"])
except Exception as e:
    raise e

##################### 2. DEFINE THE PROMPT / INSTRUCT LLM CALLERS
class DataSummary(Spine, model_name='base', prompt=describePrompt):
    """Generates comprehensive dataset descriptions using LLM analysis."""

    def pre_process(self, data_summary: str):
        """Formats data summary for LLM processing.

        Args:
            data_summary (str): Dataset summary in markdown format

        Returns:
            dict: Formatted data with 'data_table' key
        """
        return {'data_table': data_summary }

class DataMetaSummary(Spine, model_name='base', prompt=metaPrompt):
    """Generates detailed descriptions for individual dataset columns."""

    def pre_process(self, data_description: str = "", data_sample: str = "", data_label: str = "", data_samples: str = ""):
        """Formats column data for LLM analysis.

        Args:
            data_description (str): Overall dataset description
            data_sample (str): Column values in markdown format (legacy parameter)
            data_samples (str): Column values in markdown format
            data_label (str): Column name

        Returns:
            dict: Formatted data with sample values and label
        """
        # Support both old and new parameter names
        samples = data_samples or data_sample
        return {'data_description': data_description, 'data_samples': samples, 'data_label': data_label}

    def run_loop(self, client: ollama.Client, description: str, data_sample: pd.DataFrame):
        """Generates descriptions for all columns in the dataset.

        Args:
            client (ollama.Client): LLM client for inference
            description (str): Overall dataset description
            data_sample (pd.DataFrame): Sample data for analysis

        Returns:
            dict: Mapping of column names to descriptions

        Raises:
            Exception: Re-raises any processing errors
        """
        meta: dict = {}
        try:
            for col_name in data_sample.columns:
                inputs = {
                        'data_description': description,
                        'data_label': col_name,
                        'data_samples': data_sample[col_name].to_markdown(index=False)
                    }

                meta[col_name] = self.run(client=client, **inputs)

            return meta
        except Exception as e:
            raise e

class NumericTyper(Spine, model_name="base", prompt=numericTypePrompt):
    """Classifies numeric columns into semantic types (continuous, binary, ordinal, etc.)."""

    def pre_process(self, **kwargs):
        """Passes through input parameters without modification.

        Args:
            **kwargs: Column data and context

        Returns:
            dict: Input parameters unchanged
        """
        return kwargs

    def post_process(self, response):
        """Validates LLM response for numeric type classification.

        Args:
            response: Raw LLM response

        Returns:
            str: Processed response if valid

        Raises:
            ValueError: If response is not a valid numeric type
        """
        output = super().post_process(response)

        if output.lower() not in ["continous", "binary", "multi", "ordinal", "nominal"]:
            return output
        else:
            # TODO: before building the background error capturer to run in prod real-time, this should prompt the agent to retry output with different seed or reset caches
            raise ValueError

class DataTyper(Spine, model_name="base", prompt=dataTypePrompt):
    """Classifies numeric columns into semantic types (continuous, binary, ordinal, etc.)."""

    def pre_process(self, **kwargs):
        """Passes through input parameters without modification.

        Args:
            **kwargs: Column data and context

        Returns:
            dict: Input parameters unchanged
        """
        return kwargs

    def run_loop(self, client: ollama.Client, data_sample: pd.DataFrame):
        """Generates Data types descriptors in summarizing datasets.

        Args:
            client (ollama.Client): LLM client for inference
            data_sample (pd.DataFrame): Sample data for analysis

        Returns:
            dict: Mapping of column names to descriptions

        Raises:
            Exception: Re-raises any processing errors
        """
        numTyper = NumericTyper()
        meta: dict = {}
        meta_num: dict = {}

        try:
            for col_name in data_sample.columns:
                inputs = {
                        'data_label': col_name,
                        'data_samples': data_sample[col_name].to_markdown(index=False)
                    }

                meta[col_name] = self.run(client=client, **inputs)

                if meta[col_name] == "numeric":
                    meta_num[col_name] = numTyper.run(client=client, **inputs)

            return meta, meta_num
        except Exception as e:
            raise e

##################### 3. Define the Chain Pipeline. Throws an error if `forward` and `validate_stage_output` are not defined.
class DefineDataset(ChainStage):
    """Initial pipeline stage that creates basic dataset statistics and summary."""

    def forward(self, session: "SessionProfiler"): # pyright: ignore[reportUndefinedVariable]
        """Initiates the Dataset exploratory process.

        Args:
            session (session): Current session with dataset

        Returns:
            Result of next pipeline stage

        Raises:
            ValueError: If session.data_summary is None
        """

        if session.data is None:
            raise ValueError("Session Data Summary unavailable. Please define the data_summary in session before proceeding to this stage.")

        # store original datatypes
        session.data_types = session.data.dtypes.to_dict()
        # create summary table
        session.data_summary = pd.DataFrame({
            "data_field_name": session.data.columns,
            "data_type": session.data.dtypes.astype(str),
            "missing_count": session.data.isna().sum().values,
            "missing_ratio": (session.data.isna().sum() / len(session.data)*100).round(5),
            "unique_count": session.data.nunique()
        })
        return super().forward(session)

    def validate_stage_output(self, session: SessionProfiler):
        """Validates required session attributes are present.

        Args:
            session (session): session to validate

        Raises:
            ValueError: If required attributes are None.
        """

        expected_records: list = ['data_summary']

        for attr in expected_records:
            if getattr(session, attr) is None:
                raise ValueError(f'Expected Attribute {attr} either returned None or missing.')

@dataclass
class DescribeDataset(ChainStage):
    """Second pipeline stage that generates LLM descriptions for dataset and columns."""

    dataDescriber: DataSummary = field(default_factory=DataSummary)
    metaDescriber: DataMetaSummary = field(default_factory=DataMetaSummary)

    def forward(self, agent: "GabyAgent", session: SessionProfiler): # pyright: ignore[reportUndefinedVariable]
        """Generates dataset and field-level descriptions using LLM.

        Args:
            agent (GabyAgent): Agent with LLM client and state
            session (session): session with data summary

        Returns:
            Result of next pipeline stage

        Raises:
            ValueError: If session.data_summary is None
        """
        if session.data_summary is None:
            raise ValueError("session Data Summary unavailable. Please define the data_summary in session before proceeding to this stage.")

        # prompt-chain
        session.description = self.dataDescriber.run(agent.client, **{'data_summary': session.data_summary.to_markdown(index=False)})

        if isinstance(session.data_summary, pd.DataFrame):
            sample = session.data.head(MIN_SAMPLE_SIZE)

            meta_description: dict = self.metaDescriber.run_loop(agent.client, description=session.description, data_sample=sample)

            session.data_summary["description"] = session.data_summary.data_field_name.map(meta_description)

        return super().forward(session)

    def validate_stage_output(self, session: SessionProfiler):
        """Validates data summary contains expected columns.

        Args:
            session (session): session to validate

        Raises:
            ValueError: If columns don't match expected structure
        """
        summary_cols: list = DATA_SUMMARY_COLS + DATA_SUMMARY_NEW_COLS

        if session.data_summary is not None:
            if set(session.data_summary.columns) != set(summary_cols):
                missing = set(summary_cols) - set(session.data_summary.columns)
                extra = set(session.data_summary.columns) - set(summary_cols)

                raise ValueError(
                        f"Data summary columns mismatch. "
                        f"Missing: {list(missing) or 'None'}, Extra: {list(extra) or 'None'}"
                    )
        else:
            raise ValueError("Data Summary expected to be returned but is not. In-built problem - pls revise. ")

@dataclass
class DataTyperStage(ChainStage):
    """Pipeline stage for numeric type classification (placeholder implementation)."""

    dataTyper: DataTyper = field(default_factory=DataTyper)

    def forward(self, agent: "GabyAgent", session: session): # type: ignore
        """Execute numeric type classification.

        Args:
            agent (GabyAgent): Agent with LLM client and state
            session (session): session with dataset
        """

        if isinstance(session.data_summary, pd.DataFrame):
            sample = session.data.head(MIN_SAMPLE_SIZE)

            dataTypes, dataNumTypes = self.dataTyper.run_loop(agent.client, data_sample=sample)

            session.data_summary["_data_types"] = session.data_summary["data_field_name"].map(dataTypes)
            session.data_summary["_data_num_types"] = session.data_summary["data_field_name"].map(dataNumTypes)

        return super().forward(session)

    def validate_stage_output(self, session: SessionProfiler):
        """Validate numeric type classification results.

        Args:
            session (session): session to validate
        """

        if missing := [i for i in DATA_SUMMARY_TYPE_COLS if i not in session.data_summary.columns]: # type: ignore
            raise ValueError(f"Error from running pipeline stage. Expected specific data_summary fields after this pipeline stage but detected missing fields: {missing}")


@dataclass
class DataExplorer:
    """ To run, invoke DataExplorerPipeline.pipe.forward(session). """

    pipe: DefineDataset = field(default_factory=DefineDataset, init=False)
    describeData: DescribeDataset = field(default_factory=DescribeDataset, init=False)
    dataType: DataTyperStage = field(default_factory=DataTyperStage, init=False)

    def __post_init__(self):
        self.pipe.set_next_stage(self.describeData).set_next_stage(self.dataType)

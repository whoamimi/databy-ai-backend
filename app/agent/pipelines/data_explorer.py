"""
app/agent/pipelines/data_explorer.py

Instruct Callers & helper functions during the data_explorer stage - initiation of any data cleaning session.
TODO: Datatype changes handlers

"""

import ollama
import pandas as pd
from dataclasses import dataclass, field

from ...utils.settings import settings
from ..core.pipeline import ChainStage
from ..core._db import PromptBuilder
from ..core._skeleton import Spine
from ..main import GabyAgent
from .records import Session, DATA_SUMMARY_COLS, DATA_SUMMARY_NEW_COLS

prompts = settings.agent.stack.prompts

##################### 1. RETRIEVE THE PROMPTS
try:
    describePrompt = PromptBuilder(**prompts['describe_dataset'])
    metaPrompt = PromptBuilder(**prompts['dataset_meta_description'])
except Exception as e:
    raise e


##################### 2. DEFINE THE PROMPT / INSTRUCT LLM CALLERS
class DataSummary(Spine, model_name='base', prompt=describePrompt):
    def pre_process(self, data_summary: str):
        return {'data_table': data_summary }

class DataMetaSummary(Spine, model_name='base', prompt=metaPrompt):
    def pre_process(self, data_sample: str, data_label: str):
        return {'data_sample': data_sample, 'data_label': data_label}

    def run_loop(self, client: ollama.Client, description: str, data_sample: pd.DataFrame):

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

##################### OPTIONAL - for tidying the workflow. May be removed in the future.
@dataclass(frozen=True)
class DataExplorer:
    dataDescriber: DataSummary = field(default_factory=DataSummary)
    metaDescriber: DataMetaSummary = field(default_factory=DataMetaSummary)

##################### 3. Define the Chain Pipeline. Throws an error if `forward` and `validate_stage_output` are not defined.
class DefineDataset(ChainStage, DataExplorer):
    def forward(self, agent: GabyAgent, session: Session):
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

        return super().forward(agent, session)

    def validate_stage_output(self, session: Session):
        expected_records: list = ['data_summary', 'description']
        for attr in expected_records:
            if getattr(session, attr) is None:
                raise ValueError(f'Attribute {attr} returned None and is expected to be completed at this stage. ')

class DescribeDataset(ChainStage, DataExplorer):
    def forward(self, agent: GabyAgent, session: Session):
        # prompt-chain
        session.description = self.dataDescriber.run(agent.client, **{'data_summary': session.data_summary.to_markdown(index=False)})

        if isinstance(session.data_summary, pd.DataFrame):
            meta_description: dict = self.metaDescriber.run_loop(agent.client, description=session.description, data_sample=session.data.head(MIN_SAMPLE_SIZE))
            session.data_summary["description"] = session.data_summary.data_field_name.map(meta_description)

        return super().forward(agent, session)

    def validate_stage_output(self, session: Session):
        summary_cols: list = DATA_SUMMARY_COLS + DATA_SUMMARY_NEW_COLS
        if session.data_summary is not None:
            if set(session.data_summary.columns) != set(summary_cols):
                missing = set(summary_cols) - set(session.data_summary.columns)
                extra = set(session.data_summary.columns) - set(summary_cols)
                raise ValueError(
                        f"Data summary columns mismatch. "
                        f"Missing: {list(missing) or 'None'}, Extra: {list(extra) or 'None'}"
                    )

def setup_pipeline():
    d1 = DefineDataset()
    d2 = DescribeDataset()

    d1.set_next_stage(d2)
    yield d1

if __name__ == "__main__":
    import pandas as pd
    from io import StringIO

    csv_data = StringIO("""
    user_id,name,age,city,purchases,spend,signup_date
    1001,Alex,29,Sydney,5,320.50,2023-05-12
    1002,Jordan,35,Melbourne,3,180.75,2023-07-08
    1003,Riley,42,Perth,,210.00,2022-11-23
    1004,Casey,26,Brisbane,8,540.10,2023-02-19
    1005,Jamie,,Adelaide,2,95.00,2023-08-02
    1006,Taylor,31,Sydney,7,400.00,2023-01-15
    1007,Drew,38,,4,310.80,2022-09-30
    """)

    df = pd.read_csv(csv_data)
    print(df)
    session = Session(data=df)

    #data_cleaning = DataCleaning()
    #data_explore = DataExploration()
    #data_cleaning.set_next_stage(data_explore)
    #heart = HeartMonitor()
    #print(heart.agent)
    #data_cleaning.forward(heart)
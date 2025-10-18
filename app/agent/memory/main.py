"""
app.agent.memory.main

Database warehouse functions.
TODO:

- COMPLETE HUGGING FACE DB MANAGERS
- AWS MANAGERS
- GCLOUD MANAGERS

"""

import io
import boto3
import pandas as pd
from typing import Literal
from datasets import Dataset, load_dataset

from ...utils.settings import settings

PRIOR_KNOWLEDGE_DIR = settings.prior_knowledge_dir
FACT_PATHS = {
    "data_types": PRIOR_KNOWLEDGE_DIR / "data_types.csv",
}
MEMORY_LOBE = Literal[FACT_PATHS]

class LifeCycle:
    """ Kth Session Data Cycler. E.g. stores data in HF (Temp), AWS (Long) & Params to Agent's Bayes Belief Net in aws - TODO: confirm model's serving platform as this is compute heavy.
    """

    __db = settings.agent.database
    __cloud = settings.agent.cloud

    @classmethod
    def _to_huggingface(cls, session_id: str, data):
        repo_id = f"{cls.__db.hf_user}/agent-session-{session_id}"

        dataset = Dataset.from_list(data if isinstance(data, list) else [data])
        dataset.push_to_hub(repo_id, private=True, token=cls.__db.hf_token)

        return f"https://huggingface.co/datasets/{repo_id}"

    @classmethod
    def _from_huggingface(cls, session_id: str):
        repo_id = f"{cls.__db.hf_user}/agent-session-{session_id}"
        return load_dataset(repo_id, token=cls.__db.hf_token)

    @classmethod
    def _to_boto_bucket(cls, session_id: str, data):
        if not cls.__cloud.aws.s3_bucket:
            raise RuntimeError("No S3 bucket configured in settings.agent.s3_bucket")

        # Normalize into DataFrame
        df = pd.DataFrame(data if isinstance(data, list) else [data])

        # Serialize to Parquet in-memory
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False, compression="snappy")
        buffer.seek(0)

        s3 = boto3.client("s3")
        key = f"agents/sessions/{session_id}.parquet"
        s3.put_object(Bucket=cls.__cloud.aws.s3_bucket, Key=key, Body=buffer.getvalue())

        return f"s3://{cls.__cloud.aws.s3_bucket}/{key}"

    @classmethod
    def _from_boto_bucket(cls, session_id: str):
        if not cls.__cloud.aws.s3_bucket:
            raise RuntimeError("No S3 bucket configured in settings.agent.s3_bucket")

        s3 = boto3.client("s3")
        key = f"agents/sessions/{session_id}.parquet"

        # Stream file directly from S3
        obj = s3.get_object(Bucket=cls.__cloud.aws.s3_bucket, Key=key)
        buffer = io.BytesIO(obj["Body"].read())

        df = pd.read_parquet(buffer)
        return df.to_dict(orient="records")

    @classmethod
    def _from_gcloud(cls, session_id: str):
        pass

    @classmethod
    def _to_gcloud(cls, session_id, data):
        return

    @classmethod
    def save(cls, session_id: str, data, service_option: Literal["aws", "hf", "gcloud"] = "hf"):
        if service_option == "hf":
            return cls._to_huggingface(session_id, data)
        elif service_option == "aws":
            return cls._to_boto_bucket(session_id, data)
        elif service_option == "gcloud":
            return cls._to_gcloud(session_id, data)

        else:
            raise ValueError

    @classmethod
    def load(cls, session_id: str, service_option: Literal["aws", "hf", "gcloud"] = "hf"):
        if service_option == "hf":
            return cls._from_huggingface(session_id)
        elif service_option == "aws":
            return cls._from_boto_bucket(session_id)
        elif service_option == "gcloud":
            return cls._from_gcloud(session_id)

        else:
            raise ValueError

class FactTable:
    def __init__(self, load_paths: dict = FACT_PATHS):
        self.load_paths = load_paths
        self.data_types = pd.read_csv(load_paths["data_types"])

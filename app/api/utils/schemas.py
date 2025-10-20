"""
app.api.schemas

API Route Schemas.

Supported Input Methods:
1. file-upload: Direct file upload (CSV, JSON, Excel, Parquet)
2. hugging-face: Hugging Face dataset ID
3. kaggle: Kaggle dataset ID
4. supabase: Supabase connection string + table
5. mongodb: MongoDB connection string + database/collection
6. google-sheets: Google Sheets spreadsheet ID + OAuth token

"""

import pandas as pd
from uuid import uuid4, UUID
from datetime import datetime
from pydantic import BaseModel, Field, model_validator, ConfigDict

from ollama import Message
from typing import Literal, Any

from ...agent.main import GabyWindow
from ...agent.memory.loader import LoadingDock

DataSourceType = Literal[
    "file-upload",
    "hugging-face",
    "kaggle",
    "supabase",
    "mongodb",
    "google-sheets",
    "demo"
]

# BASE MODEL CLASS
class SessionBase(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# FASTAPI INPUT ENDPOINTS
class BaseDataBy(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    ds: pd.DataFrame | None = Field(default=None, exclude=True)

class FileUploadData(BaseDataBy):
    """Data structure for file upload input method."""

    filename: str
    content: bytes | str
    file_type: Literal["csv", "json", "xlsx", "parquet"] = "csv"

    @model_validator(mode="after")
    def load(cls, values):
        try:
            df = LoadingDock.load_upload_file(cls)
            cls.ds = df
        except Exception as e:
            raise ValueError(f"Failed to process file upload: {e}")
        return values

class HuggingFaceData(BaseDataBy):
    """Data structure for Hugging Face dataset input method."""

    dataset_id: str  # e.g., "username/dataset-name"
    config_name: str | None = None

    @model_validator(mode="after")
    def load(cls, values):
        try:
            df = LoadingDock.load_huggingface(cls.dataset_id, cls.config_name)
            cls.ds = df
        except Exception as e:
            raise ValueError(f"Failed to load from Hugging Face: {e}")
        return values

class KaggleData(BaseDataBy):
    """Data structure for Kaggle dataset input method."""

    dataset_id: str  # e.g., "username/dataset-name"
    file_name: str | None = None

    @model_validator(mode="after")
    def load(cls, values):
        try:
            df = LoadingDock.load_kaggle(cls.dataset_id, cls.file_name)
            cls.ds = df
        except Exception as e:
            raise ValueError(f"Failed to load from Kaggle: {e}")
        return values

class SupabaseData(BaseDataBy):
    """Data structure for Supabase connection input method. TODO"""
    connection_string: str  # e.g., "postgresql://user:pass@host:port/db"
    table_name: str
    query: str | None = None

class MongoDBData(BaseDataBy):
    """Data structure for MongoDB connection input method. TODO"""

    connection_string: str  # e.g., "mongodb://user:pass@host:port"
    database: str
    collection: str
    max_sample: int = 100

class GoogleSheetsData(BaseDataBy):
    """Data structure for Google Sheets input method. TODO"""

    url: str
    spreadsheet_id: str  # e.g., "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
    sheet_name: str | None = "Sheet1"
    range: str | None = None  # e.g., "A1:Z1000"
    access_token: str | None = None  # OAuth token from redirect

class DemoTest(BaseDataBy):
    ping: str = Field(default="ping")

    @model_validator(mode="after")
    def load(cls, values):
        """
        Output example:
            {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "timestamp": "2025-10-20T14:05:08.510Z",
                "input_method": "demo",
                "service": "clean",
                "data": {"ping": "ping"},
                "user_input_tags": [
                    "string"
                ],
                "model_objective": "string"
            }
        """
        try:
            import pandas as pd
            from ...utils.settings import settings
            file_path = str(settings.mock_data_path)
            df = pd.read_csv(file_path)
            cls.ds = df
            return values
        except Exception as e:
            raise e

class IncomingData(SessionBase):
    input_method: DataSourceType = Field(default="demo")
    service: Literal["clean", "insights"] = Field(default="insights")
    data: dict[str, Any] | FileUploadData | HuggingFaceData | KaggleData | SupabaseData | MongoDBData | GoogleSheetsData | DemoTest = Field(default={}, init=False)

    @property
    def get_session_window(self):
        return GabyWindow(
                id=self.id,
                data=self.data,
                created_timestamp=self.timestamp
            )

    # post-init validation hook (Pydantic v2)
    @model_validator(mode="after")
    def validate_data_input(self) -> "IncomingData":
        """Automatically validate and parse the `data` field after initialization."""
        try:
            if self.input_method == "file-upload":
                if isinstance(self.data, dict):
                    self.data = FileUploadData(**self.data)
                else:
                    raise ValueError("file-upload expects a dict with 'filename' and 'content'")

            elif self.input_method == "hugging-face":
                if isinstance(self.data, dict):
                    self.data = HuggingFaceData(**self.data)
                else:
                    raise ValueError("hugging-face expects a string (dataset_id) or dict")

            elif self.input_method == "kaggle":
                if isinstance(self.data, dict):
                    self.data = KaggleData(**self.data)
                else:
                    raise ValueError("kaggle expects a string (dataset_id) or dict")

            elif self.input_method == "supabase":
                if isinstance(self.data, dict):
                    self.data = SupabaseData(**self.data)
                else:
                    raise ValueError("supabase expects a dict with 'connection_string' and 'table_name'")

            elif self.input_method == "mongodb":
                if isinstance(self.data, dict):
                    self.data = MongoDBData(**self.data)
                else:
                    raise ValueError("mongodb expects a dict with 'connection_string', 'database', and 'collection'")

            elif self.input_method == "google-sheets":
                if isinstance(self.data, dict):
                    self.data = GoogleSheetsData(**self.data)
                else:
                    raise ValueError("google-sheets expects a string (spreadsheet_id) or dict")
            elif self.input_method == "demo":
                self.data = DemoTest()
            else:
                raise ValueError(f"Unknown input_method: {self.input_method}")

        except Exception as e:
            raise ValueError(f"Data validation failed for {self.input_method}: {str(e)}")

        return self

class CleanForm(IncomingData):
    user_input_tags: list[str] | None = Field(default=None)
    model_objective: str | None = Field(default=None)
    service: str = "clean"

class InsightForm(IncomingData):
    user_input_tags: list[str]
    description: str | None = None
    service: str = "insights"

########## RESPONSE

# sockets
class Output(Message):
    pass

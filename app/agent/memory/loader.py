"""app.agent.memory.loader"""

import io
import os
import base64
import pandas as pd
from datasets import load_dataset, Dataset
from kaggle.api.kaggle_api_extended import KaggleApi


class LoadingDock:
    """Handles all data loading and upload operations for multiple sources."""

    @staticmethod
    def load_upload_file(data: "FileUploadData") -> "FileUploadData":
        """Loads file upload into a DataFrame."""
        content = data.content
        file_type = data.file_type

        # ---- Step 1: Decode content ----
        if isinstance(content, str):
            if content.strip().startswith(("data:", "ey", "UEs")):
                content = base64.b64decode(content)
            else:
                content = content.encode("utf-8")

        buffer = io.BytesIO(content)

        # ---- Step 2: Parse into DataFrame ----
        if file_type == "csv":
            df = pd.read_csv(buffer)
        elif file_type == "json":
            df = pd.read_json(buffer)
        elif file_type == "xlsx":
            df = pd.read_excel(buffer)
        elif file_type == "parquet":
            df = pd.read_parquet(buffer)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        return df

    # ------------------------------------------------------------
    # Hugging Face Integration
    # ------------------------------------------------------------
    @staticmethod
    def upload_huggingface(data: "FileUploadData", session_id: str, dataset_repo_id: str = "demo-test") -> str:
        """Uploads DataFrame to Hugging Face Hub under a session-specific namespace."""
        repo_name = f"{dataset_repo_id}/{session_id}"

        if not isinstance(data.data, pd.DataFrame):
            raise ValueError("Data must be a pandas DataFrame before upload.")

        dataset = Dataset.from_pandas(data.data)
        dataset.push_to_hub(repo_id=repo_name)
        print(f"✅ Dataset pushed to Hugging Face: {repo_name}")
        return repo_name

    @staticmethod
    def load_huggingface(dataset_id: str, config_name: str | None = None) -> pd.DataFrame:
        """Loads a dataset directly from Hugging Face Hub."""
        try:
            ds = load_dataset(dataset_id, config_name=config_name)
            # Prefer 'train' split if available, otherwise use the first one
            split_name = "train" if "train" in ds else list(ds.keys())[0]
            df = ds[split_name].to_pandas()
            print(f"✅ Loaded dataset from Hugging Face: {dataset_id} ({split_name} split)")
            return df
        except Exception as e:
            raise ValueError(f"Failed to load dataset from Hugging Face: {e}")

    # ------------------------------------------------------------
    # Kaggle Integration
    # ------------------------------------------------------------
    @staticmethod
    def load_kaggle(dataset_id: str, file_name: str | None = None) -> pd.DataFrame:
        """Downloads and loads a dataset from Kaggle."""
        try:
            api = KaggleApi()
            api.authenticate()

            download_dir = f"/tmp/kaggle_{dataset_id.replace('/', '_')}"
            os.makedirs(download_dir, exist_ok=True)

            print(f"⬇️ Downloading Kaggle dataset: {dataset_id}")
            api.dataset_download_files(dataset_id, path=download_dir, unzip=True)

            # Auto-detect CSV or fallback
            if file_name:
                file_path = os.path.join(download_dir, file_name)
            else:
                csvs = [f for f in os.listdir(download_dir) if f.endswith(".csv")]
                if not csvs:
                    raise FileNotFoundError("No CSV file found in downloaded Kaggle dataset.")
                file_path = os.path.join(download_dir, csvs[0])

            df = pd.read_csv(file_path)
            print(f"✅ Loaded Kaggle dataset: {dataset_id}")
            return df
        except Exception as e:
            raise ValueError(f"Failed to load dataset from Kaggle: {e}")
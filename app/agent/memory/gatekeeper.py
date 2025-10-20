"""
app.agent.memory.gatekeeper
"""

from huggingface_hub import list_datasets
from kaggle.api.kaggle_api_extended import KaggleApi

KAGGLE_DATA_META = {
    "file_types": ['all', 'csv', 'sqlite', 'json', 'bigQuery'],
    "license_names": ['all', 'cc', 'gpl', 'odb', 'other']
}

HUGGINGFACE_BROWSE_CONFIG = {
    "vision": {
        "tasks": [
            'any-to-any',
            'image-text-to-text',
            'video-text-to-text',
            'visual-document-retrieval',
            'visual-question-answering'
        ],
        "subType": ["multimodal", "other"],
        "keywords": ["vision", "image", "cv", "object detection", "classification"]
    },

    "text": {
        "tasks": [
            'feature-extraction',
            'fill-mask',
            'multiple-choice',
            'question-answering',
            'sentence-similarity',
            'summarization',
            'table-question-answering',
            'table-to-text',
            'text-classification',
            'text-generation',
            'text-ranking',
            'text-retrieval',
            'token-classification',
            'translation',
            'zero-shot-classification'
        ],
        "subType": ["nlp"],
        "keywords": ["text", "nlp", "language", "chat", "transformer"]
    },

    "quantitative": {
        "tasks": [
            'tabular-classification',
            'tabular-regression',
            'tabular-to-text',
            'time-series-forecasting'
        ],
        "subType": ["tabular", "cv"],
        "keywords": ["finance", "stock", "economic", "quant", "business", "banking"]
    }
}

def search_hugging_dataset(domain: str, dataset_name: str | None = None, limit: int = 5):
    """ Searches HF dataset engine. Yields most recent data according to specified domain. """

    try:
        if dataset_name is not None:
            yield from list_datasets(dataset_name=dataset_name)

        if domain_meta := HUGGINGFACE_BROWSE_CONFIG.get(domain, None):
            for i in list_datasets(task_categories=domain_meta.get("tasks", None), limit=limit):
                yield i.id
        else:
            raise ValueError(f"Invalid domain: {domain}")

    except Exception as e:
        raise e


def search_kaggle_dataset(search_meta: str, sort_by: str = "votes", page: int = 1):
    try:
        # Kaggle Acc auth
        api = KaggleApi()
        api.authenticate()

        yield from api.dataset_list(
            search=search_meta,
            sort_by=sort_by,
            page=page
        )
    except Exception as e:
        raise e


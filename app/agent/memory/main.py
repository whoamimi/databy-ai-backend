"""
app.agent.memory.main

Database warehouse functions.
#TODO: optimize + extend
#TODO: Hopfield to accelerate lru-caches? pro is that the larger batches can be streamed for short-term memory and reduce the operations in measuring in real-time i think - TODO: fact check.

"""

import pandas as pd
from typing import Literal
from torch.utils.data import IterableDataset

from ...utils.settings import settings

PRIOR_KNOWLEDGE_DIR = settings.prior_knowledge_dir
FACT_PATHS = {
    "data_types": PRIOR_KNOWLEDGE_DIR / "data_types.csv",
}
MEMORY_LOBE = Literal[FACT_PATHS]

class LifeCycle:
    """ Kth Session Data Cycler. E.g. stores data in HF (Temp), AWS (Long) & Params to Agent's Bayes Belief Net in aws - TODO: confirm model's serving platform as this is compute heavy. """
    pass

class Temporal(IterableDataset):
    """ SentenceTransformer to compare with column values defined in Fact Table. """
    pass

class FactTable:
    def __init__(self, load_paths: dict = FACT_PATHS):
        self.load_paths = load_paths
        self.data_types = pd.read_csv(load_paths["data_types"])

    def load_memory(self, lobe_name: str):
        if not hasattr(self, lobe_name):
            raise ValueError
        else:
            return getattr(self, lobe_name)


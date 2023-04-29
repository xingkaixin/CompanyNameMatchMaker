import math
import re
from pathlib import Path
from typing import List

import addressparser
import companynameparser
import pandas as pd
from loguru import logger
from tqdm import tqdm

from app.client import SearchEngine
from app.utils import load_data

collection_name = "corp"

engine = SearchEngine()


def search_engine_data_init():
    fields = [
        {"name": "corp_id", "type": "string"},
        {
            "name": "corp_cn_name",
            "type": "string",
            "locale": "zh",
            "facet": False,
            "index": True,
        },
    ]
    engine.create_collection(collection_name, fields)
    target_data = load_data("./data/sample/target_corp.csv")
    data = target_data.to_dict("records")
    engine.import_data(collection_name, data)


def main():
    search_engine_data_init()


if __name__ == "__main__":
    main()

import pandas as pd
from loguru import logger


def load_data(load_file_path: str, sep: str = ",") -> pd.DataFrame:
    df = pd.read_csv(load_file_path, sep=sep)
    logger.info(f"{load_file_path} head: \n{df.head()}")
    return df

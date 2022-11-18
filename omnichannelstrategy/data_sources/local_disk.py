import os
import pandas as pd
import pyarrow.parquet as pq


def get_local_parquet(custom_file_path: str=None) -> pd.DataFrame:
    """
    This function loads the local data files (.parquet) from the data file path
    specified as LOCAL_DATA_PATH in the environmental variables (.env).
    This function returns the whole dataset.
    CAUTION: local files could blow up memory space. Recommend setting DATA_SOURCE
    to `bigquery` if BigQuery database is available.
    """

    PATH = os.getenv("LOCAL_DATA_PATH")

    if custom_file_path:
        PATH = custom_file_path

    print(f"Loading local data from {PATH}.")

    local_df = pq.read_table(source=PATH).to_pandas()

    return local_df

### Code Annotations ###
# read one file: pd.read_parquet('file.parquet', engine='pyarrow')

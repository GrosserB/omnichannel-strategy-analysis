import os
import pandas as pd

from omnichannelstrategy.data_sources.big_query import get_bq_data, save_to_bq
from omnichannelstrategy.data_sources.local_disk import get_local_parquet


def load_data(table: str=None,
              rand_sample_size: float=1,
              custom_query: str=None,
              force_local: bool=False,
              custom_file_path: str=None) -> pd.DataFrame:
    """
    This function loads the data either from Google BigQuery or from a local file path.
    The decision follows the environmental variable DATA_SOURCE (see .env file).
    If DATA_SOURCE is set to `bigquery` the data will be loaded from BigQuery.
    If DATA_SOURCE is set to `local` the data will be loaded locally.
    Both paths have to be specified. See get_bq_data or get_local_parquet for further documentation.
    """

    DATA_SOURCE = os.getenv("DATA_SOURCE")

    if DATA_SOURCE == "bigquery":

        return get_bq_data(rand_sample_size=rand_sample_size, custom_query=custom_query, table=table)

    if DATA_SOURCE == 'local' or force_local:

        return get_local_parquet(custom_file_path=custom_file_path)

    raise ValueError("No proper data source specified in local environment (.env file)")


def save_data(df: pd.DataFrame, schema: list=None, target_table: str=None):
    """
    This function either saves the data locally or uploads it to Google BigQuery.
    The decision follows the environmental variable DATA_SOURCE (see .env file).
    If DATA_SOURCE is set to `bigquery` the data will be uploaded to BigQuery.
    If DATA_SOURCE is set to `local` the data will be saved locally.
    IMPORTANT NOTICE: At the moment, the option for local saving is yet to be implemented.
    """

    DATA_SOURCE = os.getenv("DATA_SOURCE")

    if DATA_SOURCE == "bigquery":
        if not target_table:
          return "Nothing happened! Please specify target table because you want to save to BigQuery!"

        return save_to_bq(df, schema=schema, target_table=target_table)

    # if DATA_SOURCE == 'local':
        # here should be function to save parquet files locally
        # currently not implemented and won't be in the future

    raise ValueError("No proper data source specified in local environment (.env file)")

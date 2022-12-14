import os
import pandas as pd

from google.cloud import bigquery
from google.oauth2 import service_account


def get_bq_data(rand_sample_size: float=1,
                custom_query: str=None,
                table: str=None) -> pd.DataFrame:
    """
    This function loads data from Google BigQuery.
    It takes a specified `table` and loads as much data as specified in `rand_sample_size`.
    If no `rand_sample_size` is specified, the whole table will be loaded.
    If a `custom_query` is passed, it gets priority and nullifies the other two parameters.
    The loaded table will be returned as a pandas DataFrame.
    """

    credentials = service_account.Credentials.from_service_account_file(os.getenv("AUTH_JSON_PATH"))

    PROJECT = os.getenv("PROJECT")
    DATASET = os.getenv("DATASET")

    table_ref = f"{PROJECT}.{DATASET}.{table}"

    QUERY = (
    f"""SELECT * FROM `{table_ref}`
    WHERE rand() < {rand_sample_size}""")

    if custom_query:
        QUERY=custom_query

    client = bigquery.Client(credentials=credentials, project=PROJECT)
    query_job = client.query(QUERY)
    rows = query_job.result()
    big_query_df = rows.to_dataframe()

    return big_query_df


def save_to_bq(df: pd.DataFrame, target_table: str, schema: dict=None):
    """
    This function takes a pandas DataFrame and uploads it to Google BigQuery.
    It usually requires a table schema to create the table columns according to their correct data types.
    If the table already exists, it takes the schema from that table.
    """
    credentials = service_account.Credentials.from_service_account_file(os.getenv("AUTH_JSON_PATH"))

    PROJECT = os.getenv("PROJECT")
    DATASET = os.getenv("DATASET")
    table_ref = f"{DATASET}.{target_table}"

    #check if table already exists, then take the schema from there
    try:
      client = bigquery.Client(credentials=credentials, project=PROJECT)
      table = client.get_table(f'{DATASET}.{target_table}')
      schema = [{'name':i.name, 'type':i.field_type} for i in table.schema]
    except:
      print(f"Create Table {table_ref}!")

    df.to_gbq(destination_table=f'{DATASET}.{target_table}',
            project_id=PROJECT,
            chunksize=None,
            if_exists='append',
            credentials=credentials,
            table_schema=schema
            )

    print(f"Saved Dataframe of size {df.shape} to {table_ref}")

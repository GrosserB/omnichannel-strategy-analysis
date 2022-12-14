import pandas as pd
import numpy as np

def table_schema_generator(table_types: pd.Series, force_types: dict={}) -> dict:
  """
  Takes df.dtypes and returns table schema for Google BigQuery upload.
  Data type 'object' will be cast as string (though they might be something else).
  Therefore, custom types can be passed as list for the force_types parameter.
  """

  mask = {np.dtype("O"):'STRING',
          np.dtype("float64"):"FLOAT",
          np.dtype("int64"):"INTEGER",
          # np.dtype("datetime64"):"DATETIME" # does not seem to work, so it has to be specified manually
          }

  SCHEMA = [{'name':column, 'type':mask.get(table_types[column], "STRING")} for column in table_types.index]

  for column in SCHEMA:

    if column['name'] in force_types.keys():

      column['type'] = force_types[column['name']]

  return SCHEMA


# could be implemented DataFrame-wise not on the row-level (used in aggregation)
def substitute_order_value_on_return(row):
  """
  This function takes a row from a pandas DataFrame,
  and sets the column `net_order_value_euros` to 0
  if the column `return_quantity` contains a 1.
  """

  if row["return_quantity"] == 1.0:
      row["net_order_value_euros"] = 0

  return row

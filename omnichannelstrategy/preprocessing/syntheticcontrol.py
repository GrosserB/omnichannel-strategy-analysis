import pandas as pd
from scipy.stats.mstats import winsorize

# Function to Reduce Data to Specific Time Frame before x Quarters and after x Quarter in Relation to the Treatment
def get_before_after_opening_quarters(df: pd.DataFrame,
                                      treatment_area: str,
                                      num_quarter_before: int=12,
                                      num_quarter_after: int=12) -> pd.DataFrame:
    """
    This function takes a treated, aggregated DataFrame and a `treatment_area`.
    It returns the DataFrame with only the postal_codes affected by the `treatment_area` as well as all postal_codes that did not receive any treatment.
    It designates those postal codes to be `control_{treatment_area}` in the `treatment_store` column.
    Thus the `treatment_store` column should only have two unique values: the treatment_area and `control_{treatment_area}`.
    Further it only returns orders that where done x quarters before and y quarters after the opening of the treatment_store.

    Eg. For `Leipzig` and 12 quarters before and after the opening of `Leipzig_store' the DataFrame returned only contains orders within that timeframe
    and the column `treatment_store` only contains the unique values: `Leipzig` and `control_Leipzig`.
    """

    # In separate df, keep only the treatment area and all not-treated-orders
    df_store = df[df['treatment_store'] == treatment_area]
    df_zero = df[df['Treatment'] == 0]

    # then merge them back together
    df = pd.concat([df_store, df_zero], join="inner")

    # only keep orders within the given timeframe of quarters
    df = df[df[f"q_since_open_{treatment_area}"] >= (-1 * num_quarter_before)]
    df = df[df[f"q_since_open_{treatment_area}"] <= (num_quarter_after)]

    # designate all orders that are not treatment_area, to be control group for that area
    # eg. for Leipzig, all orders that are not in Leipzig reveice tag "control_Leipzig" in column "treatment_store"
    df.loc[(df.treatment_store != treatment_area),'treatment_store']=f'control_{treatment_area}'

    return df

# Function for Transformation of DataFrame in Preparation for Applying Synthetic Control
def scm_preprocessing(df_input: pd.DataFrame,
                      treatment_area: str,
                      dropna: bool=True,
                      num_quarter_before=12,
                      num_quarter_after=12,
                      earliest_quarter='2013Q2',
                      additional_columns:dict={}) -> pd.DataFrame:
    """
    This function takes a treated and aggregated dataframe, a treatment_area (eg. Leipzig),
    the number of quarters before and after the opening of the store (=treatment), which will be returned as a new column `q_since_observation`.
    It aggregates all postal codes that are assigned to have received treatment by the treatment_area to one single postal code and designates this as the treatment_area
    The function also takes additional columns and how they should be aggregated for the treatment_area. This is a way of introducing more flexibility to the functionality.
    With using `get_before_after_opening_quarters` the resulting DataFrame will only contain data for the treated area and non-treated areas.
    """

    df = df_input.copy()

    q_since_open_treatment = f'q_since_open_{treatment_area}'

    # 0. Drop NaN
    ## drop postal codes where there is not latitude/longitude because they might be wrong but be assigned to control group "Non_Store"
    if dropna:
        df.dropna(subset=["latitude"], inplace=True)

    # 1. Additional Outcome Variables
    ## create earliest `order_value` as constant variable
    temp_df = df[df['year_quarter'] == earliest_quarter][['shipping_post_code', 'order_value']].reset_index(drop=True)
    temp_df = temp_df.rename(columns={'order_value': f'order_value_{earliest_quarter}'})
    df = pd.merge(df, temp_df, how='inner', on='shipping_post_code')

    ## create return_rate outcome variable
    df['return_rate'] = df['number_of_returned_items']/df['number_of_items']

    ## need to fill nan because of division by 0
    df.return_rate.fillna(0.0, inplace=True)

    # 2. Treatment, Control Groups and Time Frame of Analysis/Observation
    ## keep only treated area and designate control group (all other areas where treatment=0, therefore also early stores)
    ## keep only within certain time frame (x quarters before and y quarters after store opening)
    df = get_before_after_opening_quarters(df, treatment_area=treatment_area, num_quarter_before=num_quarter_before, num_quarter_after=num_quarter_after)

    # 3. Shipping Post Code of Treatment
    ## replace shipping post code with treatment_store if treatment_store == treatment_area
    df.loc[df['treatment_store'] == treatment_area, "shipping_post_code"] = treatment_area

    print(f"Number of postal codes aggregated: {df[df['treatment_store'] == treatment_area].shape[0]} / {df[q_since_open_treatment].nunique()} = {df[df['treatment_store'] == treatment_area].shape[0] / df[q_since_open_treatment].nunique()}")

    ## Reduce imbalance by combining postal codes of treatment_area (necessary for SCM)
    ## eg. all postal codes from Leipzip will be combined to be one postal code: Leipzig
    ## this reduces num of postal codes for treatment_area from several 1000 to num_quarters
    aggregation_log = {'order_value' : 'mean',
                        'number_of_returned_items': 'mean',
                        'number_of_orders': 'mean',
                        'number_of_items': 'mean',
                        q_since_open_treatment: 'first',
                        'Group':'first',
                        'credit_score':'mean',
                        'population_density_per_sqkm':'mean',
                        'return_rate':'mean',
                        f'order_value_{earliest_quarter}':'mean'
                        }

    ## add additional columns and their operation (mean, sum etc.) to be added to aggregation (this will keep those columns)
    ## useful for experiments with different engineered features not always hardcode them into the function
    if additional_columns != {}:
        for column, aggregation_operation in additional_columns.items():
            aggregation_log[column] = aggregation_operation

    df = df.groupby(['shipping_post_code', 'year_quarter'], dropna=False).aggregate(aggregation_log).reset_index()


    # 4. Transform Time Frame
    ## transforms q_since_open column to be positive (necessary for SCM), outcome column will be called "q_since_observation"
    ## this will be the time column used in SCM (see year in german unification example)
    min_quarter = ((-1) * df[q_since_open_treatment].min())
    df['q_since_observation'] = df[q_since_open_treatment] + min_quarter

    # 5. Column Selection
    ## keep interesting / working / necessary columns and/or reorder existing ones
    keep_columns = ['shipping_post_code', 'q_since_observation', 'order_value','number_of_returned_items','number_of_orders', 'number_of_items', 'return_rate', 'credit_score', f'order_value_{earliest_quarter}', 'population_density_per_sqkm', 'Group']

    if additional_columns != {}:
        keep_columns.extend(additional_columns.keys())

    df = df[keep_columns]

    # 6. Sorting
    ## sort dataframe for SCM analysis
    df.sort_values(by=['shipping_post_code', 'q_since_observation'], axis=0, inplace=True)

    return df

def scm_scaler(df_input: pd.DataFrame, column_scaling: dict={}, column_winsor: dict={}) -> pd.DataFrame:
  """
  Take DataFrame and dictionary of column names (keys) and method for scaling them (values).
  For each column the dictionary must contain a list of scaling methods. The following methods are valid inputs: `minmax`, `mean_normal`, `standard`.
  The function also takes a dictionary, if the scaled columns should also be winsorised. The dictionary keys are the column names as well as
  """

  df = df_input.copy()

  for column, scaling in column_scaling.items():
    for scaler in scaling:
      if scaler == 'minmax':
        df[f'{column}_minmax'] = (df[column] - df[column].min()) / (df[column].max() - df[column].min())

      if scaler == 'meannormal':
        df[f'{column}_meannormal'] = (df[column] - df[column].mean()) / (df[column].max() - df[column].min())

      if scaler == 'standard':
        df[f'{column}_standard'] = (df[column] - df[column].mean()) / df[column].std()

      if column in column_winsor.keys():
        limits = column_winsor.get(column, [0.05, 0.05])
        df[f'{column}_{scaler}_winsor'] = winsorize(df[f'{column}_{scaler}'], limits=limits)

  return df

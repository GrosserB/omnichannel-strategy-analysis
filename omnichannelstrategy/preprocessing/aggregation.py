import numpy as np
import pandas as pd

# for `df.complete` method?
# import janitor

from multichannelstrategy.main.utils import substitute_order_value_on_return

# Function to Aggregate the Treated Data over Postal Code and Order Date Quarter
def aggregate_treated_df(df: pd.DataFrame, df_stores: pd.DataFrame) -> pd.DataFrame:
    """
    This function takes a dataframe as input and aggregates it over `shipping_post_code` and `year_quarter`.
    It also ensures a balanced panel, i.e. that for each combination of `shipping_post_code` and `year_quarter` there are rows,
    even if there is not data in them (this is needed for further analytical methods).
    The function takes a second DataFrame that has to contain the data of the stores for which the time difference should be calculated.
    """

    # 1 Drop Obsolete Columns & Rows
    ## drop obsolete column
    df = df.drop(columns=['Treatment_store_2'])

    ## drop orders that are too close to Swiss border
    df = df[df['Treatment_store_1'] != "Schaffhausen"]
    df = df[df['Treatment_store_1'] != "Basel"]
    df = df[df['Treatment_store_1'] != "Zurich"]

    # 2 Time-Invariant Data
    ## create auxiliary dataframe with all columns that are time-invariant
    df_temp = df[['shipping_post_code', 'Treatment_store_opening_date', 'Treatment_store_distance', 'Treatment_store_1', 'Treatment', 'Group']]
    df_temp = df_temp.drop_duplicates().reset_index(drop=True)
    assert pd.Series(df_temp["shipping_post_code"]).is_unique # checks if each shipping post code exists only once - true

    # 3 Balanced Panel - Complete Dataset
    ## ensure balanced panel by shipping_post_code and year_quarter
    df = df.complete("shipping_post_code", "year_quarter", sort=True)

    # 4 Adjustment of Order Value
    ## sets net_order_value to 0 if return=1
    df = df.apply(lambda row: substitute_order_value_on_return(row), axis=1)

    # 5 Time-Variant Data = Aggregation of Post Code and Quarter
    ## aggregate the time-variant items & merge with df_temp to get the time-invariant items back
    df = df.groupby(['shipping_post_code', 'year_quarter'], dropna=False).aggregate({'return_quantity': 'sum',
                                                                            'net_order_value_euros' : 'sum',
                                                                            'order_number': 'nunique',
                                                                            'item_line_number': 'count',
                                                                            'Post': 'max'}).reset_index()
    # 6 Merge Time-Variant and Time-Invariant
    ## merge back time-invariant_df
    df = pd.merge(df, df_temp, how='left', on='shipping_post_code')

    # 7 Clean Up
    ## rename columns to better represent their data values and what they should be interpreted as
    df = df.rename(columns={"net_order_value_euros": "order_value",
                            "Treatment_store_1": 'treatment_store',
                            "order_number": "number_of_orders",
                            "return_quantity": "number_of_returned_items",
                            "item_line_number": "number_of_items",
                            'Treatment_store_distance':'treatment_store_distance',
                            'Treatment_store_opening_date':'treatment_store_opening_date'
                            })

    # 8 Time Difference
    ## add difference between store openings and order date
    df = add_time_difference(df, df_stores)

    ## drop obsolete column after adding time diff
    df.drop(columns=["year_quarter_dt"], inplace=True)

    return df


# Function for Calculating Time Difference between Order Date and Store Opening Data (used in Aggregation)
def add_time_difference(df_input: pd.DataFrame, df_stores: pd.DataFrame) -> pd.DataFrame:
    """
    This function takes a dataframe as input and calculates the time difference between the opening of a store and an order quarter.
    It returns the dataframe with one additional column for each store. Those columns contain the time difference in days.
    The second argument is the dataframe containing the store information for calculating the time differences.
    """

    df = df_input.copy()

    # 1 Store Opening Dates
    ## load store opening dates from df_stores
    store_openings = df_stores.opening_date.str.split("/").apply(lambda x: '-'.join(reversed(x)))
    store_openings = {idx:[store_openings.loc[idx]] for idx in store_openings.index}

    store_column_list = []

    # 2 New Columns for Time Difference
    ## create new columns for time diff
    ## store `q_since_open_{city}` column name in store_column_name for easier access
    for city in store_openings.keys():
        store_column_name = f"q_since_open_{city}"
        df[store_column_name] = ""
        store_column_list.append(store_column_name)
    df['year_quarter_dt'] = np.nan;

    # 3 Transformation Into Quarters
    ## transform year_quarter into Period-Q object (for subtraction)
    df['year_quarter_dt'] = pd.PeriodIndex(df.year_quarter, freq='Q')

    df_quarters = pd.DataFrame.from_dict(store_openings).T.reset_index()
    df_quarters.columns = ["city", "date"]

    df_quarters['quarter'] = pd.PeriodIndex(df_quarters.date, freq='Q')
    df_quarters = df_quarters.drop("date", axis=1)

    # 4 Calculation of Time Difference
    ## for each city in df_stores (stored in store_column_list) calculate time diff
    for col in store_column_list:
        city_name = col.split('_')[-1]
        city_q = df_quarters[df_quarters.city == city_name].quarter.iloc[0]
        df[col] = df.year_quarter_dt - city_q

    ## some necessary transformation of the data type
    for col in store_column_list:
        df[col] = df[col].apply(lambda x: x.n)

    return df

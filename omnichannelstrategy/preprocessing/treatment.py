import numpy as np
import pandas as pd

from datetime import date


def treat_control_assignment(row, df_stores: pd.DataFrame, treat_dist: int=50, country_list: list=["DE"], drop_columns: list=[], early_store_date=[2013,4,1]):
    """
    This function assingns to each order its "treatment status" (i.e. whether the order belongs to the treatment or control group).
    The treatment status is based on the distance to a store.
    Based on the treatment status (or lack thereof), it also marks rows that are to be dropped in a second step.
    Finally, based on the date of the order and the opening date of a close-by store, each order is marked as Pre- or Post treatment.

    Input parameters of the function are:
    (1) treat_dist = the maximum distance to a store up until which an order is still considered to be treated;
    (2) country_list = a list of countries to be included (DE, AT, CH)
    """

    store_opening_dates = pd.to_datetime(df_stores.opening_date, format="%d/%m/%Y").dt.date
    store_opening_date_dict = {idx:store_opening_dates.loc[idx] for idx in store_opening_dates.index}

    if row['webshop_country'] in country_list:

        # For each store where distance < treat_dist, asssign treatment
        for store in store_opening_date_dict.keys():
            col_name = f'dist_{store}'
            if col_name not in drop_columns:
              if row[col_name] < treat_dist:
                  row['Treatment'] = 1
                  if row['Treatment_store_1'] == "":
                      row['Treatment_store_1'] = store
                  else:
                      row['Treatment_store_2'] = store

        # If two stores in vincinity to each other take the closer one
        if row['Treatment_store_2'] != "":
            store_1 = row['Treatment_store_1']
            store_2 = row['Treatment_store_2']

            dist_store_1 = row[f'dist_{store_1}']
            dist_store_2 = row[f'dist_{store_2}']

            if dist_store_1 <= dist_store_2:
                row['Treatment_store_2'] = ""
            else:
                row['Treatment_store_1'] = row['Treatment_store_2']
                row['Treatment_store_2']= ""


        # Assign (Control) Group
        ## Put treatment status of all pre-existing stores to zero
        if row['Treatment'] == 1 and store_opening_date_dict[row['Treatment_store_1']] < date(*early_store_date):
                row['Treatment'] = 0
                row['Group'] = "Early_Store"

        # Put treatment status of all non-treated locations to zero
        elif np.isnan(row['Treatment']):
            row['Treatment'] = 0
            row['Group'] = "Non_Store"

        else:
            assert row['Treatment'] == 1, "Only Treatment Stores in DE should not have been dealt with at this point"
            row['Group'] = "Treatment_Store"

        # Pre-Post
        for store in store_opening_date_dict.keys():
            if row['Treatment_store_1'] == store:
                row['Treatment_store_opening_date'] = pd.to_datetime(store_opening_date_dict[store]).to_period('Q') # Quarterly Date

                if row['Treatment'] == 0:
                    row['non_treated_store_distance'] = row[f"dist_{store}"]
                    row['Treatment_store_distance'] = np.nan
                else:
                    row['Treatment_store_distance'] = row[f"dist_{store}"]
                    row['non_treated_store_distance'] = np.nan

                if row['order_date'] > store_opening_date_dict[store]:
                    row['Post'] = 1
                else:
                    row['Post'] = 0

        # If not Post, then is pre
        if np.isnan(row['Post']):
            row['Post'] = 0

    # This drops all non-German locations
    else:
        row['ToBeDropped'] = 1

    return row



def apply_treat_control(df: pd.DataFrame, df_stores: pd.DataFrame, treat_dist: int=50, early_store_date: list=[2013,4,1], drop_cities: list=[]) -> pd.DataFrame:
    """
    This function takes a pandas DataFrame and applies the `treat_control_assigment` function to it.
    Beforehand, it does some light preprocessing. Both functions should be thought as a set.
    """

    # Drop all columns specified (could be stores in cities with multiple stores)
    drop_columns = [f'dit_{city}' for city in drop_cities]
    for column in drop_columns:
        if column in df.columns:
            df = df.drop([column], axis=1)

    # Create new columns
    df['Treatment'] = np.nan
    df['Post'] = np.nan
    df['Treatment_store_1'] = ""
    df['Treatment_store_2'] = ""
    df['Treatment_store_1'].astype(str)
    df['Treatment_store_2'].astype(str)
    df['ToBeDropped'] = 0
    df['Treatment_store_opening_date'] = np.nan;
    df['Treatment_store_distance'] = np.nan;
    df['Treatment_store_distance'].astype(float)
    df['non_treated_store_distance'] = np.nan
    df['non_treated_store_distance'].astype(float)
    df['Group'] = "";

    # apply treat_control_assignment
    df = df.apply(lambda row: treat_control_assignment(row=row, df_stores=df_stores, treat_dist=treat_dist, drop_columns=drop_columns, early_store_date=early_store_date), axis=1)

    # Drop ToBeDropped rows (i.e. non-DE-orders) and remove column (no useful information any longer)
    df = df[df['ToBeDropped'] == 0]
    df.drop(columns=['ToBeDropped'], inplace=True)

    # ensure correct order of columns (for saving)
    base_columns = ['order_number', 'item_line_number', 'webshop_country', 'order_date',
       'shipping_post_code', 'net_order_value_euros', 'return_quantity',
       'year_quarter', 'year_month']

    dist_columns = [column for column in df.columns if column.startswith('dist_')]
    # use this weird expression to be applicable to any number of columns with any city names

    treat_columns = ['Post', 'Treatment', 'Group',
          'Treatment_store_1', 'Treatment_store_2', 'Treatment_store_distance',
          'non_treated_store_distance', 'Treatment_store_opening_date']

    base_columns.extend(dist_columns)
    base_columns.extend(treat_columns)

    df = df[base_columns]

    return df

import pandas as pd
import numpy as np

from sklearn.neighbors import NearestNeighbors

def did_preprocessing(df_input: pd.DataFrame,
                      first_quarter='2013Q2',
                      # treatment_area: str,
                      dropna: bool=True,
                      num_quarter_before=12,
                      num_quarter_after=12,
                      num_neighbors=1) -> pd.DataFrame:

  df = df_input.copy()

  # # 0. Drop NaN
  # ## drop postal codes where there is not latitude/longitude because they might be wrong but be assigned to control group "Non_Store"
  if dropna:
      df.dropna(subset=["latitude"], inplace=True)

  # 1. Additional Outcome Variables
  ## create 2015Q1 `order_value` as constant variable
  temp_df = df[df['year_quarter'] == first_quarter][['shipping_post_code', 'order_value']].reset_index(drop=True)
  temp_df = temp_df.rename(columns={'order_value': 'order_value_firstQ'})
  df = pd.merge(df, temp_df, how='left', on='shipping_post_code')


  # 2. Distance Buckets
  ## add distance buckets to treatment_store_distance
  bucket_borders = [0, 10, 20, 30, 40, 50]
  df.treatment_store_distance.fillna(-99, inplace=True)

  for idx, bucket_end in enumerate(bucket_borders):
    if idx != 0:
      bucket_start = bucket_borders[idx-1]
      df[f'dist_{bucket_start}_{bucket_end}km'] = df.treatment_store_distance.apply(lambda dist: 1 if dist >= bucket_start and dist < bucket_end else 0)


  # 3. Quantiles
  # Put in order_value_firstQ x Time-FE
  # Compute quintiles of order_value_firstQ (this explains 70% of the corss-sectional variation)

  # order_value_firstQ
  ####################
  temp_df = df[df['year_quarter'] == first_quarter][['shipping_post_code', 'order_value_firstQ']] #, 'population_density_per_sqkm'
  temp_df['order_value_firstQ_q25'] = temp_df.quantile([.25], axis=0).iloc[0,0]
  temp_df['order_value_firstQ_q50'] = temp_df.quantile([.50], axis=0).iloc[0,0]
  temp_df['order_value_firstQ_q75'] = temp_df.quantile([.75], axis=0).iloc[0,0]
  temp_df['quantile_order_value_firstQ'] = np.nan

  def get_quantile_order_value(row):

      if row['order_value_firstQ'] <= row['order_value_firstQ_q25']:
          row['quantile_order_value_firstQ'] = 1
      elif row['order_value_firstQ'] <= row['order_value_firstQ_q50'] and row['order_value_firstQ'] > row['order_value_firstQ_q25']:
          row['quantile_order_value_firstQ'] = 2
      elif row['order_value_firstQ'] <= row['order_value_firstQ_q75'] and row['order_value_firstQ'] > row['order_value_firstQ_q50']:
          row['quantile_order_value_firstQ'] = 3
      else:
          row['quantile_order_value_firstQ'] = 4

      return row

  temp_df = temp_df.apply(lambda row: get_quantile_order_value(row), axis=1)
  temp_df = temp_df.loc[:, ['shipping_post_code', 'quantile_order_value_firstQ']]
  df = pd.merge(df, temp_df, how='left', left_on='shipping_post_code', right_on='shipping_post_code')

  return df


def get_before_after_opening_quarters(df, treatment_area, num_quarter_before = 12, num_quarter_after = 12):
    '''function to get the number of quarters before/after store opening for each store and each delivery'''

    # In separate df, keep only the treatment area
    df_store = df[df['treatment_store'] == treatment_area]
    df_zero = df[df['Treatment'] == 0]

    df = pd.concat([df_store, df_zero], join="inner")

    df = df[df[f"q_since_open_{treatment_area}"] >= (-1 * num_quarter_before)]
    df = df[df[f"q_since_open_{treatment_area}"] <= (num_quarter_after)]

    df.loc[(df.treatment_store != treatment_area),'treatment_store']=f'control_{treatment_area}'

    return df


def get_nearest_neighbors(input_df, num_neighbors=1):

    df = input_df

    # Keep just one observations per shipping_post_code
    #df_obs = df[df['year_quarter']=="2015Q1"]
    earliest_yq = df.year_quarter.min()
    df_obs = df[df['year_quarter']==earliest_yq]

    assert df_obs.duplicated(subset=['shipping_post_code']).sum() == 0 # no duplicates
    df_obs = df_obs[['Treatment', 'credit_score', 'population_density_per_sqkm', 'order_value_firstQ']]
    Control_df = df_obs[df_obs['Treatment'] == 0].loc[:,df_obs.columns != 'Treatment']
    Treatment_df = df_obs[df_obs['Treatment'] == 1].loc[:,df_obs.columns != 'Treatment']

    # Determine Nearest Neighbors
    neigh = NearestNeighbors()
    neigh.fit(Control_df)

    if num_neighbors == 1:
        neighbor_index = neigh.kneighbors(X=Treatment_df, n_neighbors=1, return_distance=False)[:,0] # If number of neighbors is 1

    else:
        neighbor_index = neigh.kneighbors(X=Treatment_df, n_neighbors=num_neighbors, return_distance=False).flatten()

    # Create df with the matched control rows
    result_df = Control_df.iloc[neighbor_index].reset_index()
    result_df = result_df.drop(columns=['credit_score', 'population_density_per_sqkm', 'order_value_firstQ'])

    # Get the shipping codes of the matched control rows
    df_Control_Shipping_Code = pd.merge(result_df, df, how='left', left_on='index', right_index=True)
    df_Control_Shipping_Code = df_Control_Shipping_Code[['shipping_post_code']]

    # Merge them back to the main dataset
    df_Matched_Controls = pd.merge(df_Control_Shipping_Code, df, how='left', left_on='shipping_post_code', right_on='shipping_post_code')
    df_Matched_Controls['Group'] = "Matched_Control"
    assert len(df_Matched_Controls.columns) == len(df.columns)
    df = pd.concat([df, df_Matched_Controls]).reset_index()

    return df


def generate_regression_city_df(input_df: pd.DataFrame,
                                treatment_area: pd.DataFrame='city1') ->pd.DataFrame:

  # Create df_city
  df_city = input_df[(input_df.treatment_store == treatment_area) | (input_df.treatment_store == f"control_{treatment_area}")]

  # Keep Treatment and Matched Controls
  df_city = df_city[(df_city.Treatment == 1) | (df_city.Group == "Matched_Control")].reset_index(drop=True) #Matched_Control

  # add post column, we use apply on row because it transfers the datatypes of the whole dataset (needed for statsmodels)
  def post_generator(row):
    row['Post'] = 1 if row[f'q_since_open_{treatment_area}'] > 0 else 0
    return row

  df_city = df_city.apply(lambda row: post_generator(row), axis=1)

  df_city['log_order_value'] = np.log((df_city['order_value']+1))
  df_city['Treatment_x_Post']= df_city['Treatment'] * df_city['Post']

  df_city['dist_0_10km_x_Post'] = df_city['dist_0_10km'] * df_city['Post']
  df_city['dist_10_20km_x_Post'] = df_city['dist_10_20km'] * df_city['Post']
  df_city['dist_20_30km_x_Post'] = df_city['dist_20_30km'] * df_city['Post']
  df_city['dist_30_40km_x_Post'] = df_city['dist_30_40km'] * df_city['Post']
  df_city['dist_40_50km_x_Post'] = df_city['dist_40_50km'] * df_city['Post']

  return df_city


def prepare_did_export_for_R(df_input, treatment_area_list, cohort_date_anchor):

  df = df_input.copy()

  # 1. Cohort Date
  ## cohort date anchor (center opening date anchor on opening date of specific treatment area)
  df['Count_date'] = df[f'q_since_open_{cohort_date_anchor}'] - 12

  ## create dictionary to calculate differences of opening dates compared to cohort date anchor
  cohort_date_city_dict = {treatment_area: (df['Count_date'] - df[f'q_since_open_{treatment_area}']).value_counts().index[0] for treatment_area in treatment_area_list}

  ## create new column that contains differences of opening dates to anchored cohort date (use cohort date dictionary)
  df['cohort_date'] = df.treatment_store.apply(lambda treatment_area: cohort_date_city_dict.get(treatment_area,0) )

  # 2. Numeric Identifier
  ## create numeric identifier
  df['id'] = df['shipping_post_code'].rank(method='dense').astype(int)

  # 3. Log Transformation
  ## transform order_value to log
  df['log_order_value'] = np.log((df['order_value']+1))

  # 4. Cleaning
  ## reduce number of columns
  df = df[['log_order_value','order_value', 'Count_date', 'id', 'cohort_date', 'Treatment', 'credit_score', 'population_density_per_sqkm', 'order_value_firstQ']]

  ## sort values
  df = df.sort_values(['id', 'Count_date'],ascending = [True, True]).reset_index(drop=True)

  return df

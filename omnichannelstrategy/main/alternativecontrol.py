import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.neighbors import NearestNeighbors
from omnichannelstrategy.preprocessing.syntheticcontrol import get_before_after_opening_quarters

def get_nearest_neigbors(df_input, num_neighbors=1, earliest_qt_column='order_value_2013Q2'):

    df = df_input

    # Keep just one observations per shipping_post_code
    earliest_yq = df.year_quarter.min()
    df_obs = df[df['year_quarter']==earliest_yq]

    assert df_obs.duplicated(subset=['shipping_post_code']).sum() == 0 # no duplicates
    df_obs = df_obs[['Treatment', 'credit_score', 'population_density_per_sqkm', earliest_qt_column]]
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
    result_df = result_df.drop(columns=['credit_score', 'population_density_per_sqkm', earliest_qt_column])

    # Get the shipping codes of the matched control rows
    df_Control_Shipping_Code = pd.merge(result_df, df, how='left', left_on='index', right_index=True)
    df_Control_Shipping_Code = df_Control_Shipping_Code[['shipping_post_code']]

    # Merge them back to the main dataset
    df_Matched_Controls = pd.merge(df_Control_Shipping_Code, df, how='left', left_on='shipping_post_code', right_on='shipping_post_code')
    df_Matched_Controls['Group'] = "Matched_Control"
    assert len(df_Matched_Controls.columns) == len(df.columns)
    df = pd.concat([df, df_Matched_Controls]).reset_index()

    return df

def alternative_control_preprocessing(df_input: pd.DataFrame,
                      treatment_area: str,
                      dropna: bool=True,
                      num_quarter_before=12,
                      num_quarter_after=12,
                      num_neighbors=1,
                      earliest_quarter='2013Q2') -> pd.DataFrame:

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
  df = pd.merge(df, temp_df, how='left', on='shipping_post_code')

  ## create return_rate outcome variable
  df['return_rate'] = df['number_of_returned_items']/df['number_of_items']

  ## need to fill nan because of division by 0
  df.return_rate.fillna(0.0, inplace=True)

  # 2. Treatment, Control Groups and Time Frame of Analysis/Observation
  ## keep only treated area and designate control group (all other areas where treatment=0, therefore also early stores)
  ## keep only within certain time frame (x quarters before and y quarters after store opening)
  df = get_before_after_opening_quarters(df, treatment_area=treatment_area, num_quarter_before=num_quarter_before, num_quarter_after=num_quarter_after)

  # 3. Nearest Neighbour
  df = get_nearest_neigbors(df_input=df, num_neighbors=num_neighbors, earliest_qt_column=f'order_value_{earliest_quarter}')

  return df

class AlternativeControl():

  def __init__(self, df_input, treatment_area, opening):

    self.df = df_input.copy()
    self.treatment_area = treatment_area
    self.opening = opening

    # Choose/Determine Control Postal Codes
    ########################################################################
    # Name of control group (e.g. 'early_stores') as 'treatment_store' value
    self.df = self.df.groupby([ 'treatment_store', 'year_quarter', 'Group'], dropna=False).aggregate({'number_of_returned_items': 'sum',
                                                                               'order_value' : 'sum',
                                                                               'number_of_orders': 'sum',
                                                                                'number_of_items': 'sum',
                                                                                'return_rate':'mean'}).reset_index()

    # Create additional outcome variable
    self.df['return_rate'] = self.df['number_of_returned_items']/self.df['number_of_items']


  def _scale_by_opening(self, df_input, columns):

    df = df_input.copy()

    for column in columns:
      if column in df_input.columns:
        df.loc[:, column] = df[column] / df.loc[df['year_quarter'] == self.opening, column].iloc[0]
      else:
        print(f"Column {column} not in dataframe")

    return df

  def fit(self):

    # create treatment unit dataframe
    self.df_treatment_unit = self.df[self.df.treatment_store == self.treatment_area]

    # create control dfs
    self.df_early_stores = self.df[(self.df.treatment_store == f"control_{self.treatment_area}") & (self.df.Group == "Early_Store")]
    self.df_non_stores = self.df[(self.df.treatment_store == f"control_{self.treatment_area}") & (self.df.Group == "Non_Store")]
    self.df_matched_control = self.df[(self.df.treatment_store == f"control_{self.treatment_area}") & (self.df.Group == "Matched_Control")]

    # scale treatment df and control dfs
    self.df_treatment_unit = self._scale_by_opening(self.df_treatment_unit, ['order_value', 'return_rate', 'number_of_orders'])
    self.df_early_stores = self._scale_by_opening(self.df_early_stores, ['order_value', 'return_rate', 'number_of_orders'])
    self.df_non_stores = self._scale_by_opening(self.df_non_stores, ['order_value', 'return_rate', 'number_of_orders'])
    self.df_matched_control = self._scale_by_opening(self.df_matched_control, ['order_value', 'return_rate', 'number_of_orders'])

    return self


  def plot(self, graphs=['matched_control'], xticks=[], treatment_label='Store opening'):


    outcome_variable = 'order_value' #number_of_orders, return_rate

    height = 3.1

    # Plot
    fig, ax = plt.subplots(1,1, figsize=(25,10))

    # plot treatment_unit graph
    plot = sns.lineplot(ax=ax, data=self.df_treatment_unit, x="year_quarter", y=outcome_variable, label=f"{self.treatment_area} Area", color="green")                      # y='order_value'

    # plot additional graphs
    if 'early_stores' in graphs:
      plot = sns.lineplot(ax=ax, data=self.df_early_stores, x="year_quarter", y='order_value', label='Control (Early Stores)', color="black")

    if 'non_stores' in graphs:
      plot = sns.lineplot(ax=ax, data=self.df_non_stores, x="year_quarter", y='order_value', label='Control (Non Stores)', color="gray")

    if 'matched_control' in graphs:
      plot = sns.lineplot(ax=ax, data=self.df_matched_control, x="year_quarter", y=outcome_variable, label='Matched Controls', color="red")


    # Set titles
    ax.text(x=0.5, y=1.1, s=f'Online Sales in {self.treatment_area} Area and Composite Control Areas', fontsize=25, weight='bold', ha='center', va='bottom', transform=ax.transAxes)
    ax.text(x=0.5, y=1.05, s='Indexed on opening date', fontsize=20, alpha=0.75, ha='center', va='bottom', transform=ax.transAxes)
    sns.set_style("whitegrid")

    # Set ticks
    plot.axes.set(xlabel=None, ylabel=None)
    plt.xticks(xticks, fontsize=20)
    plt.yticks(fontsize=20)

    # plot.yaxis.set_major_formatter('{x:1.0f}')
    # plt.ylabel('average order value', fontsize=20)
    # plt.xlabel('year|quarter',  fontsize=20, horizontalalignment='right', x=1)
    sns.lineplot(ax=ax, x=[self.opening, self.opening], y=[0, height], color="black", estimator=None, linewidth = 2.5)
    ax.annotate(f"{treatment_label}\n {self.treatment_area}",
                  xy=(self.opening, height),
                  xytext=(self.opening, height-0.3),
                  color="black",
                  horizontalalignment='center',
                  weight='bold',
                  bbox=dict(facecolor='white'),
                  size=15)
    ax.grid(False)
    #plt.grid(color='#CCCCCC', linestyle='--', linewidth=0.5)
    # plt.savefig(f'Online Sales in {self.treatment_area} Area and Composite Control Areas.png', bbox_inches='tight')
    plt.legend(loc=2, prop={'size': 20})

    return fig

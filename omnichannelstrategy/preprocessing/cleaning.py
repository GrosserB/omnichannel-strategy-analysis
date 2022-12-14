import pandas as pd

def basic_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """
    This is the first preprocessing step. This function takes in the (chunks of the) original order_data dataset
    and prepares it for further processing (eg. adding geolocation etc.).
    It returns the cleaned order_data dataset (or chunks of it)
    """

    # 1. Cancelled orders (cancellation_flag)
    ## Drop cancelled orders
    df = df[df['cancellation_flag'] == False]


    # 2. Returned items (return_quantity)
    ## Recode returns: recode NANs to zero, cast zero/one as integer
    ## return_quantity: 0 = not returned, 1 = returned
    df['return_quantity'] = df['return_quantity'].fillna(0).astype('int')


    # 3. Country (webshop_country)
    ## convert old specification and drop Unkown
    df['webshop_country'] = df['webshop_country'].str.replace('FH','DE')
    df = df[df['webshop_country'] != "UNKNOWN"]

    ## Keep only DACH for now
    keep_list = ['DE', 'AT', 'CH']
    df = df[df['webshop_country'].isin(keep_list)]


    # 4. Non-numeric values in numeric columns
    ## Drop all rows that have non-numeric values in columns that should be numeric
    should_be_numeric_cols = ['order_number', 'item_line_number', 'net_order_value_euros']
    df[should_be_numeric_cols] = df[should_be_numeric_cols].apply(pd.to_numeric, errors='coerce')
    df.dropna(subset=should_be_numeric_cols, inplace=True)


    # 5. Postal Code (shipping_post_code)
    ## the loading of the data in postal code chunks already removes false values and NULL values
    ## strip data of unnecessary spaces and remove NULL (unnecessary if postal code chunk load)
    df.loc[:,"shipping_post_code"] = df.shipping_post_code.str.strip()
    df.dropna(subset=["shipping_post_code"], inplace=True)

    ## Remove postal codes that fail the length criteria
    ## DE: five digets, from 0-9
    ## AT: four digits, from 1-9
    ## CH: four digits, from 1-9
    ## Only keep 5-digit postal codes for DE and 4-digit postal codes for AT and CH (that dont start with 0)
    df = df[((df.webshop_country == "DE") & (df.shipping_post_code.apply(len) == 5)) | ((df.webshop_country.isin(["AT", "CH"])) & (df.shipping_post_code.apply(len) == 4) & (~df.shipping_post_code.str.startswith("0")))]


    # 6. Order values (net_order_values_euros)
    ## Round the order values, and drop all order values of zero or less (data errors)
    df.loc[:, 'net_order_value_euros'] = df[['net_order_value_euros']].astype('float').round(0)
    df = df[df['net_order_value_euros'] > 0]


    # 7. Redundant columns
    ## Drop quantity_sold column and cancellation_flag (redundant information, all 1/True)
    df = df.drop(['quantity_sold', 'cancellation_flag'], axis="columns")


    # 8. Datetimes (create monthly and quarterly dates)
    ## Convert order_date to datetime-format
    df['order_date'] = pd.to_datetime(df['order_date'])

    ## Create quarterly date
    df['year_quarter'] = pd.PeriodIndex(df['order_date'], freq='Q')

    ## Create monthly date
    df['year_month'] = pd.PeriodIndex(df['order_date'], freq='M')

    ## Sort by order_date
    df=df.sort_values(by='order_date')

    # 9. Ensure Column Order
    ## force certain order of columns to prevent issues with BigQuery
    columns =['order_number', 'item_line_number', 'webshop_country', 'order_date', 'shipping_post_code', 'net_order_value_euros', 'return_quantity', 'year_quarter', 'year_month']
    df = df[columns]

    return df

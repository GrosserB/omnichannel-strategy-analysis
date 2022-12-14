import os
import googlemaps
import numpy as np
import pandas as pd

import geopandas as gpd
import pgeocode
import haversine as hs


# Function for Aggregation and Adding GeoCoordinates from GoogleMaps API
def extract_unique_post_codes_and_add_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """
    This function takes a dataframe, extracts unique `shipping_post_codes` for the DACH countries,
    and retrieves the geographic coordinates and address of that post code from google maps api.
    For this function to work an active account and token for google maps API is required.
    The function returns the dataframe of countries' unique postal codes with added geographic coordinates and address.
    """

    # definition of function for actual API access
    def get_gmaps_coordinates(country_code, postal_code, gmaps_client):
        country_encoder = {"DE": "Germany",
                            "AT": "Austria",
                            "CH": "Switzerland"}

        gmaps_query = f'Postal Code {postal_code} {country_encoder.get(country_code, "")}'
        geocode_result = gmaps_client.geocode(gmaps_query)

        # quick fix for empty results, may have to look into later
        if geocode_result == [] :
            return np.nan, np.nan, country_encoder.get(country_code, "")

        gmaps_coordinates = geocode_result[0]['geometry']['location']
        gmaps_address = geocode_result[0]['formatted_address']

        if geocode_result[0]['address_components'][0]['short_name'] == country_code:
            gmaps_coordinates = {'lat': np.nan, 'lng': np.nan}

        return gmaps_coordinates['lat'], gmaps_coordinates['lng'], gmaps_address

    # Extract Unique Postal Codes per Country with GroupBy
    unique_postal_codes = df.groupby(["webshop_country", "shipping_post_code"]).size().reset_index().drop(columns=0)

    # apply function to unique postal code dataframe
    gmaps_api_key = os.getenv("GMAPS_API_KEY")

    gmaps = googlemaps.Client(key=gmaps_api_key)

    unique_postal_codes[["gmaps_lat", "gmaps_lng", "gmaps_address"]] = unique_postal_codes.apply(lambda row: get_gmaps_coordinates(country_code=row['webshop_country'], postal_code=row['shipping_post_code'], gmaps_client=gmaps), axis='columns', result_type='expand')

    return unique_postal_codes

# Function for Getting `pgeocode` Coordinates (Latitude, Longitude)
def get_lan_lng(country: str, post_code: str) -> tuple:
    """
    This function retrieves the latitude and longitude for a given postal code from pgeocode and returns it as tuple
    """
    nomi = pgeocode.Nominatim(country)
    lat = nomi.query_postal_code([post_code]).latitude[0]
    lng = nomi.query_postal_code([post_code]).longitude[0]

    return lat, lng


# Function for Retrieving Correct Geographic Coordinates (filter out nonsense addresses from google maps)
def choose_correct_coordinates(row) -> tuple:
    """
    This function acts as a filter for correct latitudes and longitudes.
    This function returns gmaps_lat and gmaps_lng as long as it is identified as German adress.
    Otherwise this function returns geopd_lat and geopd_lng.
    If both fail, it returns spo_lat and spo_lng.
    """
    if not row["gmaps_address"]:
        # random fill of na to ble excluded later
        row["gmaps_address"] = "Utopia"

    if row["gmaps_address"].split(",")[-1].strip() in ["Germany", "Switzerland", "Austria"]:
        latitude = row["gmaps_lat"]
        longitude = row["gmaps_lng"]

    else:

        if row["geopd_lat"] != np.nan:
            latitude = row["geopd_lat"]
            longitude = row["geopd_lng"]

        else:
            latitude = row["spo_lat"]
            longitude = row["spo_lng"]


    return latitude, longitude


# Function for Calculating Distance to Stores
def map_store_distance(df: pd.DataFrame,
                       df_stores: pd.DataFrame) -> pd.DataFrame:
    """
    Function computes distances between the order shipping adresses' postal codes and the location of the stores.
    The distance computed is the haversine distance (in kilometers)
    The function fills the previously created empty columns
    """

    def apply_haversine(store_coordinates, row):
        # takes coordinates and a row from a dataframe
        # extracts coordinates from the row
        # calculates and returns distance between both coordinates
        # returns NaN if no distance can be calculated (because row has no longitude/latitude)

        delivery_coordinates = (row['latitude'], row['longitude'])

        try:
            return round(hs.haversine(store_coordinates, delivery_coordinates))
        except:
            return np.nan

    # for each city in df_stores get the coordinates and create a new column in df
    # fill that new column then with the distance using `apply_haversine` which is defined in this function as well
    for city in df_stores.city:

        store_latitude = df_stores.set_index(keys="city").loc[city].store_latitude
        store_longitude = df_stores.set_index(keys="city").loc[city].store_longitude
        store_coordinates = (store_latitude, store_longitude)

        df[f"dist_{city}"] = df.apply(lambda row: apply_haversine(store_coordinates, row), axis=1)

    return df

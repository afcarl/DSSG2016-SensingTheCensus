
# coding: utf-8
import pandas as pd
import json
import numpy
import math
from pandas.io.json import json_normalize
from scipy.spatial.distance import cosine


def df_to_geojson(df, properties):
    """
    A function that changes Pandas dataFrame to Geojson.
    
    Parameters
    ----------
    df : DataFrame
       This is a joined dataframe between CDR data and a grid data.
    properties : list
       Column names of CDR properties.

    Returns
    -------
    geojson : dict
    """
    geojson = {'crs': {'type': 'name', 
                       'properties': {"name": "urn:ogc:def:crs:EPSG::4326"}}, 
               'type': 'FeatureCollection', 'features': []}
    for _, row in df.iterrows():
        feature = {'type': 'Feature', 'properties': {}, 
                   'id': row['id'],
                   'geometry': {'type': 'Polygon', 'coordinates': []}}
        feature['geometry']['coordinates'] = row['geometry.coordinates']
        for prop in properties:
            if math.isnan(row[prop]):
                feature['properties'][prop] = 0
            else:
                feature['properties'][prop] = row[prop]
        geojson['features'].append(feature)
    return geojson


def join_cdr_grid_by_time(cdr, grid):
    """
    A function that outputs a joined table (DataFrame) from CDR and GRID data.
    The properties are more granular in time and day.
    e.g., CDR acitivities are aggregated by time period and day (weekday vs. weekend)

    Parameters
    ----------
    cdr : pandas DataFrame
       CDR data loaded in a pandas DataFrame.
    grid : pandas Series
       A pandas Series data of a city grid.

    Returns
    -------
    m_weekday, d_weekday, e_weekday, m_weekend, d_weekend, e_weekend : pandas DataFrames
        Each DataFrame has a different time period and weekday/weekend attribute.
    """
    cdrr = cdr.copy()
    cdrr.columns = ["cellId", "time", "countryCode", "smsIn", "smsOut",
                   "callIn", "callOut", "internet"]
    norm_grid = json_normalize(grid['features'])

    # change miliseconds to datetime
    cdrr.index = pd.to_datetime(cdrr['time'],unit='ms',utc=True)
    cdrr.index = cdrr.index.tz_localize('UTC').tz_convert('Europe/Rome')
    cdrr['date'] = cdrr.index
    cdrr['time_hour'] = cdrr.index.hour
    cdrr['weekday'] = cdrr.index.weekday

    # returning Booleans
    cdrr['morning_weekday'] = (cdrr['time_hour'] >= 0) & (cdrr['time_hour'] < 8) & (cdrr['weekday'] != 6) & (cdrr['weekday'] != 5)
    cdrr['day_weekday'] = (cdrr['time_hour'] >= 8) & (cdrr['time_hour'] < 16) & (cdrr['weekday'] != 6) & (cdrr['weekday'] != 5)
    cdrr['evening_weekday'] = (cdrr['time_hour'] >= 16) & (cdrr['time_hour'] < 24) & (cdrr['weekday'] != 6) & (cdrr['weekday'] != 5)
    cdrr['morning_weekend'] = (cdrr['time_hour'] >= 0) & (cdrr['time_hour'] < 8) & ((cdrr['weekday'] == 6) | (cdrr['weekday'] == 5))
    cdrr['day_weekend'] = (cdrr['time_hour'] >= 8) & (cdrr['time_hour'] < 16) & ((cdrr['weekday'] == 6) | (cdrr['weekday'] == 5))
    cdrr['evening_weekend'] = (cdrr['time_hour'] >= 16) & (cdrr['time_hour'] < 24) & ((cdrr['weekday'] == 6) | (cdrr['weekday'] == 5))

    #aggregations for each time/day slots
    morning_weekday = cdrr[(cdrr['countryCode'] != 0) & (cdrr['morning_weekday'] == True)].groupby('cellId').agg({
                        'cellId': 'first',
                        'time': 'first',
                        'smsIn': 'sum',
                        'smsOut': 'sum',
                        'callIn': 'sum',
                        'callOut': 'sum',
                        'internet': 'sum'
                    })
    day_weekday = cdrr[(cdrr['countryCode'] != 0) & (cdrr['day_weekday'] == True)].groupby('cellId').agg({
                        'cellId': 'first',
                        'time': 'first',
                        'smsIn': 'sum',
                        'smsOut': 'sum',
                        'callIn': 'sum',
                        'callOut': 'sum',
                        'internet': 'sum'
                    })
    evening_weekday = cdrr[(cdrr['countryCode'] != 0) & (cdrr['evening_weekday'] == True)].groupby('cellId').agg({
                        'cellId': 'first',
                        'time': 'first',
                        'smsIn': 'sum',
                        'smsOut': 'sum',
                        'callIn': 'sum',
                        'callOut': 'sum',
                        'internet': 'sum'
                    })
    morning_weekend = cdrr[(cdrr['countryCode'] != 0) & (cdrr['morning_weekend'] == True)].groupby('cellId').agg({
                        'cellId': 'first',
                        'time': 'first',
                        'smsIn': 'sum',
                        'smsOut': 'sum',
                        'callIn': 'sum',
                        'callOut': 'sum',
                        'internet': 'sum'
                    })
    day_weekend = cdrr[(cdrr['countryCode'] != 0) & (cdrr['day_weekend'] == True)].groupby('cellId').agg({
                        'cellId': 'first',
                        'time': 'first',
                        'smsIn': 'sum',
                        'smsOut': 'sum',
                        'callIn': 'sum',
                        'callOut': 'sum',
                        'internet': 'sum'
                    })
    evening_weekend = cdrr[(cdrr['countryCode'] != 0) & (cdrr['evening_weekend'] == True)].groupby('cellId').agg({
                        'cellId': 'first',
                        'time': 'first',
                        'smsIn': 'sum',
                        'smsOut': 'sum',
                        'callIn': 'sum',
                        'callOut': 'sum',
                        'internet': 'sum'
                    })

    # merge with grid
    m_weekday = pd.merge(left=norm_grid, right=morning_weekday, how='left', left_on='properties.cellId', right_on='cellId')
    d_weekday = pd.merge(left=norm_grid, right=day_weekday, how='left', left_on='properties.cellId', right_on='cellId')
    e_weekday = pd.merge(left=norm_grid, right=evening_weekday, how='left', left_on='properties.cellId', right_on='cellId')
    m_weekend = pd.merge(left=norm_grid, right=morning_weekend, how='left', left_on='properties.cellId', right_on='cellId')
    d_weekend = pd.merge(left=norm_grid, right=day_weekend, how='left', left_on='properties.cellId', right_on='cellId')
    e_weekend = pd.merge(left=norm_grid, right=evening_weekend, how='left', left_on='properties.cellId', right_on='cellId')

    #filling NaN values with 0's
    m_weekday.fillna(0, inplace=True)
    d_weekday.fillna(0, inplace=True)
    e_weekday.fillna(0, inplace=True)
    m_weekend.fillna(0, inplace=True)
    d_weekend.fillna(0, inplace=True)
    e_weekend.fillna(0, inplace=True)

    return m_weekday, d_weekday, e_weekday, m_weekend, d_weekend, e_weekend


def join_cdr_grid(cdr, grid):
    """
    A function that outputs a joined table (DataFrame) from CDR and GRID data.
    
    Parameters
    ----------
    cdr : pandas DataFrame
       CDR data loaded in a pandas DataFrame.
    grid : pandas Series
       A pandas Series data of a city grid.

    Returns
    -------
    joined_df : pandas DataFrame
    """
    

    cdr.columns = ["cellId", "time", "countryCode", "smsIn", "smsOut",
                   "callIn", "callOut", "internet"]
    norm_grid = json_normalize(grid['features'])

    agg_df = cdr[cdr['countryCode'] != 0].groupby('cellId').agg({
            'cellId': 'first',
            'time': 'first',
            'smsIn': 'sum',
            'smsOut': 'sum',
            'callIn': 'sum',
            'callOut': 'sum',
            'internet': 'sum'
        })


    joined_df = pd.merge(left=norm_grid, right=agg_df, how='left',
                        left_on='properties.cellId', right_on='cellId')
    
    return joined_df


def calculate_cosine_similarity(grid, dfs, reference_day='1101'):
    """
    A function that calculate consine similarity values by day.
    
    Parameters
    ----------
    grid : a pandas Series
        A pandas Series data of a city grid.
    dfs : a dict of pandas Series
        Each element of a dict has a key for a day (e.g., '1101')
        and a value for a DataFrame of joined table for that day.
    reference_day : a string
        A string of 'mm/dd' that provides a reference day to compare
        with other days.

    Returns
    -------
    smsIn, smsOut, callIn, callOut, internet : lists 
        Contain {day : consine_similarity} values, sorted by date
    """
    smsIn = {}
    smsOut = {}
    callIn = {}
    callOut = {}
    internet = {}

    reference = join_cdr_grid(dfs[reference_day], grid)
    reference.fillna(0, inplace=True)

    for key, value in dfs.items():
        if key != '1101':
            joined = join_cdr_grid(value, grid)
            joined.fillna(0, inplace=True)
            try:
                smsIn[key] = 1 - cosine(reference["smsIn"], joined["smsIn"])
            except:
                print (key)
                continue
            try:
                smsOut[key] = 1 - cosine(reference["smsOut"], joined["smsOut"])
            except:
                print (key)
                continue
            try:
                callIn[key] = 1 - cosine(reference["callIn"], joined["callIn"])
            except:
                print (key)
                continue
            try:
                callOut[key] = 1 - cosine(reference["callOut"], joined["callOut"])
            except:
                print (key)
                continue
            try:
                internet[key] = 1 - cosine(reference["internet"], joined["internet"])
            except:
                print (key)
                continue
        print("processed", key)

    #sorting
    smsIn = sorted(smsIn.items(), key=lambda s: s[0])
    smsOut = sorted(smsOut.items(), key=lambda s: s[0])
    callIn = sorted(callIn.items(), key=lambda s: s[0])
    callOut = sorted(callOut.items(), key=lambda s: s[0])
    internet = sorted(internet.items(), key=lambda s: s[0])

    return smsIn, smsOut, callIn, callOut, internet

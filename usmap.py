import pandas as pd
import haversine as hs
from haversine import Unit
# import numpy as np


def migration_data(base_df, lat_lon_df, source):
    """
    Method that subsets the main dataframe and produces
    a dataframe for the selected state on the map. Along
    with that it appends the corresponding latitutde and
    longitude values for all the states in the resulting
    df
    :param base_df: df for migrations from all states to all states
    :param lat_lon_df: df for latitude and longitude values for each state
    :param source: selected state
    :return: migration_df
    """
    filter = (base_df['o_state_name'] == source)
    migration_df = base_df[filter]
    migration_df.reset_index(drop=True, inplace=True)

    migration_df = migration_df.groupby(['o_state_id', 'o_state_name',
                                         'd_state_id', 'd_state_name'])['n']\
                               .sum()\
                               .reset_index()\
                               .drop(['o_state_id', 'o_state_name'], axis=1)

    migration_df = pd.concat([migration_df, lat_lon_df], axis=1)

    return migration_df


def calc_distance(loc1, loc2):
    """
    Method that calculates distance from one point to another, where each
    point is a tuple
    :param loc1: tuple of lat, lon
    :param loc2: tuple of lat, lon
    :return: distance in miles between the two points
    """
    return hs.haversine(loc1, loc2, unit=Unit.MILES)


def miles_moved_race(base_df, lat_lon_df, source):
    """
    Function that takes the base dataframe and source, and calculates the weighted average of the distance
    moved by each race
    :param base_df: base dataframe
    :param lat_lon_df: dataframe containing lat and lon for each state
    :param source: selected state
    :return: df with average distance moved for each race
    """
    filter = (base_df['o_state_name'] == source) & (base_df['d_state_name'] != source)
    distance_df = base_df[filter].copy()
    distance_df.reset_index(drop=True, inplace=True)
    distance_df.drop(['o_state_id', 'o_state_name', 'd_state_id'], axis=1, inplace=True)

    counts_df = distance_df.groupby(['d_state_name', 'race'])['n'].agg('sum')\
                            .reset_index()
    counts_df = counts_df.join(lat_lon_df.set_index('State'), on='d_state_name')

    # Calculating miles moved
    race_groups = counts_df.groupby(['race'])
    race_distance_dict = {'Race': [],
                          'Distance': []}
    source_lat_lon = (lat_lon_df[lat_lon_df['State'] == source]['Latitude'].item(),
                      lat_lon_df[lat_lon_df['State'] == source]['Longitude'].item())

    for race in counts_df['race'].unique():
        race_df = race_groups.get_group(race)

        # numbers_array = np.abs(np.array(list(race_df['n'])).reshape((50,)))
        numbers_array = abs(list(race_df['n']))
        lat_list = list(race_df['Latitude'])
        lon_list = list(race_df['Longitude'])

        distances = []
        for idx, dest_lat_lon in enumerate(zip(lat_list, lon_list)):
            # distances[idx] = calc_distance(source_lat_lon, dest_lat_lon)
            distances.append(calc_distance(source_lat_lon, dest_lat_lon))

        weighted_distance = 0
        for i in range(50):
            weighted_distance += numbers_array[i] * distances[i]
        # weighted_distance = distances @ numbers_array
        race_distance_dict['Race'].append(race)
        # race_distance_dict['Distance'].append(np.round(weighted_distance/np.sum(numbers_array, axis=0), 2))
        race_distance_dict['Distance'].append(weighted_distance/sum(numbers_array))

    return pd.DataFrame.from_dict(race_distance_dict, orient='columns')


def miles_moved_race_q(base_df, lat_lon_df, source):
    filter = (base_df['o_state_name'] == source) & (base_df['d_state_name'] != source)
    distance_df = base_df[filter].copy()
    distance_df.reset_index(drop=True, inplace=True)
    distance_df.drop(['o_state_id', 'o_state_name', 'd_state_id'], axis=1, inplace=True)

    distance_df = distance_df.join(lat_lon_df.set_index('State'), on='d_state_name')

    # Calculating miles moved
    race_groups = distance_df.groupby(['race'])
    race_distance_dict = {'Race': [],
                          'Quintile': [],
                          'Distance': []}
    source_lat_lon = (lat_lon_df[lat_lon_df['State'] == source]['Latitude'].item(),
                      lat_lon_df[lat_lon_df['State'] == source]['Longitude'].item())

    for race in distance_df['race'].unique():
        quintile_groups = race_groups.get_group(race).groupby(['quintile'])

        for i in range(1, 6):
            q_df = quintile_groups.get_group(i)

            numbers_array = np.abs(np.array(list(q_df['n'])).reshape((50,)))
            lat_list = list(q_df['Latitude'])
            lon_list = list(q_df['Longitude'])

            distances = np.zeros(50)
            for idx, dest_lat_lon in enumerate(zip(lat_list, lon_list)):
                distances[idx] = calc_distance(source_lat_lon, dest_lat_lon)

            weighted_distance = distances @ numbers_array
            race_distance_dict['Race'].append(race)
            race_distance_dict['Quintile'].append(i)
            race_distance_dict['Distance'].append(np.round(weighted_distance/np.sum(numbers_array, axis=0), 2))

    return pd.DataFrame.from_dict(race_distance_dict, orient='columns')


def global_average_distance(base_df, lat_lon_df):
    distances_state_wise = []

    for state in lat_lon_df['State'].unique():
        migration_df = migration_data(base_df, lat_lon_df, state)
        source_lat_lon = (lat_lon_df[lat_lon_df['State'] == state]['Latitude'].item(),
                          lat_lon_df[lat_lon_df['State'] == state]['Longitude'].item())

        numbers_array = np.abs(np.array(list(migration_df['n'])).reshape((51,)))
        lat_list = list(migration_df['Latitude'])
        lon_list = list(migration_df['Longitude'])

        distances = np.zeros(51)
        for idx, dest_lat_lon in enumerate(zip(lat_list, lon_list)):
            distances[idx] = calc_distance(source_lat_lon, dest_lat_lon)

        weighted_distance = distances @ numbers_array
        distances_state_wise.append(np.round(weighted_distance/np.sum(numbers_array, axis=0), 2))
    return np.round(np.mean(np.array(distances_state_wise)), 2)

def race_data(base_df, source):
    filter = (base_df['o_state_name'] == source)
    race_df = base_df[filter]
    race_df.reset_index(drop=True, inplace=True)
    race_df = race_df[race_df['d_state_name'] != source]
    race_df = race_df.drop(['o_state_id', 'd_state_id', 'quintile'], axis=1)
    race_df = race_df.groupby(['o_state_name', 'race'])['n']\
                               .sum()\
                               .reset_index()

    quintile_df = base_df[filter]
    quintile_df.reset_index(drop=True, inplace=True)
    quintile_df = quintile_df[quintile_df['d_state_name'] != source]
    quintile_df = quintile_df.drop(['o_state_id', 'd_state_id', 'd_state_name'], axis=1)
    quintile_df = quintile_df.groupby(['o_state_name', 'race', 'quintile'])['n']\
                               .sum()\
                               .reset_index()

    return race_df, quintile_df

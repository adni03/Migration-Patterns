import pandas as pd
from vega_datasets import data

def create_state_csv():
    df = pd.read_csv('C:/Users/anjby/IDS/abnormal_distribution/MigrationPatternsData/od.csv')
    df.info(verbose=True, show_counts=True)

    grouped_df = df.groupby(['o_state_name', 'd_state_name', 'pool'])['n']\
                .agg('sum')\
                .reset_index()
    
    # Splitting the pool in to state and quantile

    splits = grouped_df['pool'].str.split('Q', expand=True)
    grouped_df['race'] = splits[0]
    grouped_df['quintile'] = splits[1]
    grouped_df.drop(['pool'], axis=1, inplace=True)

    # Adding unique identifier for source and destination states
    pop = data.population_engineers_hurricanes()

    pop = pop[['state', 'id']]
    states = list(pop['state'])
    ids = list(pop['id'])

    ## Source state
    state_id_dict = {}

    for idx, state in zip(ids, states):
        if state == "District of Columbia":
            state_id_dict["DC"] = idx
        else:
            state_id_dict[state] = idx

    
    def assign_state_id(state):
        return state_id_dict[state]

    grouped_df['o_state_id'] = grouped_df.apply(lambda x: assign_state_id(x['o_state_name']), axis=1)
    grouped_df['d_state_id'] = grouped_df.apply(lambda x: assign_state_id(x['d_state_name']), axis=1)

    col_order = ['o_state_id', 'o_state_name', 'd_state_id', 'd_state_name',
                'race', 'quintile', 'n']
    grouped_df = grouped_df.reindex(columns=col_order)

    grouped_df.to_csv('state_to_state_migration.csv')
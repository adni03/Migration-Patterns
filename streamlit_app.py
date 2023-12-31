import altair as alt
import pandas as pd
import streamlit as st
from vega_datasets import data

from usmap import migration_data, miles_moved_race, miles_moved_race_q, global_average_distance, race_data

st.title("How does race and parental income influence how far young adults move from home for their first job?")
st.write("In this data science project we are interested in analyzing how race and the parental income of a young adult\
    influence how far they move for their first job. Here we use the Migration Patterns data whose sample includes \
    all children in the Census Numerical Identification Database (Numident) of Social Security Number holders who are \
    born in the U.S. between 1984-92. Child race is measured using information from the 2010 Decennial Census and American \
    Community Survey (ACS). In this dataset we have 5 unique values for race- Asian, Black, Hispanic, White, and Other. \
    Location at age 16 and 26 is assigned using Census, tax, and HUD information. \
    Parental income is measured as a 5-year average of family income when the children are aged 14-18 based on the \
    tax form 1040 of the parent who claims them as a dependent. The values for these quintiles are integers from 1 to 5 \
    where “1” is the poorest parental income quintile and 5 is richest parental income quintile.")

st.write('The US map shows the states young adults migrated to from a selected state highlighted in orange. It is \
    followed by a bar chart which shows the Top 10 states the population moved to from that state. Selecting a state on the map\
    highlights the corresponding bar in the bar chart and vice versa.')

@st.cache  # add caching so we load the data only once
def load_data():
    """
    Method to load relevant files:
    - state_to_state_migration.csv: Contains number of people who moved from one state to other states
                                    broken down by race and income quintiles
    - state_lat_lon.csv: Contains states and their latitude, longitudes
    :return:
        - base_df: df from state_to_state.csv
        - lat_lon_df: df from state_lat_lon.csv
    """
    base_df = pd.read_csv('state_to_state_migration.csv')
    base_df.drop(['Unnamed: 0'], axis=1, inplace=True)

    lat_lon_df = pd.read_csv('state_lat_lon.csv')
    lat_lon_df = lat_lon_df.sort_values(by=['State']).reset_index(drop=True)

    return base_df, lat_lon_df

# Method call to load the required data
base_df, lat_lon_df = load_data()

# Drop down to list the available states
states_options = lat_lon_df['State']

source = st.selectbox(
    'Where did young adults move to?',
    states_options)

migration_df = migration_data(base_df, lat_lon_df, source)

click = alt.selection_multi(fields=['d_state_name'])

# Chart for highlighting the selection
states = alt.topo_feature(data.us_10m.url, feature='states')
selection_chart = alt.Chart(states, width=2000, height=15) \
    .mark_geoshape().encode(
    tooltip=[alt.Tooltip('n:Q', title='Population staying back')],
    color=alt.Color('n:Q', scale=alt.Scale(scheme="yelloworangered"), legend=None)
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(migration_df[migration_df['d_state_name'] == source], 'd_state_id', ['n'])
).properties(
    width=600,
    height=500
).project(
    type='albersUsa'
)

# Adding our data to the chart
#https://altair-viz.github.io/gallery/choropleth.html
migration_chart = alt.Chart(states, width=2000, height=15,
                            title='Choropleth showing the number of people migrating from {}'.format(source)) \
    .mark_geoshape(
    stroke='lightgray'
).encode(
    tooltip=[alt.Tooltip('d_state_name:O', title='State'),
             alt.Tooltip('n:Q', title='# moved here')],
    color=alt.Color('n:Q',
                    title="Population migrating"),
    opacity=alt.condition(click, alt.value(1), alt.value(0.2))
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(migration_df[migration_df['d_state_name'] != source], 'd_state_id',
                         ['n', 'd_state_name'])
).properties(
    width=600,
    height=500
).project(
    type='albersUsa'
).add_selection(click)

usmap = alt.layer(selection_chart,
                  migration_chart).resolve_scale(color='independent')

#https://stackoverflow.com/questions/63751130/altair-choropleth-map-color-highlight-based-on-line-chart-selection
popular_state_bar = alt.Chart(
                        migration_df[migration_df['d_state_name'] != source].nlargest(10, 'n'),
                        title='Top 10 states young adults migrated to from {}'.format(source),
                        width=600).\
                        mark_bar().encode(
                            x=alt.X('n', title="Population migrating"),
                            opacity=alt.condition(click, alt.value(1), alt.value(0.2)),
                            color=alt.Color('n:Q', legend=None),
                            y=alt.Y('d_state_name', sort='-x', title="Destination States"),
                            tooltip=[alt.Tooltip('n:Q', title="# of people")]
                    ).add_selection(click)

combo = alt.vconcat(usmap, popular_state_bar, center=True)
combo

race_df, quintile_df = race_data(base_df, source)
max_race =  max(race_df['race'])
max_quin_pop = max(quintile_df[quintile_df['race'] == max_race]['n'])
max_quin = quintile_df.loc[quintile_df.n == max_quin_pop, 'quintile'].values[0]

st.subheader("Influence of Race and Parental Income on the number of young adults migrating")
st.write('Let us now analyze the influence of race in the movement of population. For the state of {},\
    the bar chart shows the number of people who moved out of the state by each race. The quintile chart shows the distribution \
    of population migrated in each parental income quintile. According to this dataset, Quintile **1** is the poorest \
    parental income quintile and **5** is richest parental income quintile'.format(source))
    
st.write('In state of **{}**,'.format(source))
st.markdown('- Young adults belonging to the **{}** race move the maximum. '.format(max_race))
st.markdown('- Within the race, the young adults belonging to Quintile **{}** move the most.'.format(max_quin))
   
st.write('Additionally, on clicking the bar corresponding to a particular race, the pie chart shows the number \
    of people who moved in that race by the parental income quintile.')

st.subheader('Insights:')
st.write('From analyzing the charts for a majority of the states, it was evident that the White young adults \
    moved the maximum in numbers away from their homes. Within this, it was interesting to note that young adults \
    belonging to Quintile 5 moved the most. In contrast, the Black and Hispanic young adults belonging to Quintile 1 \
    moved the most.')
brush = alt.selection_single(encodings=["y"], init={'race': max_race}, empty='none')

race_barchart = alt.Chart(race_df, 
title='Population migration from {} by Race'.format(source),
    width=420).mark_bar().encode(
    x=alt.X('n', title="Population migrating"),
    y=alt.Y('race', title="Race"),
    opacity = alt.condition(brush, alt.value(1), alt.value(0.8)),
    tooltip=[alt.Tooltip('n:Q', title="# of people")]
).add_selection(brush)

race_quintile_chart = alt.Chart(quintile_df, 
    title = 'Population migrating by selected race').encode(
    theta=alt.Theta("n:Q", stack=True), color=alt.Color("quintile:N"),
    tooltip=[alt.Tooltip('quintile:N', title='Quintile')]
).transform_filter(brush)

pie = race_quintile_chart.mark_arc(outerRadius=100, innerRadius = 60)
text = race_quintile_chart.mark_text(radius=125, size=16).encode(
    text="n:Q",
    opacity=alt.condition(brush, alt.value(1), alt.value(0)))

race_quintile_chart_comb = pie + text

race_charts = alt.hconcat(race_barchart, race_quintile_chart_comb, center=True)
race_charts


miles_moved_race_df = miles_moved_race(base_df, lat_lon_df, source)
miles_moved_race_q_df = miles_moved_race_q(base_df, lat_lon_df, source)

max_miles_dist =  max(miles_moved_race_df['Distance'])
max_miles_race = max(miles_moved_race_df[miles_moved_race_df['Distance'] == max_miles_dist]['Race'])

max_miles_quin_dist = max(miles_moved_race_q_df.loc[miles_moved_race_q_df.Race == max_miles_race, 'Distance'])
max_miles_quin = miles_moved_race_q_df.loc[miles_moved_race_q_df.Distance == max_miles_quin_dist, 'Quintile'].values[0]

st.subheader("Influence of Race and Parental Income on the distance young adults migrate")
st.write('In state of **{}**,'.format(source))
st.markdown('- Young adults belonging to the **{}** race move the farthest from their homes. '.format(max_miles_race))
st.markdown('- Within the race, the young adults belonging to Quintile **{}** move the most.'.format(max_miles_quin))
   
st.write('Additionally, on clicking the bar corresponding to a particular race, the bar chart shows the number \
    of people who moved in that race by the parental income quintile. The bar chart below also shows the average \
    distance moved in miles as compared to the national average for the selected race.')


st.subheader('Insights:')
st.write('From analyzing the charts for a majority of the states, it was evident that on average Asian young adults moved the \
    farthest away from their homes. In addition on observing the quintiles we noticed that young adults belonging to \
    Quintile 4 or 5 moved the farthest distances. However, this cannot be generalized, the distance moved by different races \
    depends on the state as well.')

race_brush = alt.selection_single(encodings=['y'])
distance_moved_race_bar = alt.Chart(
                                miles_moved_race_df,
                                height=100,
                                title='Average distance moved by each race from {}'.format(source))\
                                .mark_bar().encode(
                                    x=alt.X('Distance', title='Distance moved in miles'),
                                    y=alt.Y('Race', title="Race"),
                                    opacity=alt.condition(race_brush, alt.value(1), alt.value(0.2)),
                                    tooltip=[alt.Tooltip('Distance:Q', title='Distance moved')]
                                ).add_selection(race_brush)

distance_moved_race_q_bar = alt.Chart(
                                miles_moved_race_q_df,
                                width=180,
                                title='Average distance moved by each quintile from {}'.format(source))\
                                .mark_bar().encode(
                                    y=alt.Y('Distance:Q', title='Distance moved in miles'),
                                    x=alt.X('Quintile:O', title="Income Quantile"),
                                    tooltip=[alt.Tooltip('Distance:Q', title='Distance moved')],
                                    color='Race'
                                ).transform_filter(race_brush)

avg_distance = global_average_distance(base_df, lat_lon_df)

#Referred from 
#https://altair-viz.github.io/gallery/isotype_emoji.html
#https://medium.com/dataexplorations/how-to-add-emojis-to-an-altair-chart-f9bc02da3a4b
miles_moved_race_df['icon'] = ['👨', '👨', '👨', '👨', '👨']
avg_df = pd.DataFrame({'Name': 'National Average', 'Value': avg_distance, 'icon': '🇺🇸'}, index=[0])

race_dist = alt.Chart(
    miles_moved_race_df,
    title="Distance moved by selected race vs National Average",
    height=75)\
    .mark_text(filled=True, size=25, baseline='middle').encode(
        x=alt.X('Distance:Q', title="Distance moved in miles", axis=alt.Axis(grid=False),
                scale=alt.Scale(domain=[0, miles_moved_race_df['Distance'].max()+200])),
        text=alt.Text('icon'),
        tooltip=[alt.Tooltip('Distance:Q', title='Distance')]
    ).transform_filter(race_brush)

avg_dist = alt.Chart(
    avg_df,
    height=75)\
    .mark_text(filled=True, size=25, baseline='middle').encode(
        x=alt.X('Value:Q', scale=alt.Scale(domain=[0, miles_moved_race_df['Distance'].max()+200])),
        text=alt.Text('icon'),
        tooltip=[alt.Tooltip('Value:Q', title='Distance')]
    )

line = alt.Chart(pd.DataFrame({'y': [1]}))\
    .mark_rule().encode(y=alt.Y('y', axis=alt.Axis(tickSize=0, labelFontSize=0), title=None))

dist_plot = race_dist + avg_dist + line
combo2 = alt.hconcat(distance_moved_race_bar, distance_moved_race_q_bar, center=True)
cc = alt.vconcat(combo2, dist_plot)
cc

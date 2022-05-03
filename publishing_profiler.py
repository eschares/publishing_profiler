# -*- coding: utf-8 -*-
"""
Created on Sat Aug 28 12:26:11 2021

@author: eschares

Input: Web of Science export file
Output: analysis of corresponding authored articles and breakdown by publisher
Delivered: Streamlit web app
"""

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import time


st.set_page_config(page_title='Publishing Profiler', layout='centered', initial_sidebar_state="expanded")

st.header("**Publishing Profiler**")
st.subheader("Analyze your campus publishing output")

# either Excel or tab delimited are your choices
# Export WoS data with OG=Iowa State University OR AD=Ames, IA

#file = filename = "2020_WoS_1-500_exportedasUTF8.txt"  #works
file = filename = "WoS_2020_tabdelimited_full_record_1000records.txt"  #seems to work?
#file = filename = "WoS_ISU_AmesIA_2020.xlsx"


@st.cache(suppress_st_warning=True) #suppresses warning about st.write within load_data
def load_data(file):
    st.write("New file loaded")
    return pd.read_csv(file, delimiter='\\t', header=[0], engine='python')# skiprows=1, header=0), encoding='utf-8')  #Process the data in cached way to speed up processing
    #return pd.read_excel(file)


# if 'load_data_flag' not in st.session_state:
#     st.session_state['load_data_flag'] = 1
#     df = load_data(file)


#df = load_data(file)       #use cached load
df = pd.read_csv(file, delimiter='\\t', header=[0], engine='python')    #allow mutation of df by not using cache @load_file
df['DI'] = df['DI'].str.lower()

#If loading multiple files, would need some sort of progress bar, maybe after each file gets processed
#would also need to ignore header in file after first (2+)
my_bar = st.progress(0)
for percent_complete in range(100):
    time.sleep(0.01)
    my_bar.progress(percent_complete + 1)
#st.progress(78)
st.balloons()
#update this number somehow, maybe each loop is 1/N where N is number of files loading

st.markdown("""---""")

########  Show information about the raw starting data  ########
total_loaded_records = df.shape[0]
st.subheader(f'Raw Data loaded, Web of Science {total_loaded_records} records')

if st.checkbox('Show Raw Data'):
    st.write(df)

if st.checkbox('Show Raw Distribution of Document Types'):
    st.write(pd.value_counts(df['DT']))
st.markdown("""---""")


########  Show information about removing Document Types of Editorials, Corrections, etc  ########
# Remove the Book Review type since it contains the word "Review"
df = df.loc[~(df['DT'].isin(['Book Review']))]

# Then keep Articles, which show up as: 
#     Article; 
#     Article; Data Paper
#     Article; Early Access
# and keep Reviews, which show up as:
#     Review
#     Review; Early Access
# But not Book Review since we removed that in the previous step
df = df.loc[(df['DT'].str.contains('Article', case=False, regex=False, na=False)) | (df['DT'].str.contains('Review', case=False, regex=False, na=False))]

# Sometimes Article Title is repeated from an Early Access version
df = df.drop_duplicates(subset=['TI'], keep='first', ignore_index=True)

st.subheader(f'Remove {total_loaded_records - df.shape[0]} Editorials, Corrections, Book Reviews etc.')
st.subheader(f'Keep Article and Review Types, {df.shape[0]} records')
if st.checkbox('Show Filtered Data'):
    st.write(df)

if st.checkbox('Show Filtered Distribution of Document Types'):
    st.write(pd.value_counts(df['DT']))


########  Set up column of T/F for ISU CA or not  ########
#### Filter down to ISU CA ####
CA_column_filt = ( (df['RP'].str.contains('Iowa State Univ', case=False, regex=False, na=False)) |
    (df['RP'].str.contains('Ames Lab', case=False, regex=False, na=False)) |
    (df['RP'].str.contains('Ames, IA', case=False, regex=False, na=False)) |
    (df['RP'].str.contains('USDA', case=False, regex=False, na=False))
    )

df['ISU_CA'] = CA_column_filt


#############  Sidebar Filters  ###############
st.sidebar.subheader("**Filters**")

CA_filt = st.sidebar.radio("Look at Corresponding Authors only?", ("Yes", "No"))

if CA_filt == 'Yes':
    filt = (df['ISU_CA'] == True)
else:
    filt = ( (df['ISU_CA'] == True) | (df['ISU_CA'] == False) )   #show all records, I'm sure there's a better way to do that but oh well

st.sidebar.write(f'{df[filt].shape[0]} rows out of {df.shape[0]} match your criteria')

#############  Clean Publisher names  ###############
df_publisher_list = pd.read_csv('Publisher_list_converter.csv')
df = pd.merge(df_publisher_list, df, on='PU', how='right')      #like a VLOOKUP in Excel, right merge means output dataframe has all rows from 2nd df and matching rows from 1st df. If rows are not matched in 1st df they replaced by NaN

df.to_csv('PU_cleaned.csv')



########  Charts start here  ########
st.markdown("""---""")
st.subheader('Charts')

df[filt]
publisher_chart = alt.Chart(df[filt]).mark_bar().encode(
    alt.X('PU_cleaned:N', sort='-y', title='Publisher'),
    alt.Y('count()'),
    tooltip=['PU_cleaned', 'count(PU_cleaned)'],
    ).interactive().properties(
        height=500,
        title={
            "text": ["Article count by Publisher"],
            "subtitle": ["Graph supports pan, zoom, and live-updates from changes in filters on left sidebar"],
            "color": "black",
            "subtitleColor": "gray"
        }
        )
st.altair_chart(publisher_chart, use_container_width=True)


publisher_chart_top10 = alt.Chart(df[filt]).transform_aggregate(
    count='count()',
    groupby=['PU_cleaned']
).transform_window(
    rank='rank(count)',
    sort=[alt.SortField('count', order='descending')]
).transform_filter(
    alt.datum.rank <= 10
).mark_bar().encode(
    alt.X('PU_cleaned:N', sort='-y', title='Publisher'),
    alt.Y('count:Q'),
    tooltip=['PU_cleaned', 'count:Q']
).properties(
    height=500,
    title={
        "text": ["Article count by Publisher, Zoom in on Top 10"],
        "subtitle": ["Graph supports pan, zoom, and live-updates from changes in filters on left sidebar"],
        "color": "black",
        "subtitleColor": "gray"
    }
)



# publisher_chart_top10 = alt.Chart(df[filt]).mark_bar().encode(
#     alt.X('PU:N', sort='-y', title='Publisher'),
#     alt.Y('count()'),
#     tooltip=['PU', 'count(PU)'],
#     ).interactive().properties(
#         height=500,
#         title={
#             "text": ["Corresponding Authored Article count by Publisher"],
#             "subtitle": ["Graph supports pan, zoom, and live-updates from changes in filters on left sidebar", "Journals on the underside of this curve might be considered for cancellation"],
#             "color": "black",
#             "subtitleColor": "gray"
#         }
#         ).transform_window(
#     rank='rank(count)',
#     sort=[alt.SortField('count', order='descending')]
# ).transform_filter(
#     (alt.datum.rank < 10)
# )

st.altair_chart(publisher_chart_top10, use_container_width=True)








publisher_chart_by_journaltitle = alt.Chart(df[filt]).mark_bar().encode(
    x=alt.X('PU_cleaned:N', sort='-y', title="Publisher"),
    y=alt.Y('count()'),
    color=alt.Color('JI', legend=alt.Legend(title="Journal Title")),
    order=alt.Order('count(JI)', sort='descending'),
    tooltip=['PU_cleaned', 'JI', 'count(JI)'],
    ).interactive().properties(
        height=500,
        title={
            "text": ["Article count by Publisher and Journal Title"],
            "subtitle": ["Color-coded by Journal Title within Publisher, most frequent on bottom"],
            "color": "black",
            "subtitleColor": "gray"
        }
        )
st.altair_chart(publisher_chart_by_journaltitle, use_container_width=True)

publisher_chart_by_documenttype = alt.Chart(df[filt]).mark_bar().encode(
    x=alt.X('PU_cleaned:N', sort='-y', title="Publisher"),
    y=alt.Y('count()'),
    color=alt.Color('DT', legend=alt.Legend(title="Document Type")),
    order=alt.Order('count(DT)', sort='ascending'),
    #alt.Detail('index')
    #color=alt.condition(selection1, alt.Color('subscribed:N', scale=subscribed_colorscale), alt.value('lightgray')),   #Nominal data type
    tooltip=['PU_cleaned', 'DT', 'count(DT)'],
    ).interactive().properties(
        height=500,
        title={
            "text": ["Article count by Publisher and Document Type"],
            "subtitle": ["Color-coded by Document Type within Publisher"],
            "color": "black",
            "subtitleColor": "gray"
        }
        )
st.altair_chart(publisher_chart_by_documenttype, use_container_width=True)




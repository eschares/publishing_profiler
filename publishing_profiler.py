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
import altair as alt
import time
import plotly.express as px


st.set_page_config(page_title='Publishing Profiler', layout='centered', initial_sidebar_state="expanded")

st.header("**Publishing Profiler**")
st.subheader("Analyze your campus publishing output")

# either Excel or tab delimited are your choices
# Export WoS data with OG=Iowa State University OR AD=Ames, IA
# Expecting column headers like DT and RP 

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


########  Show information about the raw starting data  ########
st.markdown("""---""")
total_loaded_records = df.shape[0]      #have to save this number off since we need it later and the df will have changed by then
st.subheader(f'Raw Data loaded, Web of Science {total_loaded_records} records')

if st.checkbox('Show Raw Data'):
    st.write(df)

if st.checkbox('Show Raw Distribution of Document Types'):
    st.write(pd.value_counts(df['DT']))
st.markdown("""---""")


########  Show information about removing Document Types (DT) of Editorials, Corrections, etc  ########
# First remove the Book Review type since it contains the word "Review", two variants
df_bookreview_removed = df.loc[(df['DT'].isin(['Book Review', 'Book Review; Early Access']))]
df = df.loc[~(df['DT'].isin(['Book Review', 'Book Review; Early Access']))]

# Then keep Articles, which show up as: 
#     Article; 
#     Article; Data Paper
#     Article; Early Access
# and keep Reviews, which show up as:
#     Review
#     Review; Early Access
# But NOT Book Review since we removed that in the previous step

# Save what you removed
# These "removed" lines have to go first, since df gets changed in the next line
df_removed = df.loc[~((df['DT'].str.contains('Article', case=False, regex=False, na=False)) | (df['DT'].str.contains('Review', case=False, regex=False, na=False)))]
# Combine the Book Reviews with everything NOT Article, Review
frames = [df_removed, df_bookreview_removed]
df_removed = pd.concat(frames)

# Then actually change the df to keep only the wanted DT's
df = df.loc[(df['DT'].str.contains('Article', case=False, regex=False, na=False)) | (df['DT'].str.contains('Review', case=False, regex=False, na=False))]
# Sometimes Article Title is repeated from an Early Access version
df = df.drop_duplicates(subset=['TI'], keep='first', ignore_index=True)


st.subheader('Analyze Document Types')
st.write(f'**Remove** Editorials, Corrections, Book Reviews etc, **{total_loaded_records - df.shape[0]}** records')
if st.checkbox(f'Show Removed Data, {df_removed.shape[0]}' ):
    st.write(df_removed)
if st.checkbox('Show Removed Document Types'):
    st.write(pd.value_counts(df_removed['DT']))

st.write(f'**Keep** Article and Review Types, **{df.shape[0]}** records')
if st.checkbox(f'Show Kept Data'):
    st.write(df)

if st.checkbox('Show Kept Document Types'):
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
st.sidebar.subheader("**CA Filter**")

st.sidebar.write("Corresponding Author is defined as as RP (reprint) column containing Iowa State Univ; Ames Lab; Ames, IA; or USDA")
CA_filt = st.sidebar.radio("Look at Corresponding Authors only?", ("Yes", "No"))

if CA_filt == 'Yes':
    filt = (df['ISU_CA'] == True)
else:
    filt = ( (df['ISU_CA'] == True) | (df['ISU_CA'] == False) )   #show all records, I'm sure there's a better way to do that but oh well

st.sidebar.write(f'{df[filt].shape[0]} rows out of {df.shape[0]} match your criteria')

#############  Clean Publisher names  ###############
df_publisher_list = pd.read_csv('Publisher_list_converter.csv')
df = pd.merge(df_publisher_list, df, on='PU', how='right')      #like a VLOOKUP in Excel, right merge means output dataframe has all rows from 2nd df and matching rows from 1st df. If rows are not matched in 1st df they replaced by NaN

df.to_csv('PU_cleaned_windowin.csv', index=False)


########  Charts start here  ########
st.markdown("""---""")
st.subheader('Charts')

pie_counts = df[filt]['PU_cleaned'].value_counts(dropna=True, sort=True)
df_pie_counts = pd.DataFrame(pie_counts)
df_pie_counts_reset = df_pie_counts.reset_index()
df_pie_counts_reset.columns = ['PU_cleaned', 'count']
df_pie_counts_reset
df_pie_counts_reset.loc[df_pie_counts_reset['count'] < 3, 'PU_cleaned'] = 'Other' # Represent only publishers with at least 5 pubs that year

fig = px.pie(df_pie_counts_reset, values='count', names='PU_cleaned',
             title = 'Article count',
             hover_data=['count'],
             color='PU_cleaned'
)

fig


by_journal = df[filt].groupby('SO')['PU_cleaned'].describe()
df_by_journal = pd.DataFrame(by_journal)
df_by_journal = df_by_journal.reset_index()
df_by_journal.columns = ['Journal', 'count', 'unique', 'PU_cleaned', 'freq']
#df_by_journal

fig2 = px.sunburst(df_by_journal, path=['PU_cleaned', 'Journal'], values = 'count', color='PU_cleaned',
            title = 'Journal titles by publisher',
            width=800, height=800
)
fig2





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




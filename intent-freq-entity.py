import pandas as pd
import nltk
import requests
import json
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
from collections import Counter
import streamlit as st
import base64

st.markdown("""
<style>
.big-font {
    font-size:50px !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<p class="big-font">GSC Query Analysis Tool</p>
<p><b>Label Intent, Entities and Count Keyword Frequency</b></p>
<b>Directions: </b></ br><ol>
<li>Upload CSV of GSC query export (keyword column = "Top queries")</li>
<li>Custom intent could be brand or other query type category or leave blank</li>
<li>Sign up for Google Knowledge Graph <a href='https://developers.google.com/knowledge-graph/how-tos/authorizing'>API Key here</a> (100k free calls per day!)</li>
</ol>
""", unsafe_allow_html=True)

with st.form("user-details"):
    get_queries = st.file_uploader("Upload CSV of GSC query export",type=['csv'])
    custom_list = st.text_input('Custom Intent Words comma delineated (ex Brand variation words)','google,')
    kgkey = st.text_input('Enter Google Knowledge Graph API Key (leave blank if none)','')
    submitted = st.form_submit_button("Process")
    
    if submitted:
        df = pd.read_csv(get_queries)
        total_queries = len(df.index)
        query_list = df['Top queries'].tolist()

        informative = ['what','who','when','where','which','why','how']
        transactional = ['buy','order','purchase','cheap','price','discount','shop','sale','offer']
        commercial = ['best','top','review','comparison','compare','vs','versus','guide','ultimate']
        custom = custom_list.split(",")

        info_filter = df[df['Top queries'].str.contains('|'.join(informative))]
        trans_filter = df[df['Top queries'].str.contains('|'.join(transactional))]
        comm_filter = df[df['Top queries'].str.contains('|'.join(commercial))]
        custom_filter = df[df['Top queries'].str.contains('|'.join(custom))]

        info_filter['Intent'] = "Informational"
        trans_filter['Intent'] = "Transactional"
        comm_filter['Intent'] = "Commercial"
        custom_filter['Intent'] = "Custom"

        info_count = len(info_filter)
        trans_count = len(trans_filter)
        comm_count = len(comm_filter)
        custom_count = len(custom_filter)

        df_intents = pd.concat([info_filter,trans_filter,comm_filter,custom_filter]).sort_values('Clicks', ascending=False)
        df_intents = df_intents.drop_duplicates(subset='Top queries', keep="first")
        
        df_intents = df_intents[ ['Top queries'] + ['Clicks'] + ['Impressions'] + ['Intent'] + ['CTR'] + ['Position'] ]
        
        st.title("Query Intent Table")
        
        st.write("Total Queries: " + str(total_queries))
        st.write("Infomational: " + str(info_count) + " | " + str(round((info_count/total_queries)*100,1)) + "%")
        st.write("Transactional: " + str(trans_count) + " | " + str(round((trans_count/total_queries)*100,1)) + "%")
        st.write("Commercial: " + str(comm_count) + " | " + str(round((comm_count/total_queries)*100,1)) + "%")
        st.write("Custom: " + str(custom_count) + " | " + str(round((custom_count/total_queries)*100,1)) + "%")
        
        def get_csv_download_link(df, title):
            csv = df.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()
            return f'<a href="data:file/csv;base64,{b64}" download="{title}">Download CSV File</a>'
    
        st.markdown(get_csv_download_link(df_intents, "query-intent.csv"), unsafe_allow_html=True)
        
        st.dataframe(df_intents)
        
        if kgkey != "":
            st.write("Working on entities... :sunglasses:")

            ma_query_list = []
            for x in query_list:
              ma_query_list.extend(x.split(" "))

            query_tokens = nltk.pos_tag(ma_query_list)
            query_tokens = [x for x in query_tokens if x[1] in ['NN','NNS','NNP','NNPS','VB','VBD']]
            query_tokens = [x[0] for x in query_tokens]
            total_tokens = len(query_tokens)

            counts = Counter(query_tokens).most_common(50)
            df2 = pd.DataFrame(columns = ['Keyword', 'Count', 'Percent','Entity Labels'])

            def kg(keyword,apikey):
              url = f'https://kgsearch.googleapis.com/v1/entities:search?query={keyword}&key={apikey}&limit=1&indent=True'

              payload = {}
              headers= {}

              response = requests.request("GET", url, headers=headers, data = payload)
              data = json.loads(response.text)

              try:
                getlabel = data['itemListElement'][0]['result']['@type']
              except:
                getlabel = ['none']

              labels = ""
              for item in getlabel:
                labels += item + ","
              return labels

            master_labels = []

            for key, value in counts:
              percent = round((value/total_tokens)*100,1)
            
              kg_label = kg(key,kgkey)
              master_labels.extend(kg_label.rstrip(kg_label[-1]).split(","))
              total_entities = len(master_labels)
            
              data = {'Keyword': key, 'Count': value, 'Percent': percent, 'Entity Labels': kg_label}
              df2 = df2.append(data, ignore_index=True)
              
            st.title("Query Keyword Frequency and Entities")
            
            entity_counts = Counter(master_labels).most_common(5)
            
            st.write("Total Entities: " + str(total_entities))
            for key, value in entity_counts:
                st.write(key + ": " + str(value) + " | " + str(round((value/total_entities)*100,1)) + "%")
 
            st.markdown(get_csv_download_link(df2,"freq-entity.csv"), unsafe_allow_html=True)
            
            st.dataframe(df2)
            
st.write('Author: [Greg Bernhardt](https://twitter.com/GregBernhardt4) | Friends: [Rocket Clicks](https://www.rocketclicks.com), [importSEM](https://importsem.com) and [Physics Forums](https://www.physicsforums.com)')

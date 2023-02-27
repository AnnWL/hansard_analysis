from app_functions import *

st.set_page_config(page_title="Hansard Analysis Tool", layout='wide',page_icon='🔍') 

party_acronyms_dict = read_json("party_acronyms_dict.json")
mp_dict = read_json("mp_dict.json")
mp_list = ['None']
mp_list.extend(mp_dict.values())
res_mp_dict = {v: k for k, v in mp_dict.items()}
agency_theme_dict = read_json('agency_theme_dict.json')
theme_topic_dict = read_json('theme_topic_dict.json')
agency_list = list(agency_theme_dict.keys())
theme_list = ['None']
theme_list.extend(list(theme_topic_dict.keys()))
topic_list = ['None'] 
for topics in theme_topic_dict.values(): topic_list.extend(topics)
topic_list = sorted(list(set(topic_list)))

time_ref_dict = {'3 months': datetime.timedelta(days = 90),'1 year':  datetime.timedelta(days = 365),\
                 '3 years': datetime.timedelta(days = 1096), '5 years': datetime.timedelta(days = 1826)}

overall_df_file = 'pqs_240223.csv'
df_topic_file = 'social_sector_classification_layer2_27022023.csv'
df = df_merge(overall_df_file, df_topic_file, party_acronyms_dict, columns)

current_date = datetime.datetime.strptime('1-2-2023','%d-%m-%Y')
origin_val = 'None'
submit_search = False

params_dict = {
    'phrase':'',
    'theme': origin_val,
    'topic': origin_val,
    'agency': origin_val,
    'MP_name_party': origin_val, 
    'MP_name': origin_val,
    'time_ref_key':origin_val
}

#######
#Input#
#######
st.title("🔍 Hansard Analysis Tool Prototype")
st.markdown("""**_Got an upcoming PQ to staff?_** This tool makes your life as a PQ staffer easier - simply key in information such as the topic of the upcoming PQ and the MP filing the PQ. The Hansard Analysis Tool will surface the relevant information such as the past PQs filed under the topic.""")

instructions = st.sidebar.container()
instructions.markdown("""
**Different ways to use this tool**
1. Agency Search 
2. Keyword/Phrase Search
3. MP Search 
4. Theme/Topic Search
5. Combinations of #1 to #4
-----""") 

input_container = st.sidebar.container()
input_container.write('**Input Parameters**')
params_dict['agency'] = input_container.selectbox('Agency', agency_list, index = 0, key='agency') 
params_dict['phrase'] = input_container.text_input('Keyword Search')
params_dict['MP_name_party'] = input_container.selectbox('MP', mp_list)

if params_dict['MP_name_party']!='None':
    params_dict['MP_name'] = res_mp_dict[params_dict['MP_name_party']]

theme_help = "Too many values? You may wish to impute an agency value first, to get a shortlist of policy themes under the agency's purview."
topic_help = "You may wish to impute a theme first, to get a list of topics specific to the theme."

if params_dict['agency']!='None': 
    params_dict['theme'] = input_container.selectbox('Theme', list(agency_theme_dict[params_dict['agency']]))
else: 
    params_dict['theme'] = input_container.selectbox('Theme', theme_list, index = theme_list.index('None'), help = theme_help)

if params_dict['theme']!='None': 
    params_dict['topic'] = input_container.selectbox('Topic', theme_topic_dict[params_dict['theme']])
else: 
    params_dict['topic'] = input_container.selectbox('Topic', topic_list, index = topic_list.index('None'), help = topic_help)

params_dict['time_ref_key'] = input_container.selectbox('Look for PQs from the past..', list(time_ref_dict.keys()), index=2)
params_dict['reference_date'] = current_date - time_ref_dict[params_dict['time_ref_key']]
submit_search = input_container.button('🔍 Search')
st.sidebar.markdown("""---""")
params_combi, changed_params = get_impute_values(params_dict,origin_val)

if st.session_state.get('submit_search_button') != True:
    st.session_state['submit_search_button'] = submit_search

########
#Output#
########

if st.session_state["submit_search_button"]: 

    output_container1 = st.container()
    output_container1.subheader("RESULTS")
    df_slice =  get_df_slice(df, params_dict)

    summary_str = generate_summary_string(df_slice.shape[0], changed_params)
    output_container1.write(summary_str) 

    if df_slice.shape[0]>0: 
        #generate_folder(df_slice, changed_params) #this takes around 2 secs
        gen_brief = output_container1.checkbox('Export these PQs')
        output_container2 = st.container()
        if len(params_combi)>=3:
            print_output(df_slice,output_container2)

        else:

            tab_stats, tab_result = output_container2.tabs(['Summary Statistics', 'Search Results'])
            
            print_output(df_slice,tab_result)
            

            if params_combi=={'agency'}:            
                title_val = generate_time_series_title(changed_params)
                if (df_slice[df_slice.Is_PAP].shape[0]>0) & (df_slice[~df_slice.Is_PAP].shape[0]>0): 
                    fig_time = time_trend_PAP(df_slice, title_val)
                else: 
                    fig_time = time_trend(df_slice, title_val)
                tab_stats.pyplot(fig_time)

                tab_stats.markdown('##')

                title_val = 'Most Active MPs'
                parameter = 'asker_name'
                tab_stats.pyplot(bar_chart(df_slice, parameter, title_val)) 

                tab_stats.markdown('##')

                title_val = 'Most Popular Themes' 
                parameter = 'theme'
                tab_stats.pyplot(bar_chart(df_slice, parameter, title_val)) 

                tab_stats.markdown('##')

                title_val = 'Most Popular Topics' 
                parameter = 'question_topic_label' 
                tab_stats.pyplot(bar_chart(df_slice, parameter, title_val)) 

            if params_combi== {"phrase"}:             
                title_val = generate_time_series_title(changed_params)
                if (df_slice[df_slice.Is_PAP].shape[0]>0) & (df_slice[~df_slice.Is_PAP].shape[0]>0): 
                    fig_time = time_trend_PAP(df_slice, title_val)
                else: 
                    fig_time = time_trend(df_slice, title_val)
                tab_stats.pyplot(fig_time)

                tab_stats.markdown('##')

                title_val = "Top Ministries"
                fig_ministry = bar_chart(df_slice, 'ministry', title_val)
                tab_stats.pyplot(fig_ministry)

                title_val = 'Most Active MPs'
                fig = bar_chart(df_slice, 'asker_name', title_val)
                tab_stats.pyplot(fig)

            if params_combi== {"MP_name"}:             
                title = generate_time_series_title(changed_params)
                fig_time = time_trend(df_slice, title)
                tab_stats.pyplot(fig_time)

                tab_stats.markdown('##')

                title_val = "Top Ministries"
                fig_ministry = bar_chart(df_slice, 'ministry', title_val)
                tab_stats.pyplot(fig_ministry)

            if (params_combi=={'theme'}) or (params_combi=={'theme', 'agency'}):  
                title_val = generate_time_series_title(changed_params)
                if (df_slice[df_slice.Is_PAP].shape[0]>0) & (df_slice[~df_slice.Is_PAP].shape[0]>0): 
                    fig_time = time_trend_PAP(df_slice, title_val)
                else: 
                    fig_time = time_trend(df_slice, title_val)
                tab_stats.pyplot(fig_time)

                title_val = 'Most Active MPs'
                parameter = 'asker_name'
                tab_stats.pyplot(bar_chart(df_slice, parameter, title_val))

                tab_stats.markdown('##')

                title_val = 'Most Popular Topics' 
                parameter = 'question_topic_label' 
                tab_stats.pyplot(bar_chart(df_slice, parameter, title_val)) 

            if params_combi=={'topic'} or (params_combi=={'topic', 'agency'}) or (params_combi=={'topic', 'agency'})\
            or (params_combi=={'topic', 'theme'}): 
                title_val = generate_time_series_title(changed_params)
                if (df_slice[df_slice.Is_PAP].shape[0]>0) & (df_slice[~df_slice.Is_PAP].shape[0]>0): 
                    fig_time = time_trend_PAP(df_slice, title_val)
                else: 
                    fig_time = time_trend(df_slice, title_val)
                tab_stats.pyplot(fig_time)

                title_val = 'Most Active MPs'
                parameter = 'asker_name'
                tab_stats.pyplot(bar_chart(df_slice, parameter, title_val))

            if params_combi== {"phrase","agency"}:          
                title_val = generate_time_series_title(changed_params)
                if (df_slice[df_slice.Is_PAP].shape[0]>0) & (df_slice[~df_slice.Is_PAP].shape[0]>0): 
                    fig_time = time_trend_PAP(df_slice, title_val)
                else: 
                    fig_time = time_trend(df_slice, title_val)
                tab_stats.pyplot(fig_time)

                tab_stats.markdown('##')

                title_val = 'Most Active MPs'
                parameter = 'asker_name'
                tab_stats.pyplot(bar_chart(df_slice, parameter, title_val))

            if params_combi=={'MP_name', 'agency'}:
                title = generate_time_series_title(changed_params)
                fig_time = time_trend(df_slice, title)
                tab_stats.pyplot(fig_time)

                tab_stats.markdown('##')

                title_val = 'Most Popular Themes' 
                parameter = 'theme'
                tab_stats.pyplot(bar_chart(df_slice, parameter, title_val))   

                tab_stats.markdown('##')

                title_val = 'Most Popular Topics' 
                parameter = 'question_topic_label' 
                tab_stats.pyplot(bar_chart(df_slice, parameter, title_val)) 

            if params_combi=={'MP_name', 'phrase'}:
                title = generate_time_series_title(changed_params)
                fig_time = time_trend(df_slice, title)
                tab_stats.pyplot(fig_time)

                tab_stats.markdown('##')

                title_val = "Top Ministries"
                fig_ministry = bar_chart(df_slice, 'ministry', title_val)
                tab_stats.pyplot(fig_ministry)

                tab_stats.markdown('##')

                title_val = 'Most Popular Themes' 
                parameter = 'theme'
                tab_stats.pyplot(bar_chart(df_slice, parameter, title_val))   

                tab_stats.markdown('##')

                title_val = 'Most Popular Topics' 
                parameter = 'question_topic_label' 
                tab_stats.pyplot(bar_chart(df_slice, parameter, title_val)) 

            if (params_combi=={'phrase', 'theme'}) or (params_combi=={'phrase', 'topic'}):
                title = generate_time_series_title(changed_params)
                fig_time = time_trend(df_slice, title)
                tab_stats.pyplot(fig_time)

                tab_stats.markdown('##')

                title_val = "Top Ministries"
                fig_ministry = bar_chart(df_slice, 'ministry', title_val)
                tab_stats.pyplot(fig_ministry)

                tab_stats.markdown('##')

                title_val = 'Most Active MPs'
                parameter = 'asker_name'
                tab_stats.pyplot(bar_chart(df_slice, parameter, title_val))

            if (params_combi=={'theme', 'MP_name'}) or (params_combi=={'topic', 'MP_name'}):   
                title = generate_time_series_title(changed_params)
                fig_time = time_trend(df_slice, title)
                tab_stats.pyplot(fig_time)

                tab_stats.markdown('##')

                title_val = "Top Ministries"
                fig_ministry = bar_chart(df_slice, 'ministry', title_val)
                tab_stats.pyplot(fig_ministry)
        
        if gen_brief: 
            with output_container1:
                with st.spinner('Exporting PQs...'):
                    output_directory = generate_folder(df_slice, changed_params)
                    with open(output_directory+'.zip', "rb") as fp:
                        folder_name_val = output_directory.split('/')[-1]
                        btn = st.download_button(
                            label="Download Background Briefs",
                            data=fp,
                            file_name=folder_name_val+".zip",
                            mime="application/zip")
                        
                    if os.path.exists(output_directory+'.zip'):
                        os.remove(output_directory+'.zip')
                        shutil.rmtree(output_directory)
                
               

                
            









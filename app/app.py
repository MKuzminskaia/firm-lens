import streamlit as st
import pandas as pd
import json as js
import os

from core.models import Company
from core.services import WikidataService, ScorerService
from core.utils import clean_str, convert_df_to_csv, load_rules, save_rules


st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        min-width: 300px;
        max-width: 300px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("0.7 Layer")
st.header("Firm-Lens")


ENRICH = {
    "enriched_description": "...",
    "enriched_website": "...",
    "enriched_country": "...",
    "enriched_industry": "...",
    "enrich_status": "not_found",  # "hit" | "not_found" | "error",
    "enrich_source": "wikidata"
}

SEARCH_INFO = {
    'company_name' : 'empty',  
    'website' : 'empty',  
    'country' : 'empty'
}

COMPANY_LIST_FOR_ENRICHING = [
    {
        'company_name' : 'empty', 
        'company_id': 'empty',
        'website' : 'empty', 
        'country' : 'empty',
        'industry' : 'empty',
    }
]

if "enrich" not in st.session_state:
    st.session_state.enrich = ENRICH.copy()
# information entered into input fields
if "search_info" not in st.session_state:
    st.session_state.search_info = SEARCH_INFO.copy()
# list of searching companies by name and another parameters    
if "founded_list_of_companies" not in st.session_state:
    st.session_state.founded_list_of_companies = ['']
# one selected current firm   
if "selected_companies_for_enriching" not in st.session_state:
    st.session_state.selected_companies_for_enriching = ''
# Finaly list of companies    
if "company_list_for_enriching" not in st.session_state:
    st.session_state.company_list_for_enriching = []                            

final_company_list : list[Company] = []


# sidebar with rules for scoring

if 'rules_initialized' not in st.session_state:
    data = load_rules()
    st.session_state.pos_rules_list = data["pos"]
    st.session_state.neg_rules_list = data["neg"]
    st.session_state.rules_initialized = True


with st.sidebar:
    #st.subheader("Scoring Rules Configuration")
    with st.expander("Scoring Rules Configuration", expanded = False):
        st.markdown("Positive rules:")
        edited_pos = st.data_editor(
            st.session_state.pos_rules_list,
            num_rows="dynamic",
            key = "pos_editor",
            use_container_width=True,
            hide_index=True,
            column_config={
            "Keyword": st.column_config.TextColumn("Keyword", help="Word to find", required=True),
            "Points": st.column_config.NumberColumn("Points", help="Score for this word", format="%d")
        }
        )

        pos_rules_dict = [
            {
                "Keyword" : row["Keyword"],
                "Points" : abs(row["Points"]) if str(row.get("Points")).isdigit() else 0
            }

            for row in edited_pos 
            if isinstance(row, dict) and row.get("Keyword") and row.get("Keyword") != '' and row.get("Points") != 'NaN'
        
        ]

        st.session_state.pos_rules_list = pos_rules_dict

        st.markdown("Negative rules:")
        edited_neg = st.data_editor(
            st.session_state.neg_rules_list,
            num_rows="dynamic",
            key = "neg_editor",
            use_container_width=True,
            hide_index=True,
            column_config={
            "Keyword": st.column_config.TextColumn("Keyword", help="Word to find", required=True),
            "Points": st.column_config.NumberColumn("Points", help="Score for this word", format="%d")
        }
        )

        neg_rules_dict = [
            {
                "Keyword" : row["Keyword"],
                "Points" : -abs(row["Points"]) if str(row.get("Points")).lstrip("-").isdigit() else 0
            }

            for row in edited_neg 
            if isinstance(row, dict) and row.get("Keyword") and row.get("Keyword") != '' and row.get("Points") != 'NaN'
        
        ]

        st.session_state.neg_rules_list = neg_rules_dict

        if st.button("Save Rules", key="btn_save_rules"):
            save_rules(pos_rules_dict, neg_rules_dict) 


st.write("Select the method for selecting a list of companies:")

col1, col2 = st.columns(2)
with col1: 
    # menu for company info entering
    with st.container(border=True):
        company_name = clean_str(st.text_input("\* Enter the company name: ", "Google inc"))
        website = st.text_input("Enter the company website : ", "https://about.google/")
        country = st.text_input("Enter the company country: ")

        search_info = {
            'company_name' : company_name,  
            'website' : website,  
            'country' : country
        }

        results_df = pd.DataFrame([search_info])

        if "wiki_service" not in st.session_state: 
            st.session_state.wiki_service = WikidataService()
        
        if st.button("Submit", key = 'btn_search_company_by_name'):
            try:
                final_company_list = st.session_state.wiki_service.search_companies(search_info['company_name'], search_info['website'], '')
                data_for_table = [rare.to_dict() for rare in final_company_list]
                results_df = pd.DataFrame(data_for_table)
                st.session_state['founded_list_of_companies'] = data_for_table
            except Exception as e:
                st.write(e)   

with col2:  
    # analyzing file 
    with st.container(border=True):
        column: str
        uploaded_file = st.file_uploader("Select file for analyzing:", type='csv', key='analyzing_file')
        if uploaded_file is not None:
            results = pd.read_csv(uploaded_file, sep= ';')
            table_columns = results.columns

            st.session_state['founded_list_of_companies_from_file'] = results.to_dict(orient='records')

            with st.expander("Downloaded info from file"):
                st.dataframe(st.session_state.founded_list_of_companies_from_file)

            column = st.selectbox("Select column with company name id for searching:",
                                table_columns)
            
        
        # if st.button("Submit", key = 'btn_search_company_from_File'):
        
        #     if uploaded_file and column:
        #         try:
        #             companies_names = results[column]
        #             for company in companies_names:
        #                 company_info = st.session_state.wiki_service.search_companies(company, '', '')
        #                 final_company_list.append(company_info[0])  
        #             data_for_table = [rare.to_dict() for rare in final_company_list]
        #             results_df = pd.DataFrame(data_for_table)
        #             st.session_state['founded_list_of_companies'] = data_for_table
        #             st.success('File downloaded')
        #         except Exception as e:
        #             st.write(e)




with st.container(border=True):
    selected_rows = []
    # enriching list of new selected companies
    if 'founded_list_of_companies' in st.session_state:
        df = pd.DataFrame(st.session_state['founded_list_of_companies'])
        s = st.dataframe(df, 
                selection_mode="multi-row", 
                on_select="rerun", 
                column_config = {'company_id' : None}
                )
        selected_rows = s['selection']['rows']
    
    if 'founded_list_of_companies_from_file' in st.session_state:
        df = pd.DataFrame(st.session_state['founded_list_of_companies_from_file'])
        
        for i in range( len(df)):
            selected_rows.append(i)   


    # choosing columns for scoring 
    table_columns = COMPANY_LIST_FOR_ENRICHING[0].keys()
    table_columns_name = st.multiselect(
        "Select column name of table for enriching: ",
        table_columns,
    )
    st.session_state['table_columns_name'] = table_columns_name
    

    enriched_data = []
    if st.session_state['company_list_for_enriching']:
        enriched_data = st.session_state['company_list_for_enriching']

    if not table_columns_name:
        st.error("Choose at least one column name for further work")
    elif st.button("Submit", key = 'btn_submit_choosen_list_for_enriching') and st.session_state['table_columns_name']: # or (uploaded_file and column)) and selected_rows:
        with st.spinner("Searching data in Wikidata..."):
            for row_number in selected_rows:
                row = df.iloc[row_number].to_dict()  
                new_data = st.session_state.wiki_service.enrich_company(row['company_id'], '', '').to_dict()
                enriched_data.append(new_data)
            st.session_state['company_list_for_enriching'] = enriched_data    

    # generating final table (enriched with scoring)
    if st.session_state['company_list_for_enriching']:
        try:
            
            final_df = pd.DataFrame(enriched_data)
            
            if not table_columns_name:
                table_columns_name = st.session_state['table_columns_name']
            final_df[['score', 'reasons']] = (
                final_df[table_columns_name]
                .fillna("")
                .astype(str)
                .agg(" ".join , axis=1)
                .apply(lambda x: ScorerService.calculate_score(x, st.session_state.pos_rules_list, st.session_state.neg_rules_list))
                .apply(pd.Series))

            if enriched_data:     
                
                st.subheader("Result of deep analysis:")
                st.table(final_df) 


                # Download *.csv file 
                csv = convert_df_to_csv(final_df)
                file_name = "firm_lens_report"
                st.download_button(
                    label = "Download CSV",
                    data = csv,
                    file_name=f"{file_name}_{pd.Timestamp.now().strftime('%Y-%m-%d-%H-%M')}.csv",
                    mime="text/csv",
                    key='download-csv'
                )

        except Exception as e:
            st.write(e)
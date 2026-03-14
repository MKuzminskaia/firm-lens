import streamlit as st
import pandas as pd
import json as js
import os

from core.models import Company, SearchMode
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

st.title("0.8 Layer")
st.header("Firm-Lens")


# Default State
#--------------------------------------------------------------------------------------------------------

rules_data = load_rules()   # loading scoring rules from file if it exists

if 'initial_check' not in st.session_state:
    st.session_state.pos_rules_list = rules_data["pos"]     # positive rules initialisation
    st.session_state.neg_rules_list = rules_data["neg"]     # negative rules initialisation

    st.session_state.wiki_service = WikidataService()       # WikidataService inicialisation (for searching and enriching)

    st.session_state.founded_list_of_companies = ['']       # list of searching companies by name and another parameters
    st.session_state.company_list_for_enriching = []        # Finaly list of companies  
    st.session_state.enrichment_columns = []                # Columns names for enriching 

    st.session_state.initial_check = True                   # Flag we initialised main variables

    st.session_state.founded_list_of_companies_from_file = dict()  #

    st.session_state.search_mode = SearchMode.NOT_DEFINED   # Search mode : individual or by file

COMPANY_LIST_FOR_ENRICHING = [
    {
        'company_name' : 'empty', 
        'company_id': 'empty',
        'website' : 'empty', 
        'country' : 'empty',
        'industry' : 'empty',
    }
]
                               

final_company_list : list[Company] = []

# generating final table with scoring
def final_result():
    if st.session_state['company_list_for_enriching']:
        try:
            
            final_df = pd.DataFrame(st.session_state.company_list_for_enriching)
            
            enrichment_columns = st.session_state['enrichment_columns']
            final_df[['score', 'reasons']] = (
                final_df[enrichment_columns]
                .fillna("")
                .astype(str)
                .agg(" ".join , axis=1)
                .apply(lambda x: ScorerService.calculate_score(x, st.session_state.pos_rules_list, st.session_state.neg_rules_list))
                .apply(pd.Series))

            if enriched_data:     
                
                st.subheader("Result of deep analysis:")
                #st.table(final_df) 
                st.dataframe(final_df,
                             column_config={
                                "company_id" : None,
                                "company_name": st.column_config.TextColumn("Company Name", width="medium"),
                                "website": st.column_config.LinkColumn("Website", width="medium"),
                                "country": st.column_config.TextColumn("Country", width="medium"),
                                "score": st.column_config.NumberColumn("Score",),
                                "reasons": st.column_config.TextColumn("Analysis Details", width="large")
                                },
                             hide_index=True,
                             )

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


# sidebar with rules for scoring
#--------------------------------------------------------------------------------------------------------
with st.sidebar:
    with st.expander("Scoring Rules Configuration", expanded = False):
        st.markdown("Positive rules:")

        # Table of positive rules 
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
        
        # Table of negative rules
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

        # save changed rules to file and in session_state
        if st.button("Save Rules", key="btn_save_rules"):
            pos_rules_list = [
                {
                    "Keyword" : row["Keyword"],
                    "Points" : abs(row["Points"]) if str(row.get("Points")).isdigit() else 0
                }
                for row in edited_pos 
                if isinstance(row, dict) and row.get("Keyword") and row.get("Keyword") != '' and row.get("Points") != 'NaN'
            ]

            neg_rules_list = [
                {
                    "Keyword" : row["Keyword"],
                    "Points" : -abs(row["Points"]) if str(row.get("Points")).lstrip("-").isdigit() else 0
                }
                for row in edited_neg 
                if isinstance(row, dict) and row.get("Keyword") and row.get("Keyword") != '' and row.get("Points") != 'NaN'
            ]

            save_rules(pos_rules_list, neg_rules_list) 
            st.session_state.pos_rules_list = pos_rules_list
            st.session_state.neg_rules_list = neg_rules_list


st.write("Select the method for selecting a list of companies:")



tab1, tab2 = st.tabs(["Search by company name",
                      "Search by File"])
with tab1: 
    # menu for company info entering
    with st.container(border=True):
        company_name = clean_str(st.text_input("\* Enter the company name: ", placeholder="ex. Google inc"))
        website = st.text_input("Enter the company website : ", "https://", placeholder="ex. https://about.google/")
        country = st.text_input("Enter the company country: ")

        search_info = {
            'company_name' : company_name,  
            'website' : website,  
            'country' : country
        }

        results_df = pd.DataFrame([search_info])
        if company_name: dis_button = False
        else: dis_button = True 
        
        if st.button("Submit", 
                     key = 'btn_search_company_by_name',
                     disabled = dis_button):
            try:
                final_company_list = st.session_state.wiki_service.search_companies(search_info['company_name'], search_info['website'], '')
                data_for_table = [rare.to_dict() for rare in final_company_list]
                results_df = pd.DataFrame(data_for_table)
                st.session_state['founded_list_of_companies'] = data_for_table
                st.session_state.search_mode = SearchMode.INDIVIDUAL
            except Exception as e:
                st.write(e)   

        if st.session_state.search_mode != SearchMode.NOT_DEFINED:  
            with st.container(border=True):
                selected_rows = []
                # enriching list of new selected companies in INDIVIDUAL search mode
                if st.session_state.search_mode == SearchMode.INDIVIDUAL and 'founded_list_of_companies' in st.session_state:
                    df = pd.DataFrame(st.session_state['founded_list_of_companies'])
                    s = st.dataframe(df, 
                            selection_mode="multi-row", 
                            on_select="rerun", 
                            column_config = {'company_id' : None}
                            )
                    selected_rows = s['selection']['rows']

                if st.session_state.search_mode == SearchMode.INDIVIDUAL:
                # choosing columns for enriching 
            
                    table_columns = COMPANY_LIST_FOR_ENRICHING[0].keys()
                    enrichment_columns = st.multiselect(
                        "Select column name of table for enriching: ",
                        table_columns,
                    )
                    st.session_state['enrichment_columns'] = enrichment_columns
                    enriched_data = st.session_state.company_list_for_enriching

                    if not enrichment_columns:
                        st.error("Choose at least one column name for further work")
                    elif st.button("Submit", key = 'btn_submit_choosen_list_for_enriching') and st.session_state['enrichment_columns']:
                        #with st.spinner("Searching data in Wikidata..."):
                        
                        progress_iterator = 0
                        my_bar = st.progress(progress_iterator, text="Enriching progress")
                        for row_number in selected_rows:
                            row = df.iloc[row_number].to_dict()  
                            new_data = st.session_state.wiki_service.enrich_company(row['company_id'], '', '').to_dict()
                            enriched_data.append(new_data)
                            progress_iterator+=1
                            my_bar.progress(value=int(progress_iterator*100/len(selected_rows)), text="Enriching progress")
                        my_bar.empty()    
                        st.session_state.company_list_for_enriching = enriched_data    
                        final_result()


with tab2:  
    # analyzing file and selecting enriching parameters
    with st.container(border=True):
        column: str
        uploaded_file = st.file_uploader("Select file for analyzing:", type='csv', key='analyzing_file')
        if uploaded_file is not None:
            results = pd.read_csv(uploaded_file, sep=None, engine='python')
            table_columns = results.columns

            st.session_state['founded_list_of_companies_from_file'] = results.to_dict(orient='records')

            with st.expander("Downloaded info from file"):
                st.dataframe(st.session_state.founded_list_of_companies_from_file)

            file_column_name = st.selectbox("Select column with company name id for searching:",
                                table_columns)
            
            file_columns_enrich = st.multiselect("Select column names for enriching: ",
                                table_columns)
            st.session_state.enrichment_columns = file_columns_enrich
            
            if file_columns_enrich: dis_button = False
            else: dis_button = True

            if st.button(
                label="Quick search",
                key="quick_search_by_file",
                disabled = dis_button
            ): st.session_state.search_mode = SearchMode.BY_FILE            # further enrichment is carried out according to the file data


            if st.session_state.search_mode != SearchMode.NOT_DEFINED:  
                with st.container(border=True):
                    # enriching list of companies in BY_FILE search mode
                    selected_rows = []
                    if st.session_state.search_mode == SearchMode.BY_FILE and 'founded_list_of_companies_from_file' in st.session_state:
                        df = pd.DataFrame(st.session_state['founded_list_of_companies_from_file'])
                        for i in range( len(df)):
                            selected_rows.append(i)   

                    if st.session_state.search_mode == SearchMode.BY_FILE:
                        enriched_data = st.session_state.company_list_for_enriching
                        progress_iterator = 0
                        my_bar = st.progress(progress_iterator, text="Enriching progress")
                        #with st.spinner("Searching data in Wikidata..."):
                        for row_number in selected_rows:
                            row = df.iloc[row_number].to_dict()  
                            new_data = st.session_state.wiki_service.enrich_company(row['company_id'], '', '').to_dict()
                            enriched_data.append(new_data)
                            progress_iterator+=1
                            my_bar.progress(value=int(progress_iterator*100/len(selected_rows)), text="Enriching progress")
                            
                        my_bar.empty()
                        st.session_state.company_list_for_enriching = enriched_data  
                        final_result()

       
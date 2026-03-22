import streamlit as st
import pandas as pd
import json as js
from dataclasses import fields
import os
import config

from core.models import Company, SearchMode
from core.services import WikidataService, ScorerService
from core.utils import clean_str, convert_df_to_csv, load_rules, save_rules, convert_df_to_excel


st.markdown(f"""
    <style>
    [data-testid="stSidebar"] {{
        min-width: {config.SIDEBAR_MIN_WIDTH};
        max-width: {config.SIDEBAR_MAX_WIDTH};
    }}
    </style>
    """, unsafe_allow_html=True)

st.title(config.APP_TITLE)


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

    st.session_state.file_column_company_id = ''            # Selected company id for searching in file
    st.session_state.file_column_company_name = ''          # Selected company name for searching in file
    st.session_state.file_column_country = ''               # Selected country for searching in file
    st.session_state.file_column_website = ''               # Selected website id for searching in file
    
                               

final_company_list : list[Company] = []

def show_result_Table():
    final_result()
    if st.session_state.company_list_for_enriching:     
        final_df = pd.DataFrame(st.session_state.company_list_for_enriching)        
        st.subheader("Result of deep analysis:")
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
                        use_container_width=True
                        )
            
        col1, col2 = st.columns(2)
        file_name = config.EXPORT_FILE_PREFIX
        with col1:
            # Download *.csv file 
            csv = convert_df_to_csv(final_df)
            st.download_button(
                label = "Download CSV",
                data = csv,
                file_name=f"{file_name}_{pd.Timestamp.now().strftime('%Y-%m-%d-%H-%M')}.csv",
                mime=config.CSV_MIME_TYPE,
                key=f"download_csv_{st.session_state.get('search_mode')}"
            )
        with col2:
            # Generate Excel file
            excel_data = convert_df_to_excel(final_df)
            st.download_button(
                label="Download Excel Report",
                data=excel_data,
                file_name=f"{file_name}_{pd.Timestamp.now().strftime('%Y-%m-%d-%H-%M')}.xlsx",
                mime=config.EXCEL_MIME_TYPE,
                key=f"download_excel_{st.session_state.get('search_mode')}"
            )
        return True
    return False    


# generating final table with scoring
#---------------------------------------------------------------------------------------------------------
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
            
            for i, company_obj in enumerate(st.session_state.company_list_for_enriching):
                company_obj.score = final_df.at[i, 'score']
                company_obj.reasons = final_df.at[i, 'reasons']

            #st.session_state.company_list_for_enriching = final_df.to_dict(orient='records')
        except Exception as e:
            st.write(e)


# prepare table from file: enriching
#---------------------------------------------------------------------------------------------------------
def enrich_prepare():
    with st.container(border=True):
        # enriching list of companies in BY_FILE search mode
        selected_rows = []
        #if st.session_state.search_mode == SearchMode.BY_FILE and 'founded_list_of_companies_from_file' in st.session_state:
        if 'founded_list_of_companies_from_file' in st.session_state:
        
            df = pd.DataFrame(st.session_state['founded_list_of_companies_from_file'])
            for i in range( len(df)):
                selected_rows.append(i)   


        #if st.session_state.search_mode == SearchMode.BY_FILE:
        enriched_data = st.session_state.company_list_for_enriching
        progress_iterator = 0
        my_bar = st.progress(progress_iterator, text="Enriching progress")
        new_data : Company
        for row_number in selected_rows:
            try:
                row = df.iloc[row_number].to_dict()  
                current_company_id = row['company_id']
                new_data = st.session_state.wiki_service.enrich_company(current_company_id, '', '') #.to_dict()
                # check whether the new company is already included or not
                if any(c.company_id == current_company_id for c in enriched_data):
                    pass
                else: 
                    enriched_data.append(new_data)
            except Exception as e:
                st.warning(e)
            progress_iterator+=1
            my_bar.progress(value=int(progress_iterator*100/len(selected_rows)), text="Enriching progress")
            
        my_bar.empty()
        st.session_state.company_list_for_enriching = enriched_data  
        final_result()

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
            if st.session_state.get('search_mode') != SearchMode.INDIVIDUAL:
                st.session_state.company_list_for_enriching = []
                st.session_state.search_mode = SearchMode.INDIVIDUAL

            try:
                with st.spinner("In process"):
                    final_company_list = st.session_state.wiki_service.search_companies(search_info['company_name'], search_info['website'], search_info['country'])
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
            
                    table_columns = [f.name for f in fields(Company)]
                    if 'score' in table_columns:
                        table_columns.remove('score')
                    if 'reasons' in table_columns:
                        table_columns.remove('reasons')
                    
                    enrichment_columns = st.multiselect(
                        "Select column name of table for enriching: ",
                        table_columns,
                    )
                    st.session_state['enrichment_columns'] = enrichment_columns
                    enriched_data = st.session_state.company_list_for_enriching

                    if not enrichment_columns:
                        st.error("Choose at least one column name for further work")
                    elif st.button("Submit", key = 'btn_submit_choosen_list_for_enriching') and st.session_state['enrichment_columns']:
                        
                        progress_iterator = 0
                        my_bar = st.progress(progress_iterator, text="Enriching progress")
                        for row_number in selected_rows:
                            try:
                                row = df.iloc[row_number].to_dict()  
                                
                                current_company_id = row['company_id']
                                new_data = st.session_state.wiki_service.enrich_company(current_company_id, '', '') #.to_dict()
                                # check whether the new company is already included or not
                                if any(c.company_id == current_company_id for c in enriched_data):
                                    pass
                                else: 
                                    enriched_data.append(new_data)
                            except Exception as e:
                                st.warning(f"Error after enriched_data build: {e}")
                            progress_iterator+=1
                            my_bar.progress(value=int(progress_iterator*100/len(selected_rows)), text="Enriching progress")
                        my_bar.empty()    
                        st.session_state.company_list_for_enriching = enriched_data    

            if st.session_state.search_mode == SearchMode.INDIVIDUAL:
                show_result_Table()


with tab2:  
    # analyzing file and selecting enriching parameters
    with st.container(border=True):
        column: str
        uploaded_file = st.file_uploader("Select file for analyzing:", type='csv', key='analyzing_file')
        if uploaded_file  is not None:
            
            #st.session_state.search_mode = SearchMode.BY_FILE

            results = pd.read_csv(uploaded_file, sep=None, engine='python')
            
            table_columns = [f.name for f in fields(Company)]
            if 'score' in table_columns:
                table_columns.remove('score')
            if 'reasons' in table_columns:
                table_columns.remove('reasons')
                    

            st.session_state['founded_list_of_companies_from_file'] = results.to_dict(orient='records')

            with st.expander("Downloaded info from file"):
                st.dataframe(st.session_state.founded_list_of_companies_from_file)

            file_column_company_id = st.selectbox("Select column with company id for searching:",
                                table_columns,
                                index=None,
                                placeholder="Select company id column..."
                                )
            if file_column_company_id:
                st.session_state.file_column_company_id = file_column_company_id
            else: 
                st.session_state.file_column_company_id = ''
            st.write(st.session_state.file_column_company_id)

            file_column_company_name = st.selectbox("Select column with company name for searching:",
                                table_columns,
                                index=None,
                                placeholder="Select company name column..."
                                )
            if file_column_company_name:
                st.session_state.file_column_company_name = file_column_company_name
            else: 
                st.session_state.file_column_company_name = ''

            file_column_website = st.selectbox("Select column with company website for searching:",
                                table_columns,
                                index=None,
                                placeholder="Select company website column..."
                                )
            if file_column_website:
                st.session_state.file_column_website = file_column_website
            else: 
                st.session_state.file_column_website = ''

            file_column_country = st.selectbox("Select column with company country for searching:",
                                table_columns,
                                index=None,
                                placeholder="Select company country column..."
                                )
            if file_column_country:
                st.session_state.file_column_country = file_column_country
            else: 
                st.session_state.file_column_country = ''

            file_columns_enrich = st.multiselect("Select column names for enriching: ",
                                table_columns)
            st.session_state.enrichment_columns = file_columns_enrich
            
            if file_columns_enrich and file_column_company_name: dis_button = False
            else: dis_button = True

            if st.button(
                label="Quick search",
                key="quick_search_by_file",
                disabled = dis_button
            ): 
                if st.session_state.get('search_mode') != SearchMode.BY_FILE:
                    st.session_state.company_list_for_enriching = [] 
                    st.session_state.founded_list_of_companies = [''] 
                    st.session_state.search_mode = SearchMode.BY_FILE

                enriched_data = []
                progress_iterator = 0
                my_bar = st.progress(progress_iterator, text="Enriching progress")
                for comp in st.session_state.founded_list_of_companies_from_file:
                    if st.session_state.file_column_company_name:
                        company_name = comp[file_column_company_name]
                    else:
                        company_name = ''
                    if st.session_state.file_column_website:
                        website = comp[file_column_website]
                    else: 
                        website = ''
                    if st.session_state.file_column_country:  
                        country = comp[file_column_country]
                    else:     
                        country = ''
                    enriched_data.append(st.session_state.wiki_service.process_raw_company(company_name, website, country))
                    my_bar.progress(value=int(progress_iterator*100/len(st.session_state.founded_list_of_companies_from_file)), text="Enriching progress")
                    progress_iterator+=1
                my_bar.empty()  
                st.session_state.company_list_for_enriching = enriched_data
                show_result_Table()
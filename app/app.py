import streamlit as st
import pandas as pd
import json as js

from core.models import Company
from core.services import WikidataService, ScorerService
from core.utils import clean_str, rules_to_str, rules_parser, convert_df_to_csv

st.title("0.6 Layer")
st.header("Firm-Lens")

#uploaded_file = st.file_uploader("Upload data", type="csv")

POS_RULES = {
    "medical": 30,
    "health": 25,
    "clinic": 20,
    "ai": 10,
    "internet": 10,
}

NEG_RULES = {
    "gambling": -100,
    "adult": -100,
}

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

# session_state default values
if "pos_rules" not in st.session_state: 
    st.session_state.pos_rules = POS_RULES.copy()
if "neg_rules" not in st.session_state:
    st.session_state.neg_rules = NEG_RULES.copy()
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
with st.sidebar:
    txt_pos = st.text_area(
        "Write positive rules:",
        rules_to_str(st.session_state["pos_rules"]),
        height="content"
    )
    txt_neg = st.text_area(
        "Write negative rules:",
        rules_to_str(st.session_state["neg_rules"]),
        height="content"
    )
    apply = st.button(
        label="Apply"
    )

    if apply: 
        st.session_state["pos_rules"] = rules_parser(txt_pos)
        st.session_state["neg_rules"] = rules_parser(txt_neg)

# menu for company info entering
company_name = clean_str(st.text_input("Company name: ", "Google inc"))
website = st.text_input("website: ", "https://")
country = st.text_input("Country: ")

search_info = {
    'company_name' : company_name,  
    'Website' : website,  
    'country' : country
}

results_df = pd.DataFrame([search_info])

if "wiki_service" not in st.session_state: 
    st.session_state.wiki_service = WikidataService()

# searching companies based on entered data
if st.button("Submit", key = 'btn_submit_to_search_company'):
    try:
        final_company_list = st.session_state.wiki_service.search_companies(search_info['company_name'], '', '')
        data_for_table = [rare.to_dict() for rare in final_company_list]
        results_df = pd.DataFrame(data_for_table)
        st.session_state['founded_list_of_companies'] = data_for_table
    except Exception as e:
        st.write(e)

# choosing columns for scoring 
table_columns = COMPANY_LIST_FOR_ENRICHING[0].keys()
table_columns_name = st.multiselect(
    "Select column name of table for enriching: ",
    table_columns,
)
st.session_state['table_columns_name'] = table_columns_name


if not table_columns_name:
    st.error("Choose at least one column name for further work")

selected_rows = []
choosen_row = {}
choosen_rows = []
enriched_data = []
if st.session_state['company_list_for_enriching']:
    enriched_data = st.session_state['company_list_for_enriching']
    


# enriching list of new selected companies
if 'founded_list_of_companies' in st.session_state:
    df = pd.DataFrame(st.session_state['founded_list_of_companies'])
    s = st.dataframe(df, 
             selection_mode="multi-row", 
             on_select="rerun", 
             column_config = {'company_id' : None}
             )
    
    selected_rows = s['selection']['rows']
    
    if st.button("Submit", key = 'btn_submit_choosen_list_for_enriching') and selected_rows:
        
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
            .apply(lambda x: ScorerService.calculate_score(x, st.session_state.pos_rules, st.session_state.neg_rules))
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
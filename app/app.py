import streamlit as st
import pandas as pd
import json as js


st.title("0.5 Layer")
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
    st.session_state["pos_rules"] = POS_RULES.copy()
if "neg_rules" not in st.session_state:
    st.session_state["neg_rules"] = NEG_RULES.copy()
if "enrich" not in st.session_state:
    st.session_state["enrich"] = ENRICH.copy()
# information entered into input fields
if "search_info" not in st.session_state:
    st.session_state["search_info"] = SEARCH_INFO.copy()
# list of searching companies by name and another parameters    
if "founded_list_of_companies" not in st.session_state:
    st.session_state['founded_list_of_companies'] = ['']
# one selected current firm   
if "selected_companies_for_enriching" not in st.session_state:
    st.session_state['selected_companies_for_enriching'] = ''
# Finaly list of companies    
if "company_list_for_enriching" not in st.session_state:
    st.session_state['company_list_for_enriching'] = []



# returns a short list of companies that match the parameters 
#--------------------------------------------------------------------------------------------------------------------------------------------------------
def search_company(company_name :str, website: str, country: str): 
    company_name = company_name.strip()
    company_name = clean_str(company_name.lower())
    result_info = []

    if not company_name:
        raise ValueError("Company Name is empty")
    else: 
        query = f"""SELECT DISTINCT ?item ?itemLabel ?website ?countryLabel ?industryLabel WHERE {{
                ?item rdfs:label "{company_name}"@en ."""
        if website:
            query += f"""?item wdt:P856 "<{website}>" ."""    
        if country:
            query += f"""?item wdt:P17 "{country}"@en ."""    
        query += f"""?item wdt:P31 wd:Q4830453 .
                OPTIONAL {{ ?item wdt:P856 ?website. }}
                OPTIONAL {{ ?item wdt:P17 ?country. ?country rdfs:label ?countryLabel. FILTER(LANG(?countryLabel) = "en") }}
                OPTIONAL {{ ?item wdt:P452 ?industry. ?industry rdfs:label ?industryLabel. FILTER(LANG(?industryLabel) = "en") }}
                SERVICE wikibase:label {{bd:serviceParam wikibase:language "en". }}
                }}
                """
        url = "https://query.wikidata.org/sparql"
        headers = {'User-Agent': 'FirmLensBot/1.0 (blackmarka@gmail.com)', 'Accept': 'application/sparql-results+json'}

        try:
            response = requests.get(url, params = {'query' : query, 'format': 'json'}, headers = headers, timeout=10)
            data = response.json()
            results = data.get('results', {}).get('bindings', [])

            if results:
                for res in results:
                    one_company_result = {
                        'company_id' : res.get('item', {}).get('value', "N/A"),
                        'company_name' : res.get('itemLabel', {}).get('value', "N/A"),
                        'website' : res.get('website', {}).get('value', "N/A"),
                        'country' : res.get('countryLabel', {}).get('value', "N/A"),
                        'industry' : res.get('industryLabel', {}).get('value', "N/A")
                    }
                    result_info.append(one_company_result)
        except Exception as e:
            st.error(f"Error enriching {company_name}: {e}") 

    return result_info

# returns the enriched list of one company by id 
#--------------------------------------------------------------------------------------------------------------------------------------------------------
def enrich(company_id :str, website: str, country: str) -> dict [str, str]:
    company_id = company_id.strip()

    default_result = {
        'company_id' : company_id,
        'company_name' : country,
        'website' : website,
        'country' : 'N/A',
        'industry' : 'N/A'
    }

    if not company_id or company_id == 'N/A':
        raise ValueError("Company Name is empty")
    else: 
        company_id = company_id.split('/')[-1]
        query = f"""SELECT DISTINCT ?item ?itemLabel ?website ?countryLabel ?industryLabel WHERE {{
                BIND(wd:{company_id} AS ?item) ."""
        if website:
            query += f"""?item wdt:P856 "<{website}>" ."""    
        if country:
            query += f"""?item wdt:P17 "{country}"@en ."""    
        query += f"""?item wdt:P31 wd:Q4830453 .
                OPTIONAL {{ ?item wdt:P856 ?website. }}
                OPTIONAL {{ ?item wdt:P17 ?country. ?country rdfs:label ?countryLabel. FILTER(LANG(?countryLabel) = "en") }}
                OPTIONAL {{ ?item wdt:P452 ?industry. ?industry rdfs:label ?industryLabel. FILTER(LANG(?industryLabel) = "en") }}
                SERVICE wikibase:label {{bd:serviceParam wikibase:language "en". }}
                }}
                """
        url = "https://query.wikidata.org/sparql"
        headers = {'User-Agent': 'FirmLensBot/1.0 (blackmarka@gmail.com)', 'Accept': 'application/sparql-results+json'}

        try:
            response = requests.get(url, params = {'query' : query, 'format': 'json'}, headers = headers, timeout=10)
            data = response.json()
            enriched_result = data.get('results', {}).get('bindings', [])

            if enriched_result:
                res = enriched_result[0]
                return {
                    'company_id' : res.get('item', {}).get('value', "N/A"),
                    'company_name' : res.get('itemLabel', {}).get('value', "N/A"),
                    'website' : res.get('website', {}).get('value', "N/A"),
                    'country' : res.get('countryLabel', {}).get('value', "N/A"),
                    'industry' : res.get('industryLabel', {}).get('value', "N/A")
                }

        except Exception as e:
            st.error(f"Error enriching {company_name}: {e}") 
    return default_result


# total score and reasons for dict (one row of table)
#--------------------------------------------------------------------------------------------------------------------------------------------------------
def score(text: str) -> dict [str, str]:
    total_score = 0
    reasons = []
    if not text:
        raise ValueError("Column with this name is empty")
    else:
        pos_rules :dict [str, int] = st.session_state["pos_rules"]
        neg_rules :dict [str, int] = st.session_state["neg_rules"]
        
        for word, pts in pos_rules.items():
            if word in text.lower():
                total_score += pts
                reasons.append(f"+{pts}:{word}")

        for word, pts in neg_rules.items():
            if word in text.lower():
                total_score += pts
                reasons.append(f"{pts}:{word}")

    return str(total_score), "; ".join(reasons)


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


#if uploaded_file is not None:
    #st.success("File uploaded")
    #df = pd.read_csv(uploaded_file)

    #table_columns = df.columns.to_list()

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


# searching companies based on entered data
if st.button("Submit", key = 'btn_submit_to_search_company'):
    try:
        rare_data = search_company(search_info['company_name'], '', '')
        results_df = pd.DataFrame(rare_data)
        st.session_state['founded_list_of_companies'] = rare_data
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
    st.success(f"You choose:{selected_rows}")
    
    if st.button("Submit", key = 'btn_submit_choosen_list_for_enriching') and selected_rows:
        
        with st.spinner("Searching data in Wikidata..."):
            for row_number in selected_rows:
                row = df.iloc[row_number].to_dict()  
                st.warning(row)
                new_data = enrich(row['company_id'], '', '')
                enriched_data.append(new_data)
            st.session_state['company_list_for_enriching'] = enriched_data    

# generating final table (enriched with scoring)
if st.session_state['company_list_for_enriching']:
    try:

        final_df = pd.DataFrame(enriched_data)

        if not table_columns_name:
            table_columns_name = st.session_state['table_columns_name']
        st.write(table_columns_name)    
        final_df[['score_column', 'reason_column']] = final_df[table_columns_name].fillna("").astype(str).agg(" ".join , axis=1).apply(score).apply(pd.Series)

        if enriched_data:     
            
            st.subheader("Result of deep analysis:")
            st.table(final_df) 

    except Exception as e:
        st.write(e)


#csv = out.to_csv(index = False, sep=';').encode("utf-8")

#st.download_button(
#    label = "Download CSV",
#    data = csv,
#    file_name = "data.csv",
#)

#else: 
#    st.info("No file yet")


